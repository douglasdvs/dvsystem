from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.decorators import login_required
from .models import Cliente, TipoCliente, Endereco, Tag, Segmento
from .forms import ClienteForm, TipoClienteForm, EnderecoForm, TagForm
from django import forms
from .services import CepService, ClienteExportService
import pandas as pd
import json
import requests
import re
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator
import logging
from django.views.decorators.http import require_GET

class SegmentoForm(forms.ModelForm):
    class Meta:
        model = Segmento
        fields = ['nome', 'descricao']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

@login_required
def novo_segmento(request):
    if request.method == 'POST':
        form = SegmentoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Segmento cadastrado com sucesso!')
            return redirect('clientes:listar')
    else:
        form = SegmentoForm()
    return render(request, 'clientes/segmento_form.html', {'form': form, 'titulo': 'Novo Segmento'})

logger = logging.getLogger(__name__)

def listar_clientes(request):
    """
    Lista clientes com paginação e busca avançada.
    """
    busca = request.GET.get('busca', '')
    tipo_cliente = request.GET.get('tipo_cliente', '')
    status = request.GET.get('status', 'todos')
    uf = request.GET.get('uf', '')
    
    clientes = Cliente.objects.all()
    
    # Filtro por busca
    if busca:
        clientes = clientes.filter(
            Q(nome__icontains=busca) | 
            Q(cpf_cnpj__icontains=busca) |
            Q(email__icontains=busca) | 
            Q(telefone__icontains=busca)
        )
    
    # Filtro por tipo de cliente
    if tipo_cliente and tipo_cliente != 'todos':
        clientes = clientes.filter(tipo_cliente__id=tipo_cliente)
    
    # Filtro por status
    if status == 'ativos':
        clientes = clientes.filter(ativo=True)
    elif status == 'inativos':
        clientes = clientes.filter(ativo=False)
        
    # Filtro por UF
    if uf:
        clientes = clientes.filter(uf=uf)
    
    # Ordenação
    sort = request.GET.get('sort', 'nome')
    clientes = clientes.order_by(sort)
    
    # Estatísticas
    total_clientes = clientes.count()
    clientes_por_uf = dict(clientes.values('uf').annotate(
        count=Count('uf')).values_list('uf', 'count'))
    clientes_por_tipo = dict(clientes.values('tipo_cliente__nome').annotate(
        count=Count('tipo_cliente')).values_list('tipo_cliente__nome', 'count'))
    
    # Paginação
    itens_por_pagina = int(request.GET.get('itens_por_pagina', 10))
    paginator = Paginator(clientes, itens_por_pagina)
    page_number = request.GET.get('page')
    clientes_paginados = paginator.get_page(page_number)
    
    # Listar tipos de cliente para o filtro
    tipos_cliente = TipoCliente.objects.all()
    
    return render(request, 'clientes/listar.html', {
        'clientes': clientes_paginados,
        'busca': busca,
        'tipo_cliente': tipo_cliente,
        'tipos_cliente': tipos_cliente,
        'status': status,
        'uf_selected': uf,
        'sort': sort,
        'total_clientes': total_clientes,
        'clientes_por_uf': clientes_por_uf,
        'clientes_por_tipo': clientes_por_tipo,
        'itens_por_pagina': itens_por_pagina
    })

@login_required
def novo_cliente(request):
    if request.method == 'POST':
        form = ClienteForm(request.POST)
        if form.is_valid():
            cliente = form.save(commit=False)
            cliente.criado_por = request.user
            cliente.save()
            messages.success(request, 'Cliente criado com sucesso!')
            
            # Verificar se o usuário quer continuar cadastrando
            if 'salvar_continuar' in request.POST:
                return redirect('clientes:novo')
            return redirect('clientes:listar')
    else:
        form = ClienteForm()
    
    return render(request, 'clientes/form.html', {
        'form': form,
        'titulo': 'Novo Cliente'
    })

@login_required
def excluir_cliente(request, pk):
    """
    Exclui um cliente após confirmação.
    """
    cliente = get_object_or_404(Cliente, pk=pk)
    if request.method == 'POST':
        # Inativar em vez de excluir
        if 'inativar' in request.POST:
            cliente.ativo = False
            cliente.save()
            messages.success(request, 'Cliente inativado com sucesso!')
        # Exclusão definitiva
        else:
            cliente.delete()
            messages.success(request, 'Cliente excluído com sucesso!')
        return redirect('clientes:listar')
    
    return render(request, 'clientes/confirmar_exclusao.html', {
        'cliente': cliente
    })
    
