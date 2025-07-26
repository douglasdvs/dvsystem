import json
import logging
import re

import pandas as pd
import requests
from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.forms import inlineformset_factory
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.decorators.http import require_GET
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from .forms import ClienteForm, EnderecoForm, TagForm, TipoClienteForm
from .models import Cliente, Endereco, Segmento, Tag, TipoCliente
from .services import CepService, ClienteExportService

EnderecoFormSet = inlineformset_factory(
    Cliente, Endereco, form=EnderecoForm, extra=1, can_delete=False, max_num=1, validate_max=True
)


class SegmentoForm(forms.ModelForm):
    class Meta:
        model = Segmento
        fields = ["nome", "descricao"]
        widgets = {
            "nome": forms.TextInput(attrs={"class": "form-control"}),
            "descricao": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }


@login_required
def novo_segmento(request):
    from .models import Segmento

    if request.method == "POST":
        form = SegmentoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Segmento cadastrado com sucesso!")
            return redirect("clientes:listar")
    else:
        form = SegmentoForm()
    # pyrefly: ignore  # missing-attribute
    segmentos = Segmento.objects.all().order_by("nome")
    return render(
        request, "clientes/segmento_form.html", {"form": form, "titulo": "Novo Segmento", "segmentos": segmentos}
    )


logger = logging.getLogger(__name__)


def listar_clientes(request):
    """
    Lista clientes com paginação e busca avançada.
    """
    busca = request.GET.get("busca", "")
    tipo_cliente = request.GET.get("tipo_cliente", "")
    status = request.GET.get("status", "todos")
    uf = request.GET.get("uf", "")
    segmento_id = request.GET.get("segmento", "")

    # Carrega todos os campos para permitir filtragem correta
    # pyrefly: ignore  # missing-attribute
    clientes = Cliente.objects.all()

    # Filtro por busca
    if busca:
        clientes = clientes.filter(
            # pyrefly: ignore  # missing-attribute
            Q(nome__icontains=busca)
            | Q(cpf_cnpj__icontains=busca)
            | Q(email__icontains=busca)
            | Q(telefone__icontains=busca)
        )

    # Filtro por tipo de cliente
    if tipo_cliente and tipo_cliente != "todos":
        try:
            tipo_cliente_int = int(tipo_cliente)
            clientes = clientes.filter(tipo_cliente_id=tipo_cliente_int)
        except (ValueError, TypeError):
            pass

    # Filtro por status
    if status == "ativos":
        clientes = clientes.filter(ativo=True)
    elif status == "inativos":
        clientes = clientes.filter(ativo=False)

    # Filtro por UF
    if uf:
        clientes = clientes.filter(enderecos__uf=uf).distinct()

    # Filtro por segmento
    if segmento_id:
        try:
            segmento_id_int = int(segmento_id)
            clientes = clientes.filter(segmento_id=segmento_id_int)
        except (ValueError, TypeError):
            pass

    sort = request.GET.get("sort", "nome")
    clientes = clientes.order_by("nome")

    # Paginação
    itens_por_pagina = 15
    paginator = Paginator(clientes, itens_por_pagina)
    page_number = request.GET.get("page")
    clientes_paginados = paginator.get_page(page_number)

    # Estatísticas separadas para não impactar a listagem
    # pyrefly: ignore  # missing-attribute
    total_clientes = Cliente.objects.count()
    # pyrefly: ignore  # missing-attribute
    clientes_por_uf = dict(
        Endereco.objects.values("uf").annotate(count=Count("cliente", distinct=True)).values_list("uf", "count")
    )

    # pyrefly: ignore  # missing-attribute
    clientes_por_tipo = dict(
        Cliente.objects.filter(tipo_cliente__isnull=False)
        .values("tipo_cliente__nome")
        .annotate(count=Count("id"))
        .values_list("tipo_cliente__nome", "count")
    )

    # pyrefly: ignore  # missing-attribute
    tipos_cliente = TipoCliente.objects.all()
    # pyrefly: ignore  # missing-attribute
    segmentos = Segmento.objects.all().order_by("nome")

    return render(
        request,
        "clientes/listar.html",
        {
            "clientes": clientes_paginados,
            "busca": busca,
            "tipo_cliente": tipo_cliente,
            "tipos_cliente": tipos_cliente,
            "status": status,
            "uf_selected": uf,
            "sort": sort,
            "total_clientes": total_clientes,
            "clientes_por_uf": clientes_por_uf,
            "clientes_por_tipo": clientes_por_tipo,
            "itens_por_pagina": itens_por_pagina,
            "segmentos": segmentos,
            "segmento_id": segmento_id,
        },
    )


