import csv
import io
import json
import logging
import uuid
from datetime import datetime, timedelta
from io import StringIO

import pandas as pd
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.db.models import F, Q, Sum
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.decorators.http import require_GET
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from .forms import CategoriaProdutoForm, FiltroAvancadoForm, ImportarProdutosForm, MovimentoEstoqueForm, ProdutoForm
from .models import CategoriaProduto, HistoricoPreco, MovimentoEstoque, Produto

# Imports para código de barras
try:
    import barcode
    from barcode.writer import ImageWriter

    BARCODE_AVAILABLE = True
except ImportError:
    barcode = None
    ImageWriter = None
    BARCODE_AVAILABLE = False

logger = logging.getLogger(__name__)


@login_required
def listar_produtos(request):
    # pyrefly: ignore  # missing-attribute
    produtos = Produto.objects.all()
    busca = request.GET.get("busca", "").strip()
    categoria = request.GET.get("categoria", "")
    status = request.GET.get("status", "")

    if busca:
        produtos = produtos.filter(Q(descricao__icontains=busca) | Q(codigo__icontains=busca))
    if categoria:
        produtos = produtos.filter(categoria_id=categoria)
    if status == "ativos":
        produtos = produtos.filter(ativo=True)
    elif status == "inativos":
        produtos = produtos.filter(ativo=False)

    produtos = produtos.order_by("descricao")
    # Paginação
    from django.core.paginator import Paginator

    paginator = Paginator(produtos, 15)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    context = {
        "page_obj": page_obj,
        "total_produtos": produtos.count(),
        # pyrefly: ignore  # missing-attribute
        "categorias": CategoriaProduto.objects.all(),
    }
    return render(request, "produtos/listar.html", context)


@login_required
def criar_produto(request):
    if request.method == "POST":
        form = ProdutoForm(request.POST)
        try:
            if form.is_valid():
                produto = form.save()
                messages.success(request, "Produto criado com sucesso!")
                return redirect("produtos:detalhe", id=produto.id)
            else:
                # Log dos erros do formulário
                # pyrefly: ignore  # missing-attribute
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f"Erro no campo {field}: {error}")
                        logger.error(f"Erro no campo {field}: {error}")
        except Exception as e:
            messages.error(request, f"Erro ao criar produto: {str(e)}")
            logger.error(f"Erro ao criar produto: {str(e)}")
    else:
        form = ProdutoForm()

    return render(request, "produtos/form.html", {"form": form, "titulo": "Novo Produto"})


@login_required
def editar_produto(request, id):
    produto = get_object_or_404(Produto, id=id)
    if request.method == "POST":
        form = ProdutoForm(request.POST, instance=produto)
        if form.is_valid():
            produto = form.save()
            messages.success(request, "Produto atualizado com sucesso!")
            return redirect("produtos:detalhe", id=produto.id)
    else:
        form = ProdutoForm(instance=produto)

    return render(
        request,
        "produtos/form.html",
        {"form": form, "produto": produto, "titulo": f"Editar Produto: {produto.descricao}"},
    )


@login_required
def excluir_produto(request, id):
    produto = get_object_or_404(Produto, id=id)
    if request.method == "POST":
        produto.delete()
        messages.success(request, "Produto excluído com sucesso!")
        return redirect("produtos:index")
    return render(request, "produtos/confirmar_exclusao.html", {"produto": produto})


@login_required
def detalhe_produto(request, id):
    produto = get_object_or_404(Produto, id=id)
    # pyrefly: ignore  # missing-attribute
    movimentos = MovimentoEstoque.objects.filter(produto=produto).order_by("-criado_em")[:10]
    # pyrefly: ignore  # missing-attribute
    historico_precos = HistoricoPreco.objects.filter(produto=produto).order_by("-data_alteracao")[:10]

    context = {
        "produto": produto,
        "movimentos": movimentos,
        "historico_precos": historico_precos,
    }
    return render(request, "produtos/detalhe.html", context)


@login_required
def listar_categorias(request):
    # pyrefly: ignore  # missing-attribute
    categorias = CategoriaProduto.objects.all()
    return render(request, "produtos/categorias_listar.html", {"categorias": categorias})


@login_required
def criar_categoria(request):
    if request.method == "POST":
        form = CategoriaProdutoForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("produtos:listar_categorias")
    else:
        form = CategoriaProdutoForm()
    return render(request, "produtos/categoria_form.html", {"form": form})