@login_required
def editar_cliente(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    if request.method == 'POST':
        form = ClienteForm(request.POST, instance=cliente)
        if form.is_valid():
            cliente = form.save(commit=False)
            # não alteramos criado_por aqui
            cliente.save()
            messages.success(request, 'Cliente atualizado com sucesso!')
            return redirect('clientes:listar')
    else:
        form = ClienteForm(instance=cliente)
    
    return render(request, 'clientes/form.html', {
        'form': form,
        'cliente': cliente,
        'titulo': f'Editar Cliente: {cliente.nome}'
    })

def buscar_cep(request):
    """View para busca de CEP via AJAX."""
    cep = request.GET.get('cep', '')
    if not cep:
        return JsonResponse({'erro': 'CEP não informado'}, status=400)
    
    resultado = CepService.buscar_cep(cep)
    if resultado:
        return JsonResponse(resultado)
    return JsonResponse({'erro': 'CEP não encontrado'}, status=404)

def exportar_clientes(request):
    """View para exportação de clientes para Excel."""
    try:
        # Obter filtros
        busca = request.GET.get('busca', '')
        tipo = request.GET.get('tipo', '')
        status = request.GET.get('status', '')
        
        # Filtrar clientes
        queryset = Cliente.objects.all()
        
        if busca:
            queryset = queryset.filter(
                Q(nome__icontains=busca) |
                Q(cpf_cnpj__icontains=busca) |
                Q(email__icontains=busca)
            )
        
        if tipo:
            queryset = queryset.filter(tipo_cliente_id=tipo)
        
        if status:
            queryset = queryset.filter(ativo=status == 'ativo')
        
        # Exportar para Excel
        wb = ClienteExportService.exportar_excel(queryset)
        
        # Criar resposta
        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename={ClienteExportService.get_filename()}'
        
        # Salvar arquivo
        wb.save(response)
        
        logger.info(f'Exportação de {queryset.count()} clientes realizada com sucesso')
        return response
        
    except Exception as e:
        logger.error(f'Erro ao exportar clientes: {str(e)}')
        messages.error(request, f'Erro ao exportar clientes: {str(e)}')
        return redirect('clientes:listar')

@login_required
def tipos_cliente(request):
    """Gerenciar tipos de cliente"""
    tipos = TipoCliente.objects.all().order_by('nome')
    
    if request.method == 'POST':
        form = TipoClienteForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Tipo de cliente criado com sucesso!')
            return redirect('clientes:tipos_cliente')
    else:
        form = TipoClienteForm()
        
    return render(request, 'clientes/tipos_cliente.html', {
        'tipos': tipos,
        'form': form
    })

@login_required
def editar_tipo_cliente(request, pk):
    """Editar tipo de cliente"""
    tipo = get_object_or_404(TipoCliente, pk=pk)
    
    if request.method == 'POST':
        form = TipoClienteForm(request.POST, instance=tipo)
        if form.is_valid():
            form.save()
            messages.success(request, 'Tipo de cliente atualizado com sucesso!')
            return redirect('clientes:tipos_cliente')
    else:
        form = TipoClienteForm(instance=tipo)
        
    return render(request, 'clientes/editar_tipo_cliente.html', {
        'form': form,
        'tipo': tipo
    })

@login_required
def excluir_tipo_cliente(request, pk):
    """Excluir tipo de cliente"""
    tipo = get_object_or_404(TipoCliente, pk=pk)
    
    # Verificar se há clientes usando este tipo
    count = Cliente.objects.filter(tipo_cliente=tipo).count()
    if count > 0:
        messages.error(request, f'Este tipo de cliente não pode ser excluído pois está em uso por {count} cliente(s).')
        return redirect('clientes:tipos_cliente')
    
    if request.method == 'POST':
        tipo.delete()
        messages.success(request, 'Tipo de cliente excluído com sucesso!')
        return redirect('clientes:tipos_cliente')
    
    return render(request, 'clientes/confirmar_exclusao_tipo.html', {
        'tipo': tipo
    })

class ClienteListView(LoginRequiredMixin, ListView):
    model = Cliente
    template_name = 'clientes/listar.html'
    context_object_name = 'clientes'
    paginate_by = 10
    
    def get_queryset(self):
        queryset = super().get_queryset()
        busca = self.request.GET.get('busca', '')
        tipo = self.request.GET.get('tipo', '')
        status = self.request.GET.get('status', '')
        
        if busca:
            queryset = queryset.filter(
                Q(nome__icontains=busca) |
                Q(cpf_cnpj__icontains=busca) |
                Q(email__icontains=busca)
            )
        
        if tipo:
            queryset = queryset.filter(tipo_cliente_id=tipo)
        
        if status:
            queryset = queryset.filter(ativo=status == 'ativo')
        
        return queryset.select_related('tipo_cliente')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tipos_cliente'] = TipoCliente.objects.all()
        context['total_clientes'] = self.get_queryset().count()
        context['clientes_ativos'] = self.get_queryset().filter(ativo=True).count()
        return context

class ClienteCreateView(LoginRequiredMixin, CreateView):
    model = Cliente
    form_class = ClienteForm
    template_name = 'clientes/form.html'
    
    def get_success_url(self):
        # Se houver um parâmetro next na URL, redireciona para ele
        next_url = self.request.GET.get('next')
        if next_url:
            # Se for um pedido, adiciona o ID do cliente como parâmetro
            if 'pedidos:novo' in next_url:
                return f"{next_url}?cliente_id={self.object.id}"
            return next_url
        return reverse_lazy('clientes:listar')
    
    def form_valid(self, form):
        try:
            response = super().form_valid(form)
            messages.success(self.request, 'Cliente criado com sucesso!')
            logger.info(f'Cliente {form.instance.nome} criado com sucesso')
            return response
        except Exception as e:
            messages.error(self.request, f'Erro ao criar cliente: {str(e)}')
            logger.error(f'Erro ao criar cliente: {str(e)}')
            return self.form_invalid(form)

class ClienteUpdateView(LoginRequiredMixin, UpdateView):
    model = Cliente
    form_class = ClienteForm
    template_name = 'clientes/form.html'
    success_url = reverse_lazy('clientes:listar')
    
    def form_valid(self, form):
        try:
            response = super().form_valid(form)
            messages.success(self.request, 'Cliente atualizado com sucesso!')
            logger.info(f'Cliente {form.instance.nome} atualizado com sucesso')
            return response
        except Exception as e:
            messages.error(self.request, f'Erro ao atualizar cliente: {str(e)}')
            logger.error(f'Erro ao atualizar cliente: {str(e)}')
            return self.form_invalid(form)

class ClienteDeleteView(LoginRequiredMixin, DeleteView):
    model = Cliente
    success_url = reverse_lazy('clientes:listar')
    
    def delete(self, request, *args, **kwargs):
        try:
            cliente = self.get_object()
            nome = cliente.nome
            response = super().delete(request, *args, **kwargs)
            messages.success(request, f'Cliente {nome} excluído com sucesso!')
            logger.info(f'Cliente {nome} excluído com sucesso')
            return response
        except Exception as e:
            messages.error(request, f'Erro ao excluir cliente: {str(e)}')
            logger.error(f'Erro ao excluir cliente: {str(e)}')
            return redirect(self.success_url)

class ClienteDetailView(LoginRequiredMixin, DetailView):
    model = Cliente
    template_name = 'clientes/detalhe.html'
    context_object_name = 'cliente'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['enderecos'] = self.object.enderecos.all()
        # Adicionar tags disponíveis (excluindo as que o cliente já tem)
        context['tags_disponiveis'] = Tag.objects.exclude(
            id__in=self.object.tags.values_list('id', flat=True)
        )
        # TODO: Adicionar histórico de compras quando implementar módulo de vendas
        return context

# @method_decorator(cache_page(60 * 15), name='dispatch')  # Cache por 15 minutos
class TipoClienteListView(LoginRequiredMixin, ListView):
    model = TipoCliente
    template_name = 'clientes/tipos_cliente.html'
    context_object_name = 'tipos'
    ordering = ['nome']
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_tipos'] = self.get_queryset().count()
        return context

class TipoClienteCreateView(LoginRequiredMixin, CreateView):
    model = TipoCliente
    form_class = TipoClienteForm
    template_name = 'clientes/tipo_cliente_form.html'
    success_url = reverse_lazy('clientes:tipos_cliente')
    
    def form_valid(self, form):
        try:
            response = super().form_valid(form)
            messages.success(self.request, 'Tipo de cliente criado com sucesso!')
            logger.info(f'Tipo de cliente {form.instance.nome} criado com sucesso')
            return response
        except Exception as e:
            messages.error(self.request, f'Erro ao criar tipo de cliente: {str(e)}')
            logger.error(f'Erro ao criar tipo de cliente: {str(e)}')
            return self.form_invalid(form)

class TipoClienteUpdateView(LoginRequiredMixin, UpdateView):
    model = TipoCliente
    form_class = TipoClienteForm
    template_name = 'clientes/tipo_cliente_form.html'
    success_url = reverse_lazy('clientes:tipos_cliente')
    
    def form_valid(self, form):
        try:
            response = super().form_valid(form)
            messages.success(self.request, 'Tipo de cliente atualizado com sucesso!')
            logger.info(f'Tipo de cliente {form.instance.nome} atualizado com sucesso')
            return response
        except Exception as e:
            messages.error(self.request, f'Erro ao atualizar tipo de cliente: {str(e)}')
            logger.error(f'Erro ao atualizar tipo de cliente: {str(e)}')
            return self.form_invalid(form)

class TipoClienteDeleteView(LoginRequiredMixin, DeleteView):
    model = TipoCliente
    success_url = reverse_lazy('clientes:tipos_cliente')
    
    def delete(self, request, *args, **kwargs):
        try:
            tipo = self.get_object()
            if tipo.clientes.exists():
                messages.error(request, 'Não é possível excluir um tipo de cliente que possui clientes vinculados!')
                return redirect(self.success_url)
            
            nome = tipo.nome
            response = super().delete(request, *args, **kwargs)
            messages.success(request, f'Tipo de cliente {nome} excluído com sucesso!')
            logger.info(f'Tipo de cliente {nome} excluído com sucesso')
            return response
        except Exception as e:
            messages.error(request, f'Erro ao excluir tipo de cliente: {str(e)}')
            logger.error(f'Erro ao excluir tipo de cliente: {str(e)}')
            return redirect(self.success_url)

class TagListView(LoginRequiredMixin, ListView):
    model = Tag
    template_name = 'clientes/tags.html'
    context_object_name = 'tags'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_tags'] = self.get_queryset().count()
        return context

class TagCreateView(LoginRequiredMixin, CreateView):
    model = Tag
    form_class = TagForm
    template_name = 'clientes/tag_form.html'
    success_url = reverse_lazy('clientes:tags')
    
    def form_valid(self, form):
        try:
            response = super().form_valid(form)
            messages.success(self.request, 'Tag criada com sucesso!')
            logger.info(f'Tag {form.instance.nome} criada com sucesso')
            return response
        except Exception as e:
            messages.error(self.request, f'Erro ao criar tag: {str(e)}')
            logger.error(f'Erro ao criar tag: {str(e)}')
            return self.form_invalid(form)

class TagUpdateView(LoginRequiredMixin, UpdateView):
    model = Tag
    form_class = TagForm
    template_name = 'clientes/tag_form.html'
    success_url = reverse_lazy('clientes:tags')
    
    def form_valid(self, form):
        try:
            response = super().form_valid(form)
            messages.success(self.request, 'Tag atualizada com sucesso!')
            logger.info(f'Tag {form.instance.nome} atualizada com sucesso')
            return response
        except Exception as e:
            messages.error(self.request, f'Erro ao atualizar tag: {str(e)}')
            logger.error(f'Erro ao atualizar tag: {str(e)}')
            return self.form_invalid(form)

class TagDeleteView(LoginRequiredMixin, DeleteView):
    model = Tag
    success_url = reverse_lazy('clientes:tags')
    
    def delete(self, request, *args, **kwargs):
        try:
            tag = self.get_object()
            if tag.clientes.exists():
                messages.error(request, 'Não é possível excluir uma tag que possui clientes vinculados!')
                return redirect(self.success_url)
            
            nome = tag.nome
            response = super().delete(request, *args, **kwargs)
            messages.success(request, f'Tag {nome} excluída com sucesso!')
            logger.info(f'Tag {nome} excluída com sucesso')
            return response
        except Exception as e:
            messages.error(request, f'Erro ao excluir tag: {str(e)}')
            logger.error(f'Erro ao excluir tag: {str(e)}')
            return redirect(self.success_url)

def adicionar_tag_cliente(request, cliente_id):
    """View para adicionar uma tag a um cliente via AJAX."""
    if request.method == 'POST':
        try:
            cliente = Cliente.objects.get(id=cliente_id)
            tag_id = request.POST.get('tag_id')
            tag = Tag.objects.get(id=tag_id)
            
            cliente.adicionar_tag(tag)
            messages.success(request, f'Tag {tag.nome} adicionada com sucesso!')
            return JsonResponse({'status': 'success'})
        except (Cliente.DoesNotExist, Tag.DoesNotExist):
            return JsonResponse({'status': 'error', 'message': 'Cliente ou tag não encontrado'}, status=404)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    return JsonResponse({'status': 'error', 'message': 'Método não permitido'}, status=405)

def remover_tag_cliente(request, cliente_id):
    """View para remover uma tag de um cliente via AJAX."""
    if request.method == 'POST':
        try:
            cliente = Cliente.objects.get(id=cliente_id)
            tag_id = request.POST.get('tag_id')
            tag = Tag.objects.get(id=tag_id)
            
            cliente.remover_tag(tag)
            messages.success(request, f'Tag {tag.nome} removida com sucesso!')
            return JsonResponse({'status': 'success'})
        except (Cliente.DoesNotExist, Tag.DoesNotExist):
            return JsonResponse({'status': 'error', 'message': 'Cliente ou tag não encontrado'}, status=404)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    return JsonResponse({'status': 'error', 'message': 'Método não permitido'}, status=405)

@login_required
def adicionar_endereco(request, cliente_id):
    cliente = get_object_or_404(Cliente, pk=cliente_id)
    if request.method == 'POST':
        form = EnderecoForm(request.POST)
        if form.is_valid():
            endereco = form.save(commit=False)
            endereco.cliente = cliente
            endereco.save()
            messages.success(request, "Endereço adicionado com sucesso.")
            return redirect('clientes:detalhe', pk=cliente.pk)
    else:
         form = EnderecoForm()
    return render(request, 'clientes/endereco_form.html', {'form': form, 'cliente': cliente, 'titulo': 'Adicionar Endereço'})

@login_required
def editar_endereco(request, pk):
    endereco = get_object_or_404(Endereco, pk=pk)
    if request.method == 'POST':
         form = EnderecoForm(request.POST, instance=endereco)
         if form.is_valid():
             form.save()
             messages.success(request, "Endereço atualizado com sucesso.")
             return redirect('clientes:detalhe', pk=endereco.cliente.pk)
    else:
         form = EnderecoForm(instance=endereco)
    return render(request, 'clientes/endereco_form.html', {'form': form, 'endereco': endereco, 'titulo': 'Editar Endereço'})

@login_required
def excluir_endereco(request, pk):
    endereco = get_object_or_404(Endereco, pk=pk)
    cliente_pk = endereco.cliente.pk
    endereco.delete()
    messages.success(request, "Endereço excluído com sucesso.")
    return redirect('clientes:detalhe', pk=cliente_pk)

@require_GET
@login_required
def buscar_clientes_ajax(request):
    """View para busca AJAX de clientes."""
    termo = request.GET.get('term', '')
    if len(termo) < 2:
        return JsonResponse({'results': []})
    
    clientes = Cliente.objects.filter(
        Q(nome__icontains=termo) |
        Q(cpf_cnpj__icontains=termo) |
        Q(email__icontains=termo) |
        Q(telefone__icontains=termo) |
        Q(enderecos__logradouro__icontains=termo) |
        Q(enderecos__cidade__icontains=termo)
    ).filter(ativo=True).distinct()[:10]
    
    results = [{
        'id': cliente.id,
        'text': f"{cliente.nome} ({cliente.cpf_cnpj})",
        'email': cliente.email,
        'telefone': cliente.telefone,
        'tipo': cliente.tipo_cliente.nome if cliente.tipo_cliente else '',
        'endereco': cliente.enderecos.first().logradouro if cliente.enderecos.exists() else ''
    } for cliente in clientes]
    
    return JsonResponse({'results': results})

from django.http import JsonResponse
from django.db.models import Q

def api_buscar_cliente(request):
    term = request.GET.get('term', '')
    if len(term) < 2:
        return JsonResponse({'results': []})

    clientes = Cliente.objects.filter(
        Q(nome__icontains=term) |
        Q(cpf_cnpj__icontains=term) |
        Q(email__icontains=term)
    ).values('id', 'nome', 'email', 'telefone')[:10]

    results = [
        {
            'id': cliente['id'],
            'text': cliente['nome'],
            'email': cliente['email'],
            'telefone': cliente['telefone']
        }
        for cliente in clientes
    ]

    return JsonResponse({'results': results})