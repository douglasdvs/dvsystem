from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q, F, Sum
from .models import Produto, CategoriaProduto, MovimentoEstoque, HistoricoPreco
from .forms import ProdutoForm, CategoriaProdutoForm, MovimentoEstoqueForm, ImportarProdutosForm, FiltroAvancadoForm
from django.db import transaction
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import datetime, timedelta
import io
import json
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
import pandas as pd
import csv
from io import StringIO
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.decorators.http import require_GET
import logging

logger = logging.getLogger(__name__)

@login_required
def listar_produtos(request):
    produtos = Produto.objects.all().order_by('-id')
    print('PRODUTOS NO BANCO:', list(produtos))
    context = {
        'page_obj': produtos,
        'total_produtos': produtos.count(),
        'categorias': CategoriaProduto.objects.all(),
    }
    return render(request, 'produtos/listar.html', context)

@login_required
def criar_produto(request):
    if request.method == 'POST':
        form = ProdutoForm(request.POST)
        try:
            if form.is_valid():
                produto = form.save()
                messages.success(request, 'Produto criado com sucesso!')
                return redirect('produtos:detalhe', id=produto.id)
            else:
                # Log dos erros do formulário
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f'Erro no campo {field}: {error}')
                        logger.error(f'Erro no campo {field}: {error}')
        except Exception as e:
            messages.error(request, f'Erro ao criar produto: {str(e)}')
            logger.error(f'Erro ao criar produto: {str(e)}')
    else:
        form = ProdutoForm()
    
    return render(request, 'produtos/form.html', {
        'form': form,
        'titulo': 'Novo Produto'
    })

@login_required
def editar_produto(request, id):
    produto = get_object_or_404(Produto, id=id)
    if request.method == 'POST':
        form = ProdutoForm(request.POST, instance=produto)
        if form.is_valid():
            produto = form.save()
            messages.success(request, 'Produto atualizado com sucesso!')
            return redirect('produtos:detalhe', id=produto.id)
    else:
        form = ProdutoForm(instance=produto)
    
    return render(request, 'produtos/form.html', {
        'form': form,
        'produto': produto,
        'titulo': f'Editar Produto: {produto.descricao}'
    })

@login_required
def excluir_produto(request, id):
    produto = get_object_or_404(Produto, id=id)
    if request.method == 'POST':
        produto.delete()
        messages.success(request, 'Produto excluído com sucesso!')
        return redirect('produtos:listar')
    return render(request, 'produtos/confirmar_exclusao.html', {'produto': produto})

@login_required
def detalhe_produto(request, id):
    produto = get_object_or_404(Produto, id=id)
    movimentos = MovimentoEstoque.objects.filter(produto=produto).order_by('-criado_em')[:10]
    historico_precos = HistoricoPreco.objects.filter(produto=produto).order_by('-data_alteracao')[:10]
    
    context = {
        'produto': produto,
        'movimentos': movimentos,
        'historico_precos': historico_precos,
    }
    return render(request, 'produtos/detalhe.html', context)

@login_required
def listar_categorias(request):
    categorias = CategoriaProduto.objects.all()
    return render(request, 'produtos/categorias_listar.html', {'categorias': categorias})

@login_required
def criar_categoria(request):
    if request.method == 'POST':
        form = CategoriaProdutoForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('produtos:listar_categorias')
    else:
        form = CategoriaProdutoForm()
    return render(request, 'produtos/categoria_form.html', {'form': form})

@login_required
def editar_categoria(request, pk):
    categoria = get_object_or_404(CategoriaProduto, pk=pk)
    if request.method == 'POST':
        form = CategoriaProdutoForm(request.POST, instance=categoria)
        if form.is_valid():
            form.save()
            return redirect('produtos:listar_categorias')
    else:
        form = CategoriaProdutoForm(instance=categoria)
    return render(request, 'produtos/categoria_form.html', {'form': form, 'categoria': categoria})

@login_required
def excluir_categoria(request, id):
    categoria = get_object_or_404(CategoriaProduto, id=id)
    if request.method == 'POST':
        categoria.delete()
        messages.success(request, 'Categoria excluída com sucesso!')
        return redirect('produtos:listar_categorias')
    return render(request, 'produtos/categorias/confirmar_exclusao.html', {'categoria': categoria})

@login_required
def listar_movimentos_estoque(request):
    movimentos = MovimentoEstoque.objects.all().order_by('-criado_em')
    return render(request, 'produtos/movimentos/listar.html', {'movimentos': movimentos})

@login_required
def listar_historico_precos(request):
    historico = HistoricoPreco.objects.all().order_by('-data_alteracao')
    return render(request, 'produtos/historico/listar.html', {'historico': historico})