@login_required
def editar_categoria(request, pk):
    categoria = get_object_or_404(CategoriaProduto, pk=pk)
    if request.method == "POST":
        form = CategoriaProdutoForm(request.POST, instance=categoria)
        if form.is_valid():
            form.save()
            return redirect("produtos:listar_categorias")
    else:
        form = CategoriaProdutoForm(instance=categoria)
    return render(request, "produtos/categoria_form.html", {"form": form, "categoria": categoria})


@login_required
def excluir_categoria(request, id):
    categoria = get_object_or_404(CategoriaProduto, id=id)
    if request.method == "POST":
        categoria.delete()
        messages.success(request, "Categoria excluída com sucesso!")
        return redirect("produtos:listar_categorias")
    return render(request, "produtos/categorias/confirmar_exclusao.html", {"categoria": categoria})


@login_required
def listar_movimentos_estoque(request):
    # pyrefly: ignore  # missing-attribute
    movimentos = MovimentoEstoque.objects.all().order_by("-criado_em")
    return render(request, "produtos/movimentos/listar.html", {"movimentos": movimentos})


@login_required
def listar_historico_precos(request):
    # pyrefly: ignore  # missing-attribute
    historico = HistoricoPreco.objects.all().order_by("-data_alteracao")
    return render(request, "produtos/historico/listar.html", {"historico": historico})


@login_required
def relatorio_estoque(request):
    # pyrefly: ignore  # missing-attribute
    produtos = Produto.objects.annotate(valor_total=F("estoque") * F("preco_custo")).order_by("descricao")

    total_produtos = produtos.count()
    total_valor = produtos.aggregate(total=Sum("valor_total"))["total"] or 0
    produtos_baixo_estoque = produtos.filter(estoque__lte=F("estoque_minimo")).count()

    context = {
        "produtos": produtos,
        "total_produtos": total_produtos,
        "total_valor": total_valor,
        "produtos_baixo_estoque": produtos_baixo_estoque,
    }
    return render(request, "produtos/relatorios/estoque.html", context)


@login_required
@require_GET
def api_produtos(request):
    # pyrefly: ignore  # missing-attribute
    produtos = Produto.objects.all().values("id", "codigo", "descricao", "preco_venda", "estoque")
    return JsonResponse(list(produtos), safe=False)


@login_required
@require_GET
def api_categorias(request):
    # pyrefly: ignore  # missing-attribute
    categorias = CategoriaProduto.objects.filter(ativo=True).values("id", "nome")
    return JsonResponse(list(categorias), safe=False)


@login_required
@require_GET
def api_buscar_produto(request):
    termo = request.GET.get("termo", "")
    if termo:
        # pyrefly: ignore  # missing-attribute
        produtos = Produto.objects.filter(Q(descricao__icontains=termo) | Q(codigo__icontains=termo)).values(
            "id", "codigo", "descricao", "preco_venda", "estoque"
        )[:10]
        return JsonResponse(list(produtos), safe=False)
    return JsonResponse([], safe=False)


@login_required
def duplicar_produto(request, id):
    produto_original = get_object_or_404(Produto, id=id)
    if request.method == "POST":
        # pyrefly: ignore  # missing-attribute
        produto = Produto.objects.get(id=id)
        produto.pk = None  # Novo registro
        produto.codigo = None  # Deixa em branco para gerar sequencial
        produto.descricao = f"{produto.descricao} (CÓPIA)"  # Opcional: indicar cópia na descrição
        produto.save()
        messages.success(request, "Produto duplicado com sucesso!")
        return redirect("produtos:detalhe", id=produto.id)
    return render(request, "produtos/confirmar_duplicacao.html", {"produto": produto_original})


@login_required
def atualizar_estoque(request, id):
    produto = get_object_or_404(Produto, id=id)
    if request.method == "POST":
        form = MovimentoEstoqueForm(request.POST)
        if form.is_valid():
            movimento = form.save(commit=False)
            movimento.produto = produto

            try:
                # pyrefly: ignore  # missing-attribute
                with transaction.atomic():
                    movimento.save()

                    # Atualiza o estoque do produto
                    if movimento.tipo == "entrada":
                        produto.estoque += movimento.quantidade
                    else:  # saída
                        produto.estoque -= movimento.quantidade
                    produto.save()

                messages.success(request, "Estoque atualizado com sucesso!")
            except Exception as e:
                messages.error(request, f"Ocorreu um erro ao atualizar o estoque: {e}")

            return redirect("produtos:detalhe", id=produto.id)
    else:
        form = MovimentoEstoqueForm(initial={"produto": produto})

    return render(
        request,
        "produtos/movimentos/form.html",
        {"form": form, "produto": produto, "titulo": f"Atualizar Estoque: {produto.descricao}"},
    )