@login_required
def novo_cliente(request):
    EnderecoFormSet = inlineformset_factory(
        Cliente, Endereco, form=EnderecoForm, extra=1, can_delete=False, max_num=1, validate_max=True
    )

    if request.method == "POST":
        form = ClienteForm(request.POST)
        endereco_formset = EnderecoFormSet(request.POST)
        if form.is_valid() and endereco_formset.is_valid():
            cliente = form.save(commit=False)
            cliente.criado_por = request.user
            cliente.save()
            endereco_formset.instance = cliente
            endereco_formset.save()
            messages.success(request, "Cliente cadastrado com sucesso!")
            return redirect("clientes:listar")
    else:
        form = ClienteForm()
        endereco_formset = EnderecoFormSet()

    return render(
        request,
        "clientes/cliente_form.html",
        {"form": form, "endereco_formset": endereco_formset, "titulo": "Novo Cliente"},
    )


@login_required
def excluir_cliente(request, pk):
    """
    Exclui um cliente após confirmação.
    """
    cliente = get_object_or_404(Cliente, pk=pk)
    if request.method == "POST":
        # Inativar em vez de excluir
        if "inativar" in request.POST:
            cliente.ativo = False
            cliente.save()
            messages.success(request, "Cliente inativado com sucesso!")
        # Exclusão definitiva
        else:
            cliente.delete()
            messages.success(request, "Cliente excluído com sucesso!")
        return redirect("clientes:listar")

    return render(request, "clientes/confirmar_exclusao.html", {"cliente": cliente})