@login_required
def relatorio_estoque(request):
    produtos = Produto.objects.annotate(
        valor_total=F('estoque') * F('preco_custo')
    ).order_by('descricao')
    
    total_produtos = produtos.count()
    total_valor = produtos.aggregate(total=Sum('valor_total'))['total'] or 0
    produtos_baixo_estoque = produtos.filter(estoque__lte=F('estoque_minimo')).count()
    
    context = {
        'produtos': produtos,
        'total_produtos': total_produtos,
        'total_valor': total_valor,
        'produtos_baixo_estoque': produtos_baixo_estoque,
    }
    return render(request, 'produtos/relatorios/estoque.html', context)

@login_required
@require_GET
def api_produtos(request):
    produtos = Produto.objects.all().values('id', 'codigo', 'descricao', 'preco_venda', 'estoque')
    return JsonResponse(list(produtos), safe=False)

@login_required
@require_GET
def api_categorias(request):
    categorias = CategoriaProduto.objects.filter(ativo=True).values('id', 'nome')
    return JsonResponse(list(categorias), safe=False)

@login_required
@require_GET
def api_buscar_produto(request):
    termo = request.GET.get('termo', '')
    if termo:
        produtos = Produto.objects.filter(
            Q(descricao__icontains=termo) |
            Q(codigo__icontains=termo)
        ).values('id', 'codigo', 'descricao', 'preco_venda', 'estoque')[:10]
        return JsonResponse(list(produtos), safe=False)
    return JsonResponse([], safe=False)

@login_required
def duplicar_produto(request, id):
    produto_original = get_object_or_404(Produto, id=id)
    if request.method == 'POST':
        # Cria uma cópia do produto
        produto = Produto.objects.get(id=id)
        produto.pk = None  # Isso fará com que o Django crie um novo registro
        produto.codigo = f"{produto.codigo}-COPY"  # Adiciona sufixo ao código
        produto.descricao = f"{produto.descricao} (Cópia)"  # Adiciona sufixo à descrição
        produto.save()
        
        messages.success(request, 'Produto duplicado com sucesso!')
        return redirect('produtos:detalhe', id=produto.id)
    
    return render(request, 'produtos/confirmar_duplicacao.html', {'produto': produto_original})

@login_required
def atualizar_estoque(request, id):
    produto = get_object_or_404(Produto, id=id)
    if request.method == 'POST':
        form = MovimentoEstoqueForm(request.POST)
        if form.is_valid():
            movimento = form.save(commit=False)
            movimento.produto = produto
            
            try:
                with transaction.atomic():
                    movimento.save()
                    
                    # Atualiza o estoque do produto
                    if movimento.tipo == 'entrada':
                        produto.estoque += movimento.quantidade
                    else:  # saída
                        produto.estoque -= movimento.quantidade
                    produto.save()
                
                messages.success(request, 'Estoque atualizado com sucesso!')
            except Exception as e:
                messages.error(request, f"Ocorreu um erro ao atualizar o estoque: {e}")

            return redirect('produtos:detalhe', id=produto.id)
    else:
        form = MovimentoEstoqueForm(initial={'produto': produto})
    
    return render(request, 'produtos/movimentos/form.html', {
        'form': form,
        'produto': produto,
        'titulo': f'Atualizar Estoque: {produto.descricao}'
    })

@login_required
def gerar_codigo_barras(request, id):
    produto = get_object_or_404(Produto, id=id)
    
    # Gera o código de barras se não existir
    if not produto.codigo_barras:
        produto.codigo_barras = str(uuid.uuid4().int)[:12]  # Gera um código de 12 dígitos
        produto.save()
    
    # Gera a imagem do código de barras
    ean = barcode.get('ean13', produto.codigo_barras, writer=ImageWriter())
    buffer = io.BytesIO()
    ean.write(buffer)
    buffer.seek(0)
    
    # Retorna a imagem como resposta
    response = HttpResponse(buffer.getvalue(), content_type='image/png')
    response['Content-Disposition'] = f'attachment; filename="codigo_barras_{produto.codigo}.png"'
    return response

@login_required
def gerar_etiqueta(request, id):
    produto = get_object_or_404(Produto, id=id)
    return render(request, 'produtos/etiqueta.html', {
        'produto': produto,
        'titulo': f'Etiqueta: {produto.descricao}'
    })

@login_required
def gerar_etiquetas_multiplas(request):
    if request.method == 'POST':
        produtos_ids = request.POST.getlist('produtos')
        produtos = Produto.objects.filter(id__in=produtos_ids)
        return render(request, 'produtos/etiquetas_multiplas.html', {
            'produtos': produtos,
            'titulo': 'Etiquetas Múltiplas'
        })
    
    produtos = Produto.objects.all()
    return render(request, 'produtos/selecionar_etiquetas.html', {
        'produtos': produtos,
        'titulo': 'Selecionar Produtos para Etiquetas'
    })