@login_required
def gerar_codigo_barras(request, id):
    produto = get_object_or_404(Produto, id=id)

    if not BARCODE_AVAILABLE:
        messages.error(
            request, "Biblioteca de código de barras não está instalada. Execute: pip install python-barcode[images]"
        )
        return redirect("produtos:detalhe", id=produto.id)

    # Gera o código de barras se não existir
    if not produto.codigo_barras:
        produto.codigo_barras = str(uuid.uuid4().int)[:12]  # Gera um código de 12 dígitos
        produto.save()

    try:
        # Gera a imagem do código de barras
        ean = barcode.get("ean13", produto.codigo_barras, writer=ImageWriter())
        buffer = io.BytesIO()
        ean.write(buffer)
        buffer.seek(0)

        # Retorna a imagem como resposta
        response = HttpResponse(buffer.getvalue(), content_type="image/png")
        response["Content-Disposition"] = f'attachment; filename="codigo_barras_{produto.codigo}.png"'
        return response
    except Exception as e:
        messages.error(request, f"Erro ao gerar código de barras: {str(e)}")
        return redirect("produtos:detalhe", id=produto.id)


@login_required
def gerar_etiqueta(request, id):
    produto = get_object_or_404(Produto, id=id)
    return render(request, "produtos/etiqueta.html", {"produto": produto, "titulo": f"Etiqueta: {produto.descricao}"})


@login_required
def gerar_etiquetas_multiplas(request):
    if request.method == "POST":
        produtos_ids = request.POST.getlist("produtos")
        # pyrefly: ignore  # missing-attribute
        produtos = Produto.objects.filter(id__in=produtos_ids)
        return render(
            request, "produtos/etiquetas_multiplas.html", {"produtos": produtos, "titulo": "Etiquetas Múltiplas"}
        )

    # pyrefly: ignore  # missing-attribute
    produtos = Produto.objects.all()
    return render(
        request,
        "produtos/selecionar_etiquetas.html",
        {"produtos": produtos, "titulo": "Selecionar Produtos para Etiquetas"},
    )


@login_required
def importar_produtos(request):
    if request.method == "POST":
        form = ImportarProdutosForm(request.POST, request.FILES)
        if form.is_valid():
            arquivo = request.FILES["arquivo"]
            atualizar_existentes = form.cleaned_data["atualizar_existentes"]

            try:
                if arquivo.name.endswith(".csv"):
                    df = pd.read_csv(arquivo)
                else:
                    df = pd.read_excel(arquivo)

                produtos_importados = 0
                produtos_atualizados = 0
                erros = []

                for _, row in df.iterrows():
                    try:
                        codigo = str(row.get("codigo", "")).strip()
                        if not codigo:
                            continue

                        produto_data = {
                            # pyrefly: ignore  # missing-attribute
                            "descricao": row.get("descricao", "").strip(),
                            # pyrefly: ignore  # missing-attribute
                            "categoria": row.get("categoria", "").strip(),
                            # pyrefly: ignore  # bad-argument-type
                            "preco_custo": float(row.get("preco_custo", 0)),
                            # pyrefly: ignore  # bad-argument-type
                            "margem_lucro": float(row.get("margem_lucro", 0)),
                            # pyrefly: ignore  # no-matching-overload
                            "estoque": int(row.get("estoque", 0)),
                            # pyrefly: ignore  # no-matching-overload
                            "estoque_minimo": int(row.get("estoque_minimo", 0)),
                            # pyrefly: ignore  # missing-attribute
                            "unidade_medida": row.get("unidade_medida", "UN").strip(),
                            # pyrefly: ignore  # bad-argument-type
                            "peso": float(row.get("peso", 0)),
                        }

                        if atualizar_existentes:
                            # pyrefly: ignore  # missing-attribute
                            produto, created = Produto.objects.update_or_create(codigo=codigo, defaults=produto_data)
                            if created:
                                produtos_importados += 1
                            else:
                                produtos_atualizados += 1
                        else:
                            # pyrefly: ignore  # missing-attribute
                            if not Produto.objects.filter(codigo=codigo).exists():
                                # pyrefly: ignore  # missing-attribute
                                Produto.objects.create(codigo=codigo, **produto_data)
                                produtos_importados += 1

                    except Exception as e:
                        # pyrefly: ignore  # bad-argument-type
                        erros.append(f"Erro na linha {_ + 2}: {str(e)}")

                if erros:
                    messages.warning(request, f"Importação concluída com {len(erros)} erros.")
                    for erro in erros:
                        messages.error(request, erro)
                else:
                    messages.success(
                        request,
                        f"Importação concluída com sucesso! {produtos_importados} produtos importados, {produtos_atualizados} atualizados.",
                    )

                return redirect("produtos:listar")

            except Exception as e:
                messages.error(request, f"Erro ao processar arquivo: {str(e)}")
    else:
        form = ImportarProdutosForm()

    return render(request, "produtos/importar.html", {"form": form, "titulo": "Importar Produtos"})