@login_required
def editar_cliente(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    EnderecoFormSet = inlineformset_factory(
        Cliente, Endereco, form=EnderecoForm, extra=1, can_delete=False, max_num=1, validate_max=True
    )

    if request.method == "POST":
        form = ClienteForm(request.POST, instance=cliente)
        endereco_formset = EnderecoFormSet(request.POST, instance=cliente)
        if form.is_valid() and endereco_formset.is_valid():
            form.save()
            endereco_formset.save()
            messages.success(request, "Cliente atualizado com sucesso!")
            # Redireciona para a página de detalhes do cliente
            return redirect("clientes:detalhe", pk=cliente.pk)
    else:
        form = ClienteForm(instance=cliente)
        endereco_formset = EnderecoFormSet(instance=cliente)

    return render(
        request,
        "clientes/cliente_form.html",
        {
            "form": form,
            "endereco_formset": endereco_formset,
            "cliente": cliente,
            "titulo": f"Editar Cliente: {cliente.nome}",
        },
    )


def buscar_cep(request):
    """View para busca de CEP via AJAX."""
    cep = request.GET.get("cep", "")
    if not cep:
        return JsonResponse({"erro": "CEP não informado"}, status=400)

    # pyrefly: ignore  # missing-attribute
    resultado = CepService.buscar_cep(cep)
    if resultado:
        return JsonResponse(resultado)
    return JsonResponse({"erro": "CEP não encontrado"}, status=404)


def exportar_clientes(request):
    """View para exportação de clientes para Excel."""
    try:
        # Obter filtros
        busca = request.GET.get("busca", "")
        tipo = request.GET.get("tipo", "")
        status = request.GET.get("status", "")

        # Filtrar clientes
        # pyrefly: ignore  # missing-attribute
        queryset = Cliente.objects.all()

        if busca:
            queryset = queryset.filter(
                # pyrefly: ignore  # missing-attribute
                Q(nome__icontains=busca)
                | Q(cpf_cnpj__icontains=busca)
                | Q(email__icontains=busca)
            )

        if tipo:
            queryset = queryset.filter(tipo_cliente_id=tipo)

        if status:
            queryset = queryset.filter(ativo=status == "ativo")

        # Exportar para Excel
        wb = ClienteExportService.exportar_excel(queryset)

        # Criar resposta
        response = HttpResponse(content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        response["Content-Disposition"] = f"attachment; filename={ClienteExportService.get_filename()}"

        # Salvar arquivo
        wb.save(response)

        logger.info(f"Exportação de {queryset.count()} clientes realizada com sucesso")
        return response

    except Exception as e:
        logger.error(f"Erro ao exportar clientes: {str(e)}")
        messages.error(request, f"Erro ao exportar clientes: {str(e)}")
        return redirect("clientes:listar")


@login_required
def tipos_cliente(request):
    """Gerenciar tipos de cliente"""
    # pyrefly: ignore  # missing-attribute
    tipos = TipoCliente.objects.all().order_by("nome")

    if request.method == "POST":
        form = TipoClienteForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Tipo de cliente criado com sucesso!")
            return redirect("clientes:tipos_cliente")
    else:
        form = TipoClienteForm()

    return render(request, "clientes/tipos_cliente.html", {"tipos": tipos, "form": form})


@login_required
def editar_tipo_cliente(request, pk):
    """Editar tipo de cliente"""
    tipo = get_object_or_404(TipoCliente, pk=pk)

    if request.method == "POST":
        form = TipoClienteForm(request.POST, instance=tipo)
        if form.is_valid():
            form.save()
            messages.success(request, "Tipo de cliente atualizado com sucesso!")
            return redirect("clientes:tipos_cliente")
    else:
        form = TipoClienteForm(instance=tipo)

    return render(request, "clientes/editar_tipo_cliente.html", {"form": form, "tipo": tipo})


@login_required
def excluir_tipo_cliente(request, pk):
    """Excluir tipo de cliente"""
    tipo = get_object_or_404(TipoCliente, pk=pk)

    # Verificar se há clientes usando este tipo
    # pyrefly: ignore  # missing-attribute
    count = Cliente.objects.filter(tipo_cliente=tipo).count()
    if count > 0:
        messages.error(request, f"Este tipo de cliente não pode ser excluído pois está em uso por {count} cliente(s).")
        return redirect("clientes:tipos_cliente")

    if request.method == "POST":
        tipo.delete()
        messages.success(request, "Tipo de cliente excluído com sucesso!")
        return redirect("clientes:tipos_cliente")

    return render(request, "clientes/confirmar_exclusao_tipo.html", {"tipo": tipo})


class ClienteListView(LoginRequiredMixin, ListView):
    # pyrefly: ignore  # bad-override
    model = Cliente
    # pyrefly: ignore  # bad-override
    template_name = "clientes/listar.html"
    # pyrefly: ignore  # bad-override
    context_object_name = "clientes"
    # pyrefly: ignore  # bad-override
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset()
        busca = self.request.GET.get("busca", "")
        tipo = self.request.GET.get("tipo", "")
        status = self.request.GET.get("status", "")

        if busca:
            queryset = queryset.filter(
                # pyrefly: ignore  # missing-attribute
                Q(nome__icontains=busca)
                | Q(cpf_cnpj__icontains=busca)
                | Q(email__icontains=busca)
            )

        if tipo:
            queryset = queryset.filter(tipo_cliente_id=tipo)

        if status:
            queryset = queryset.filter(ativo=status == "ativo")

        return queryset.select_related("tipo_cliente")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # pyrefly: ignore  # missing-attribute
        context["tipos_cliente"] = TipoCliente.objects.all()
        context["total_clientes"] = self.get_queryset().count()
        context["clientes_ativos"] = self.get_queryset().filter(ativo=True).count()
        return context


class ClienteCreateView(LoginRequiredMixin, CreateView):
    # pyrefly: ignore  # bad-override
    model = Cliente
    # pyrefly: ignore  # bad-override
    form_class = ClienteForm
    # pyrefly: ignore  # bad-override
    template_name = "clientes/form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context["endereco_formset"] = EnderecoFormSet(self.request.POST)
        else:
            context["endereco_formset"] = EnderecoFormSet()
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        endereco_formset = context["endereco_formset"]
        if endereco_formset.is_valid():
            self.object = form.save()
            endereco_formset.instance = self.object
            endereco_formset.save()
            messages.success(self.request, "Cliente criado com sucesso!")
            return redirect(self.get_success_url())
        else:
            return self.render_to_response(self.get_context_data(form=form))

    def get_success_url(self):
        # Se houver um parâmetro next na URL, redireciona para ele
        next_url = self.request.GET.get("next")
        if next_url:
            # Se for um pedido, adiciona o ID do cliente como parâmetro
            if "pedidos:novo" in next_url:
                return f"{next_url}?cliente_id={self.object.id}"
            return next_url
        return reverse_lazy("clientes:listar")


class ClienteUpdateView(LoginRequiredMixin, UpdateView):
    # pyrefly: ignore  # bad-override
    model = Cliente
    # pyrefly: ignore  # bad-override
    form_class = ClienteForm
    # pyrefly: ignore  # bad-override
    template_name = "clientes/form.html"
    # pyrefly: ignore  # bad-override
    success_url = reverse_lazy("clientes:listar")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context["endereco_formset"] = EnderecoFormSet(self.request.POST, instance=self.object)
        else:
            context["endereco_formset"] = EnderecoFormSet(instance=self.object)
        return context

    # pyrefly: ignore  # bad-override
    def form_valid(self, form):
        context = self.get_context_data()
        endereco_formset = context["endereco_formset"]
        if endereco_formset.is_valid():
            self.object = form.save()
            endereco_formset.instance = self.object
            endereco_formset.save()
            messages.success(self.request, "Cliente atualizado com sucesso!")
            return redirect(self.success_url)
        else:
            return self.render_to_response(self.get_context_data(form=form))


class ClienteDeleteView(LoginRequiredMixin, DeleteView):
    # pyrefly: ignore  # bad-override
    model = Cliente
    # pyrefly: ignore  # bad-override
    success_url = reverse_lazy("clientes:listar")

    def delete(self, request, *args, **kwargs):
        try:
            cliente = self.get_object()
            nome = cliente.nome
            response = super().delete(request, *args, **kwargs)
            messages.success(request, f"Cliente {nome} excluído com sucesso!")
            logger.info(f"Cliente {nome} excluído com sucesso")
            return response
        except Exception as e:
            messages.error(request, f"Erro ao excluir cliente: {str(e)}")
            logger.error(f"Erro ao excluir cliente: {str(e)}")
            return redirect(self.success_url)


class ClienteDetailView(LoginRequiredMixin, DetailView):
    # pyrefly: ignore  # bad-override
    model = Cliente
    # pyrefly: ignore  # bad-override
    template_name = "clientes/detalhe.html"
    # pyrefly: ignore  # bad-override
    context_object_name = "cliente"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["enderecos"] = self.object.enderecos.all()
        # Adicionar tags disponíveis (excluindo as que o cliente já tem)
        # pyrefly: ignore  # missing-attribute
        context["tags_disponiveis"] = Tag.objects.exclude(id__in=self.object.tags.values_list("id", flat=True))
        # TODO: Adicionar histórico de compras quando implementar módulo de vendas
        return context


# @method_decorator(cache_page(60 * 15), name='dispatch')  # Cache por 15 minutos
class TipoClienteListView(LoginRequiredMixin, ListView):
    # pyrefly: ignore  # bad-override
    model = TipoCliente
    # pyrefly: ignore  # bad-override
    template_name = "clientes/tipos_cliente.html"
    # pyrefly: ignore  # bad-override
    context_object_name = "tipos"
    # pyrefly: ignore  # bad-override
    ordering = ["nome"]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["total_tipos"] = self.get_queryset().count()
        return context


class TipoClienteCreateView(LoginRequiredMixin, CreateView):
    # pyrefly: ignore  # bad-override
    model = TipoCliente
    # pyrefly: ignore  # bad-override
    form_class = TipoClienteForm
    # pyrefly: ignore  # bad-override
    template_name = "clientes/tipo_cliente_form.html"
    # pyrefly: ignore  # bad-override
    success_url = reverse_lazy("clientes:tipos_cliente")

    def form_valid(self, form):
        try:
            response = super().form_valid(form)
            messages.success(self.request, "Tipo de cliente criado com sucesso!")
            logger.info(f"Tipo de cliente {form.instance.nome} criado com sucesso")
            return response
        except Exception as e:
            messages.error(self.request, f"Erro ao criar tipo de cliente: {str(e)}")
            logger.error(f"Erro ao criar tipo de cliente: {str(e)}")
            return self.form_invalid(form)


class TipoClienteUpdateView(LoginRequiredMixin, UpdateView):
    # pyrefly: ignore  # bad-override
    model = TipoCliente
    # pyrefly: ignore  # bad-override
    form_class = TipoClienteForm
    # pyrefly: ignore  # bad-override
    template_name = "clientes/tipo_cliente_form.html"
    # pyrefly: ignore  # bad-override
    success_url = reverse_lazy("clientes:tipos_cliente")

    def form_valid(self, form):
        try:
            response = super().form_valid(form)
            messages.success(self.request, "Tipo de cliente atualizado com sucesso!")
            logger.info(f"Tipo de cliente {form.instance.nome} atualizado com sucesso")
            return response
        except Exception as e:
            messages.error(self.request, f"Erro ao atualizar tipo de cliente: {str(e)}")
            logger.error(f"Erro ao atualizar tipo de cliente: {str(e)}")
            return self.form_invalid(form)


class TipoClienteDeleteView(LoginRequiredMixin, DeleteView):
    # pyrefly: ignore  # bad-override
    model = TipoCliente
    # pyrefly: ignore  # bad-override
    success_url = reverse_lazy("clientes:tipos_cliente")

    def delete(self, request, *args, **kwargs):
        try:
            tipo = self.get_object()
            if tipo.clientes.exists():
                messages.error(request, "Não é possível excluir um tipo de cliente que possui clientes vinculados!")
                return redirect(self.success_url)

            nome = tipo.nome
            response = super().delete(request, *args, **kwargs)
            messages.success(request, f"Tipo de cliente {nome} excluído com sucesso!")
            logger.info(f"Tipo de cliente {nome} excluído com sucesso")
            return response
        except Exception as e:
            messages.error(request, f"Erro ao excluir tipo de cliente: {str(e)}")
            logger.error(f"Erro ao excluir tipo de cliente: {str(e)}")
            return redirect(self.success_url)


class TagListView(LoginRequiredMixin, ListView):
    # pyrefly: ignore  # bad-override
    model = Tag
    # pyrefly: ignore  # bad-override
    template_name = "clientes/tags.html"
    # pyrefly: ignore  # bad-override
    context_object_name = "tags"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["total_tags"] = self.get_queryset().count()
        return context


class TagCreateView(LoginRequiredMixin, CreateView):
    # pyrefly: ignore  # bad-override
    model = Tag
    # pyrefly: ignore  # bad-override
    form_class = TagForm
    # pyrefly: ignore  # bad-override
    template_name = "clientes/tag_form.html"
    # pyrefly: ignore  # bad-override
    success_url = reverse_lazy("clientes:tags")

    def form_valid(self, form):
        try:
            response = super().form_valid(form)
            messages.success(self.request, "Tag criada com sucesso!")
            logger.info(f"Tag {form.instance.nome} criada com sucesso")
            return response
        except Exception as e:
            messages.error(self.request, f"Erro ao criar tag: {str(e)}")
            logger.error(f"Erro ao criar tag: {str(e)}")
            return self.form_invalid(form)


class TagUpdateView(LoginRequiredMixin, UpdateView):
    # pyrefly: ignore  # bad-override
    model = Tag
    # pyrefly: ignore  # bad-override
    form_class = TagForm
    # pyrefly: ignore  # bad-override
    template_name = "clientes/tag_form.html"
    # pyrefly: ignore  # bad-override
    success_url = reverse_lazy("clientes:tags")

    def form_valid(self, form):
        try:
            response = super().form_valid(form)
            messages.success(self.request, "Tag atualizada com sucesso!")
            logger.info(f"Tag {form.instance.nome} atualizada com sucesso")
            return response
        except Exception as e:
            messages.error(self.request, f"Erro ao atualizar tag: {str(e)}")
            logger.error(f"Erro ao atualizar tag: {str(e)}")
            return self.form_invalid(form)


class TagDeleteView(LoginRequiredMixin, DeleteView):
    # pyrefly: ignore  # bad-override
    model = Tag
    # pyrefly: ignore  # bad-override
    success_url = reverse_lazy("clientes:tags")

    def delete(self, request, *args, **kwargs):
        try:
            tag = self.get_object()
            if tag.clientes.exists():
                messages.error(request, "Não é possível excluir uma tag que possui clientes vinculados!")
                return redirect(self.success_url)

            nome = tag.nome
            response = super().delete(request, *args, **kwargs)
            messages.success(request, f"Tag {nome} excluída com sucesso!")
            logger.info(f"Tag {nome} excluída com sucesso")
            return response
        except Exception as e:
            messages.error(request, f"Erro ao excluir tag: {str(e)}")
            logger.error(f"Erro ao excluir tag: {str(e)}")
            return redirect(self.success_url)


def adicionar_tag_cliente(request, cliente_id):
    """View para adicionar uma tag a um cliente via AJAX."""
    if request.method == "POST":
        try:
            # pyrefly: ignore  # missing-attribute
            cliente = Cliente.objects.get(id=cliente_id)
            tag_id = request.POST.get("tag_id")
            # pyrefly: ignore  # missing-attribute
            tag = Tag.objects.get(id=tag_id)

            cliente.adicionar_tag(tag)
            messages.success(request, f"Tag {tag.nome} adicionada com sucesso!")
            return JsonResponse({"status": "success"})
        # pyrefly: ignore  # missing-attribute
        except (Cliente.DoesNotExist, Tag.DoesNotExist):
            return JsonResponse({"status": "error", "message": "Cliente ou tag não encontrado"}, status=404)
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)
    return JsonResponse({"status": "error", "message": "Método não permitido"}, status=405)


def remover_tag_cliente(request, cliente_id):
    """View para remover uma tag de um cliente via AJAX."""
    if request.method == "POST":
        try:
            # pyrefly: ignore  # missing-attribute
            cliente = Cliente.objects.get(id=cliente_id)
            tag_id = request.POST.get("tag_id")
            # pyrefly: ignore  # missing-attribute
            tag = Tag.objects.get(id=tag_id)

            cliente.remover_tag(tag)
            messages.success(request, f"Tag {tag.nome} removida com sucesso!")
            return JsonResponse({"status": "success"})
        # pyrefly: ignore  # missing-attribute
        except (Cliente.DoesNotExist, Tag.DoesNotExist):
            return JsonResponse({"status": "error", "message": "Cliente ou tag não encontrado"}, status=404)
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)
    return JsonResponse({"status": "error", "message": "Método não permitido"}, status=405)