@login_required
def importar_produtos(request):
    if request.method == 'POST':
        form = ImportarProdutosForm(request.POST, request.FILES)
        if form.is_valid():
            arquivo = request.FILES['arquivo']
            atualizar_existentes = form.cleaned_data['atualizar_existentes']
            
            try:
                if arquivo.name.endswith('.csv'):
                    df = pd.read_csv(arquivo)
                else:
                    df = pd.read_excel(arquivo)
                
                produtos_importados = 0
                produtos_atualizados = 0
                erros = []
                
                for _, row in df.iterrows():
                    try:
                        codigo = str(row.get('codigo', '')).strip()
                        if not codigo:
                            continue
                            
                        produto_data = {
                            'descricao': row.get('descricao', '').strip(),
                            'categoria': row.get('categoria', '').strip(),
                            'preco_custo': float(row.get('preco_custo', 0)),
                            'margem_lucro': float(row.get('margem_lucro', 0)),
                            'estoque': int(row.get('estoque', 0)),
                            'estoque_minimo': int(row.get('estoque_minimo', 0)),
                            'unidade_medida': row.get('unidade_medida', 'UN').strip(),
                            'peso': float(row.get('peso', 0)),
                        }
                        
                        if atualizar_existentes:
                            produto, created = Produto.objects.update_or_create(
                                codigo=codigo,
                                defaults=produto_data
                            )
                            if created:
                                produtos_importados += 1
                            else:
                                produtos_atualizados += 1
                        else:
                            if not Produto.objects.filter(codigo=codigo).exists():
                                Produto.objects.create(codigo=codigo, **produto_data)
                                produtos_importados += 1
                            
                    except Exception as e:
                        erros.append(f"Erro na linha {_ + 2}: {str(e)}")
                
                if erros:
                    messages.warning(request, f'Importação concluída com {len(erros)} erros.')
                    for erro in erros:
                        messages.error(request, erro)
                else:
                    messages.success(request, f'Importação concluída com sucesso! {produtos_importados} produtos importados, {produtos_atualizados} atualizados.')
                
                return redirect('produtos:listar')
                
            except Exception as e:
                messages.error(request, f'Erro ao processar arquivo: {str(e)}')
    else:
        form = ImportarProdutosForm()
    
    return render(request, 'produtos/importar.html', {
        'form': form,
        'titulo': 'Importar Produtos'
    })