@login_required
def exportar_excel(request):
    # pyrefly: ignore  # missing-attribute
    produtos = Produto.objects.all().values(
        "codigo",
        "descricao",
        "categoria__nome",
        "preco_custo",
        "margem_lucro",
        "preco_venda",
        "estoque",
        "estoque_minimo",
        "unidade_medida",
        "peso",
    )

    df = pd.DataFrame(produtos)
    df.columns = [
        "Código",
        "Descrição",
        "Categoria",
        "Preço Custo",
        "Margem Lucro (%)",
        "Preço Venda",
        "Estoque",
        "Estoque Mínimo",
        "Unidade",
        "Peso",
    ]

    output = io.BytesIO()
    # pyrefly: ignore  # bad-argument-type
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, sheet_name="Produtos", index=False)

        # Ajusta a largura das colunas
        worksheet = writer.sheets["Produtos"]
        for i, col in enumerate(df.columns):
            max_length = max(df[col].astype(str).apply(len).max(), len(col)) + 2
            worksheet.set_column(i, i, max_length)

    output.seek(0)
    response = HttpResponse(
        output.read(), content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = "attachment; filename=produtos.xlsx"
    return response


@login_required
def exportar_csv(request):
    # pyrefly: ignore  # missing-attribute
    produtos = Produto.objects.all().values(
        "codigo",
        "descricao",
        "categoria__nome",
        "preco_custo",
        "margem_lucro",
        "preco_venda",
        "estoque",
        "estoque_minimo",
        "unidade_medida",
        "peso",
    )

    output = StringIO()
    writer = csv.writer(output)

    # Escreve o cabeçalho
    writer.writerow(
        [
            "Código",
            "Descrição",
            "Categoria",
            "Preço Custo",
            "Margem Lucro (%)",
            "Preço Venda",
            "Estoque",
            "Estoque Mínimo",
            "Unidade",
            "Peso",
        ]
    )

    # Escreve os dados
    for produto in produtos:
        writer.writerow(
            [
                produto["codigo"],
                produto["descricao"],
                produto["categoria__nome"],
                produto["preco_custo"],
                produto["margem_lucro"],
                produto["preco_venda"],
                produto["estoque"],
                produto["estoque_minimo"],
                produto["unidade_medida"],
                produto["peso"],
            ]
        )

    output.seek(0)
    response = HttpResponse(output.getvalue(), content_type="text/csv")
    response["Content-Disposition"] = "attachment; filename=produtos.csv"
    return response


@login_required
def download_modelo_importacao(request):
    # Cria um DataFrame com as colunas necessárias
    # pyrefly: ignore  # bad-argument-type
    df = pd.DataFrame(
        columns=[
            "codigo",
            "descricao",
            "categoria",
            "preco_custo",
            "margem_lucro",
            "estoque",
            "estoque_minimo",
            "unidade_medida",
            "peso",
        ]
    )

    # Adiciona algumas linhas de exemplo
    df.loc[0] = ["001", "Produto Exemplo", "Categoria Exemplo", 10.00, 30.00, 100, 10, "UN", 0.5]

    output = io.BytesIO()
    # pyrefly: ignore  # bad-argument-type
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, sheet_name="Modelo", index=False)

        # Adiciona uma aba de instruções
        workbook = writer.book
        worksheet = workbook.add_worksheet("Instruções")

        instrucoes = [
            ["Instruções para Importação de Produtos"],
            [""],
            ["Colunas Obrigatórias:"],
            ["- codigo: Código único do produto"],
            ["- descricao: Descrição do produto"],
            ["- categoria: Nome da categoria"],
            ["- preco_custo: Preço de custo (decimal)"],
            ["- margem_lucro: Margem de lucro em % (decimal)"],
            ["- estoque: Quantidade em estoque (inteiro)"],
            ["- estoque_minimo: Estoque mínimo (inteiro)"],
            ["- unidade_medida: Unidade de medida (ex: UN, KG)"],
            ["- peso: Peso do produto (decimal)"],
            [""],
            ["Observações:"],
            ["1. O arquivo deve estar no formato Excel (.xlsx) ou CSV"],
            ["2. A primeira linha deve conter os nomes das colunas"],
            ["3. Valores numéricos devem usar ponto como separador decimal"],
            ["4. Não use caracteres especiais no código do produto"],
        ]

        for i, linha in enumerate(instrucoes):
            for j, texto in enumerate(linha):
                worksheet.write(i, j, texto)

        # Ajusta a largura das colunas
        worksheet.set_column(0, 0, 50)

    output.seek(0)
    response = HttpResponse(
        output.read(), content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = "attachment; filename=modelo_importacao_produtos.xlsx"
    return response


class CategoriaProdutoListView(LoginRequiredMixin, ListView):
    # pyrefly: ignore  # bad-override
    model = CategoriaProduto
    # pyrefly: ignore  # bad-override
    template_name = "produtos/categoria_list.html"
    # pyrefly: ignore  # bad-override
    context_object_name = "categorias"
    # pyrefly: ignore  # bad-override
    ordering = ["nome"]


class CategoriaProdutoCreateView(LoginRequiredMixin, CreateView):
    # pyrefly: ignore  # bad-override
    model = CategoriaProduto
    # pyrefly: ignore  # bad-override
    form_class = CategoriaProdutoForm
    # pyrefly: ignore  # bad-override
    template_name = "produtos/categoria_form.html"
    # pyrefly: ignore  # bad-override
    success_url = reverse_lazy("produtos:listar_categorias")

    def form_valid(self, form):
        try:
            response = super().form_valid(form)
            messages.success(self.request, "Categoria criada com sucesso!")
            logger.info(f"Categoria {form.instance.nome} criada com sucesso")
            return response
        except Exception as e:
            messages.error(self.request, f"Erro ao criar categoria: {str(e)}")
            logger.error(f"Erro ao criar categoria: {str(e)}")
            return self.form_invalid(form)


class CategoriaProdutoUpdateView(LoginRequiredMixin, UpdateView):
    # pyrefly: ignore  # bad-override
    model = CategoriaProduto
    # pyrefly: ignore  # bad-override
    form_class = CategoriaProdutoForm
    # pyrefly: ignore  # bad-override
    template_name = "produtos/categoria_form.html"
    # pyrefly: ignore  # bad-override
    success_url = reverse_lazy("produtos:listar_categorias")

    def form_valid(self, form):
        try:
            response = super().form_valid(form)
            messages.success(self.request, "Categoria atualizada com sucesso!")
            logger.info(f"Categoria {form.instance.nome} atualizada com sucesso")
            return response
        except Exception as e:
            messages.error(self.request, f"Erro ao atualizar categoria: {str(e)}")
            logger.error(f"Erro ao atualizar categoria: {str(e)}")
            return self.form_invalid(form)


class CategoriaProdutoDeleteView(LoginRequiredMixin, DeleteView):
    # pyrefly: ignore  # bad-override
    model = CategoriaProduto
    # pyrefly: ignore  # bad-override
    success_url = reverse_lazy("produtos:listar_categorias")

    def delete(self, request, *args, **kwargs):
        try:
            categoria = self.get_object()
            if categoria.produtos.exists():
                messages.error(request, "Não é possível excluir uma categoria que possui produtos vinculados!")
                return redirect(self.success_url)

            nome = categoria.nome
            response = super().delete(request, *args, **kwargs)
            messages.success(request, f"Categoria {nome} excluída com sucesso!")
            logger.info(f"Categoria {nome} excluída com sucesso")
            return response
        except Exception as e:
            messages.error(request, f"Erro ao excluir categoria: {str(e)}")
            logger.error(f"Erro ao excluir categoria: {str(e)}")
            return redirect(self.success_url)