@login_required
def adicionar_endereco(request, cliente_id):
    cliente = get_object_or_404(Cliente, pk=cliente_id)
    if request.method == "POST":
        form = EnderecoForm(request.POST)
        if form.is_valid():
            endereco = form.save(commit=False)
            endereco.cliente = cliente
            endereco.save()
            messages.success(request, "Endereço adicionado com sucesso.")
            return redirect("clientes:detalhe", pk=cliente.pk)
    else:
        form = EnderecoForm()
    return render(
        request, "clientes/endereco_form.html", {"form": form, "cliente": cliente, "titulo": "Adicionar Endereço"}
    )


@login_required
def editar_endereco(request, pk):
    endereco = get_object_or_404(Endereco, pk=pk)
    if request.method == "POST":
        form = EnderecoForm(request.POST, instance=endereco)
        if form.is_valid():
            form.save()
            messages.success(request, "Endereço atualizado com sucesso.")
            return redirect("clientes:detalhe", pk=endereco.cliente.pk)
    else:
        form = EnderecoForm(instance=endereco)
    return render(
        request, "clientes/endereco_form.html", {"form": form, "endereco": endereco, "titulo": "Editar Endereço"}
    )


@login_required
def excluir_endereco(request, pk):
    endereco = get_object_or_404(Endereco, pk=pk)
    cliente_pk = endereco.cliente.pk
    endereco.delete()
    messages.success(request, "Endereço excluído com sucesso.")
    return redirect("clientes:detalhe", pk=cliente_pk)