@login_required
def exportar_excel(request):
    produtos = Produto.objects.all().values(
        'codigo', 'descricao', 'categoria__nome', 'preco_custo',
        'margem_lucro', 'preco_venda', 'estoque', 'estoque_minimo',
        'unidade_medida', 'peso'
    )
    
    df = pd.DataFrame(produtos)
    df.columns = [
        'Código', 'Descrição', 'Categoria', 'Preço Custo',
        'Margem Lucro (%)', 'Preço Venda', 'Estoque',
        'Estoque Mínimo', 'Unidade', 'Peso'
    ]
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name='Produtos', index=False)
        
        # Ajusta a largura das colunas
        worksheet = writer.sheets['Produtos']
        for i, col in enumerate(df.columns):
            max_length = max(df[col].astype(str).apply(len).max(), len(col)) + 2
            worksheet.set_column(i, i, max_length)
    
    output.seek(0)
    response = HttpResponse(
        output.read(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename=produtos.xlsx'
    return response

@login_required
def exportar_csv(request):
    produtos = Produto.objects.all().values(
        'codigo', 'descricao', 'categoria__nome', 'preco_custo',
        'margem_lucro', 'preco_venda', 'estoque', 'estoque_minimo',
        'unidade_medida', 'peso'
    )
    
    output = StringIO()
    writer = csv.writer(output)
    
    # Escreve o cabeçalho
    writer.writerow([
        'Código', 'Descrição', 'Categoria', 'Preço Custo',
        'Margem Lucro (%)', 'Preço Venda', 'Estoque',
        'Estoque Mínimo', 'Unidade', 'Peso'
    ])
    
    # Escreve os dados
    for produto in produtos:
        writer.writerow([
            produto['codigo'],
            produto['descricao'],
            produto['categoria__nome'],
            produto['preco_custo'],
            produto['margem_lucro'],
            produto['preco_venda'],
            produto['estoque'],
            produto['estoque_minimo'],
            produto['unidade_medida'],
            produto['peso']
        ])
    
    output.seek(0)
    response = HttpResponse(output.getvalue(), content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename=produtos.csv'
    return response

@login_required
def download_modelo_importacao(request):
    # Cria um DataFrame com as colunas necessárias
    df = pd.DataFrame(columns=[
        'codigo', 'descricao', 'categoria', 'preco_custo',
        'margem_lucro', 'estoque', 'estoque_minimo',
        'unidade_medida', 'peso'
    ])
    
    # Adiciona algumas linhas de exemplo
    df.loc[0] = [
        '001', 'Produto Exemplo', 'Categoria Exemplo',
        10.00, 30.00, 100, 10, 'UN', 0.5
    ]
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name='Modelo', index=False)
        
        # Adiciona uma aba de instruções
        workbook = writer.book
        worksheet = workbook.add_worksheet('Instruções')
        
        instrucoes = [
            ['Instruções para Importação de Produtos'],
            [''],
            ['Colunas Obrigatórias:'],
            ['- codigo: Código único do produto'],
            ['- descricao: Descrição do produto'],
            ['- categoria: Nome da categoria'],
            ['- preco_custo: Preço de custo (decimal)'],
            ['- margem_lucro: Margem de lucro em % (decimal)'],
            ['- estoque: Quantidade em estoque (inteiro)'],
            ['- estoque_minimo: Estoque mínimo (inteiro)'],
            ['- unidade_medida: Unidade de medida (ex: UN, KG)'],
            ['- peso: Peso do produto (decimal)'],
            [''],
            ['Observações:'],
            ['1. O arquivo deve estar no formato Excel (.xlsx) ou CSV'],
            ['2. A primeira linha deve conter os nomes das colunas'],
            ['3. Valores numéricos devem usar ponto como separador decimal'],
            ['4. Não use caracteres especiais no código do produto']
        ]
        
        for i, linha in enumerate(instrucoes):
            for j, texto in enumerate(linha):
                worksheet.write(i, j, texto)
        
        # Ajusta a largura das colunas
        worksheet.set_column(0, 0, 50)
    
    output.seek(0)
    response = HttpResponse(
        output.read(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename=modelo_importacao_produtos.xlsx'
    return response

class CategoriaProdutoListView(LoginRequiredMixin, ListView):
    model = CategoriaProduto
    template_name = 'produtos/categoria_list.html'
    context_object_name = 'categorias'
    ordering = ['nome']

class CategoriaProdutoCreateView(LoginRequiredMixin, CreateView):
    model = CategoriaProduto
    form_class = CategoriaProdutoForm
    template_name = 'produtos/categoria_form.html'
    success_url = reverse_lazy('produtos:listar_categorias')
    
    def form_valid(self, form):
        try:
            response = super().form_valid(form)
            messages.success(self.request, 'Categoria criada com sucesso!')
            logger.info(f'Categoria {form.instance.nome} criada com sucesso')
            return response
        except Exception as e:
            messages.error(self.request, f'Erro ao criar categoria: {str(e)}')
            logger.error(f'Erro ao criar categoria: {str(e)}')
            return self.form_invalid(form)

class CategoriaProdutoUpdateView(LoginRequiredMixin, UpdateView):
    model = CategoriaProduto
    form_class = CategoriaProdutoForm
    template_name = 'produtos/categoria_form.html'
    success_url = reverse_lazy('produtos:listar_categorias')
    
    def form_valid(self, form):
        try:
            response = super().form_valid(form)
            messages.success(self.request, 'Categoria atualizada com sucesso!')
            logger.info(f'Categoria {form.instance.nome} atualizada com sucesso')
            return response
        except Exception as e:
            messages.error(self.request, f'Erro ao atualizar categoria: {str(e)}')
            logger.error(f'Erro ao atualizar categoria: {str(e)}')
            return self.form_invalid(form)

class CategoriaProdutoDeleteView(LoginRequiredMixin, DeleteView):
    model = CategoriaProduto
    success_url = reverse_lazy('produtos:listar_categorias')
    
    def delete(self, request, *args, **kwargs):
        try:
            categoria = self.get_object()
            if categoria.produtos.exists():
                messages.error(request, 'Não é possível excluir uma categoria que possui produtos vinculados!')
                return redirect(self.success_url)
            
            nome = categoria.nome
            response = super().delete(request, *args, **kwargs)
            messages.success(request, f'Categoria {nome} excluída com sucesso!')
            logger.info(f'Categoria {nome} excluída com sucesso')
            return response
        except Exception as e:
            messages.error(request, f'Erro ao excluir categoria: {str(e)}')
            logger.error(f'Erro ao excluir categoria: {str(e)}')
            return redirect(self.success_url)