@require_GET
@login_required
def buscar_clientes_ajax(request):
    """View para busca AJAX de clientes."""
    termo = request.GET.get("term", "")
    if len(termo) < 2:
        return JsonResponse({"results": []})

    # pyrefly: ignore  # missing-attribute
    clientes = (
        Cliente.objects.filter(
            # pyrefly: ignore  # missing-attribute
            Q(nome__icontains=termo)
            | Q(cpf_cnpj__icontains=termo)
            | Q(email__icontains=termo)
            | Q(telefone__icontains=termo)
            | Q(enderecos__logradouro__icontains=termo)
            | Q(enderecos__cidade__icontains=termo)
        )
        .filter(ativo=True)
        .distinct()[:10]
    )

    results = [
        {
            "id": cliente.id,
            "text": f"{cliente.nome} ({cliente.cpf_cnpj})",
            "email": cliente.email,
            "telefone": cliente.telefone,
            "tipo": cliente.tipo_cliente.nome if cliente.tipo_cliente else "",
            "endereco": str(cliente.enderecos.first()) if cliente.enderecos.exists() else "",
        }
        for cliente in clientes
    ]

    return JsonResponse({"results": results})


from django.db.models import Q
from django.http import JsonResponse


def api_buscar_cliente(request):
    term = request.GET.get("term", "")
    if len(term) < 2:
        return JsonResponse({"results": []})

    # pyrefly: ignore  # missing-attribute
    clientes = Cliente.objects.filter(
        # pyrefly: ignore  # missing-attribute
        Q(nome__icontains=term)
        | Q(nome_loja__icontains=term)
        | Q(cpf_cnpj__icontains=term)
        | Q(email__icontains=term)
    ).values("id", "nome", "nome_loja", "email", "telefone")[:10]

    results = [
        {
            "id": cliente["id"],
            "text": f"{cliente['nome']} ({cliente['nome_loja']})" if cliente["nome_loja"] else cliente["nome"],
            "email": cliente["email"],
            "telefone": cliente["telefone"],
        }
        for cliente in clientes
    ]

    return JsonResponse({"results": results})


class SegmentoUpdateView(LoginRequiredMixin, UpdateView):
    # pyrefly: ignore  # bad-override
    model = Segmento
    # pyrefly: ignore  # bad-override
    form_class = SegmentoForm
    # pyrefly: ignore  # bad-override
    template_name = "clientes/segmento_form.html"
    # pyrefly: ignore  # bad-override
    success_url = reverse_lazy("clientes:novo_segmento")


class SegmentoDeleteView(LoginRequiredMixin, DeleteView):
    # pyrefly: ignore  # bad-override
    model = Segmento
    # pyrefly: ignore  # bad-override
    template_name = "clientes/segmento_confirm_delete.html"
    # pyrefly: ignore  # bad-override
    success_url = reverse_lazy("clientes:novo_segmento")

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object.clientes.exists():
            messages.error(request, "Não é possível excluir: existem clientes vinculados a este segmento.")
            return redirect(self.success_url)
        return super().delete(request, *args, **kwargs)
