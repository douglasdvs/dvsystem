from datetime import datetime
from decimal import Decimal

import pandas as pd
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db.models import Case, Count, ExpressionWrapper, F, FloatField, Max, Q, Sum, When
from django.http import HttpResponse
from django.shortcuts import render

from clientes.models import Cliente
from financeiro.models import Despesa
from pedidos.models import ItemPedido, Pedido
from produtos.models import CATEGORIAS_PRODUTO, Produto
from vendedores.models import Vendedor


def index(request):
    # pyrefly: ignore  # missing-attribute
    total_clientes = Cliente.objects.count()
    # pyrefly: ignore  # missing-attribute
    total_pedidos = Pedido.objects.count()
    # pyrefly: ignore  # missing-attribute
    # Usa agregação SQL para total vendido
    total_vendido = Pedido.objects.aggregate(total=Sum(F('itens__quantidade') * F('itens__preco_unitario')))['total'] or 0
    # pyrefly: ignore  # missing-attribute
    total_produtos = Produto.objects.count()
    total_vendedores = len(Pedido.VENDEDORES_CHOICES)
    return render(
        request,
        "relatorios/index.html",
        {
            "total_clientes": total_clientes,
            "total_pedidos": total_pedidos,
            "total_vendido": total_vendido,
            "total_produtos": total_produtos,
            "total_vendedores": total_vendedores,
        },
    )


def get_pedidos_filtrados(request):
    from django.utils.dateparse import parse_date

    inicio = request.GET.get("inicio")
    fim = request.GET.get("fim")
    categoria = request.GET.get("categoria", "")
    vendedor = request.GET.get("vendedor", "")
    # pyrefly: ignore  # missing-attribute
    pedidos = Pedido.objects.all().select_related("cliente").prefetch_related("itens")
    erro_data = None
    # Validação de datas
    if inicio and fim:
        try:
            data_inicio = parse_date(inicio)
            data_fim = parse_date(fim)
            if data_inicio and data_fim and data_inicio > data_fim:
                erro_data = "Data inicial não pode ser maior que a final."
        except Exception:
            erro_data = "Formato de data inválido."
    if inicio:
        pedidos = pedidos.filter(data__gte=inicio)
    if fim:
        pedidos = pedidos.filter(data__lte=fim)
    if vendedor:
        # Filtra por nome do vendedor (campo nome em Vendedor)
        pedidos = pedidos.filter(vendedor__nome=vendedor)
    if categoria:
        # Filtra por nome da categoria
        pedidos = pedidos.filter(itens__produto__categoria__nome=categoria)
    return pedidos, erro_data


def relatorio_abc_clientes(request):
    pedidos, erro_data = get_pedidos_filtrados(request)
    # Calcula o total geral de forma eficiente
    total_geral_agg = pedidos.aggregate(
        total_geral=Sum(F("itens__quantidade") * F("itens__preco_unitario"), output_field=FloatField())
    )
    total_geral = total_geral_agg["total_geral"] or 1.0
    # Soma total por cliente
    dados = (
        pedidos.values("cliente__nome")
        .annotate(total=Sum(F("itens__quantidade") * F("itens__preco_unitario"), output_field=FloatField()))
        .order_by("-total")
    )
    acumulado = 0
    resultado = []
    for d in dados:
        percentual = (d["total"] / total_geral) * 100
        acumulado += percentual
        if acumulado <= 80:
            grupo = "A"
        elif acumulado <= 95:
            grupo = "B"
        else:
            grupo = "C"
        resultado.append(
            {
                "cliente": d["cliente__nome"],
                "total": d["total"],
                "percentual": percentual,
                "acumulado": acumulado,
                "grupo": grupo,
            }
        )
    # Paginação
    page = request.GET.get("page", 1)
    paginator = Paginator(resultado, 30)  # 30 por página
    try:
        resultado_paginado = paginator.page(page)
    except PageNotAnInteger:
        resultado_paginado = paginator.page(1)
    except EmptyPage:
        resultado_paginado = paginator.page(paginator.num_pages)
    categorias = CATEGORIAS_PRODUTO
    VENDEDORES_CHOICES = Pedido.VENDEDORES_CHOICES
    return render(
        request,
        "relatorios/abc_clientes.html",
        {
            "dados": resultado_paginado,
            "inicio": request.GET.get("inicio"),
            "fim": request.GET.get("fim"),
            "categoria": request.GET.get("categoria", ""),
            "categorias": categorias,
            "vendedor": request.GET.get("vendedor", ""),
            "vendedores": VENDEDORES_CHOICES,
            "erro_data": erro_data,
        },
    )


def get_clientes_sem_compras_filtrados(request):
    from django.utils.dateparse import parse_date

    inicio = request.GET.get("inicio")
    fim = request.GET.get("fim")
    categoria = request.GET.get("categoria", "")
    vendedor = request.GET.get("vendedor", "")
    # pyrefly: ignore  # missing-attribute
    clientes = Cliente.objects.all()
    # pyrefly: ignore  # missing-attribute
    pedidos = Pedido.objects.all().select_related("cliente")
    erro_data = None
    if inicio and fim:
        try:
            data_inicio = parse_date(inicio)
            data_fim = parse_date(fim)
            if data_inicio and data_fim and data_inicio > data_fim:
                erro_data = "Data inicial não pode ser maior que a final."
        except Exception:
            erro_data = "Formato de data inválido."
    if inicio:
        pedidos = pedidos.filter(data__gte=inicio)
    if fim:
        pedidos = pedidos.filter(data__lte=fim)
    if vendedor:
        pedidos = pedidos.filter(vendedor__nome=vendedor)
    if categoria:
        pedidos = pedidos.filter(itens__produto__categoria__nome=categoria)
    clientes_com_pedido = pedidos.values_list("cliente_id", flat=True).distinct()
    clientes_sem_compras = clientes.exclude(id__in=clientes_com_pedido)
    return clientes_sem_compras, erro_data


def relatorio_clientes_sem_compras(request):
    clientes_sem_compras, erro_data = get_clientes_sem_compras_filtrados(request)
    resultado = []
    for cliente in clientes_sem_compras:
        # pyrefly: ignore  # missing-attribute
        ultimo_pedido = Pedido.objects.filter(cliente=cliente).order_by("-data").first()
        resultado.append(
            {
                "nome": cliente.nome,
                "contato": cliente.email or cliente.telefone,
                "ultima_compra": ultimo_pedido.data if ultimo_pedido else None,
                "vendedor": ultimo_pedido.vendedor if ultimo_pedido else "",
            }
        )
    # Paginação
    from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator

    page = request.GET.get("page", 1)
    paginator = Paginator(resultado, 30)
    try:
        resultado_paginado = paginator.page(page)
    except PageNotAnInteger:
        resultado_paginado = paginator.page(1)
    except EmptyPage:
        resultado_paginado = paginator.page(paginator.num_pages)
    categorias = CATEGORIAS_PRODUTO
    VENDEDORES_CHOICES = Pedido.VENDEDORES_CHOICES
    return render(
        request,
        "relatorios/clientes_sem_compras.html",
        {
            "dados": resultado_paginado,
            "inicio": request.GET.get("inicio"),
            "fim": request.GET.get("fim"),
            "categoria": request.GET.get("categoria", ""),
            "categorias": categorias,
            "vendedor": request.GET.get("vendedor", ""),
            "vendedores": VENDEDORES_CHOICES,
            "erro_data": erro_data,
        },
    )


def get_pedidos_dre_filtrados(request):
    from django.utils.dateparse import parse_date

    inicio = request.GET.get("inicio")
    fim = request.GET.get("fim")
    categoria = request.GET.get("categoria", "")
    vendedor = request.GET.get("vendedor", "")
    # pyrefly: ignore  # missing-attribute
    pedidos = Pedido.objects.all().select_related("cliente")
    erro_data = None
    if inicio and fim:
        try:
            data_inicio = parse_date(inicio)
            data_fim = parse_date(fim)
            if data_inicio and data_fim and data_inicio > data_fim:
                erro_data = "Data inicial não pode ser maior que a final."
        except Exception:
            erro_data = "Formato de data inválido."
    if inicio:
        pedidos = pedidos.filter(data__gte=inicio)
    if fim:
        pedidos = pedidos.filter(data__lte=fim)
    if vendedor:
        # Filtra por nome do vendedor
        pedidos = pedidos.filter(vendedor__nome=vendedor)
    if categoria:
        # Filtra por nome da categoria
        pedidos = pedidos.filter(itens__produto__categoria__nome=categoria)
    return pedidos, erro_data


def relatorio_dre(request):
    pedidos, erro_data = get_pedidos_dre_filtrados(request)
    from financeiro.models import Despesa

    # 1. Receita Bruta
    receita_bruta = (
        pedidos.aggregate(total=Sum(F("itens__quantidade") * F("itens__preco_unitario"), output_field=FloatField()))[
            "total"
        ]
        or 0
    )
    # 2. Custos Reais (Custo da Mercadoria Vendida - CMV)
    # pyrefly: ignore  # missing-attribute
    itens_pedidos = ItemPedido.objects.filter(pedido__in=pedidos).select_related("produto", "pedido")
    custos = (
        itens_pedidos.aggregate(total=Sum(F("quantidade") * F("produto__preco_custo"), output_field=FloatField()))[
            "total"
        ]
        or 0
    )
    # 3. Despesas Reais
    from django.utils.dateparse import parse_date

    # pyrefly: ignore  # missing-attribute
    despesas_query = Despesa.objects.filter(status="R")
    inicio = request.GET.get("inicio")
    fim = request.GET.get("fim")
    if inicio:
        despesas_query = despesas_query.filter(data__gte=inicio)
    if fim:
        despesas_query = despesas_query.filter(data__lte=fim)
    despesas = despesas_query.aggregate(total=Sum("valor"))["total"] or 0
    despesas = float(despesas)
    # 4. Cálculos do DRE
    lucro_bruto = receita_bruta - custos
    lucro_operacional = lucro_bruto - despesas
    lucro_liquido = lucro_operacional

    def pct(valor, base):
        try:
            return round(100 * float(valor) / float(base), 2) if base else 0.0
        except Exception:
            return 0.0

    dados = {
        "receita_bruta": receita_bruta,
        "custos": custos,
        "lucro_bruto": lucro_bruto,
        "despesas": despesas,
        "lucro_operacional": lucro_operacional,
        "lucro_liquido": lucro_liquido,
        "pct_custos": pct(custos, receita_bruta),
        "pct_lucro_bruto": pct(lucro_bruto, receita_bruta),
        "pct_despesas": pct(despesas, receita_bruta),
        "pct_lucro_operacional": pct(lucro_operacional, receita_bruta),
    }
    # Evolução mensal para gráfico de barras
    from collections import defaultdict

    from django.db.models.functions import TruncMonth

    dados_mensais = defaultdict(lambda: {"receita": 0, "custo": 0, "despesa": 0})
    receitas_q = (
        pedidos.annotate(mes=TruncMonth("data"))
        .values("mes")
        .annotate(total=Sum(F("itens__quantidade") * F("itens__preco_unitario")))
        .order_by("mes")
    )
    # pyrefly: ignore  # missing-attribute
    custos_q = (
        ItemPedido.objects.filter(pedido__in=pedidos)
        .annotate(mes=TruncMonth("pedido__data"))
        .values("mes")
        .annotate(total=Sum(F("quantidade") * F("produto__preco_custo")))
        .order_by("mes")
    )
    despesas_q = (
        despesas_query.annotate(mes=TruncMonth("data")).values("mes").annotate(total=Sum("valor")).order_by("mes")
    )
    for r in receitas_q:
        # pyrefly: ignore  # bad-argument-type
        if r["mes"]:
            dados_mensais[r["mes"].strftime("%b/%y")]["receita"] = float(r["total"] or 0)
    for c in custos_q:
        # pyrefly: ignore  # bad-argument-type
        if c["mes"]:
            dados_mensais[c["mes"].strftime("%b/%y")]["custo"] = float(c["total"] or 0)
    for d in despesas_q:
        # pyrefly: ignore  # bad-argument-type
        if d["mes"]:
            dados_mensais[d["mes"].strftime("%b/%y")]["despesa"] = float(d["total"] or 0)
    sorted_items = sorted(dados_mensais.items(), key=lambda item: datetime.strptime(item[0], "%b/%y"))
    meses = [item[0] for item in sorted_items]
    receita_mensal = [item[1]["receita"] for item in sorted_items]
    custos_mensal = [item[1]["custo"] for item in sorted_items]
    despesas_mensal = [item[1]["despesa"] for item in sorted_items]
    categorias = CATEGORIAS_PRODUTO
    VENDEDORES_CHOICES = Pedido.VENDEDORES_CHOICES
    return render(
        request,
        "relatorios/dre.html",
        {
            "dados": dados,
            "inicio": request.GET.get("inicio"),
            "fim": request.GET.get("fim"),
            "categoria": request.GET.get("categoria", ""),
            "categorias": categorias,
            "vendedor": request.GET.get("vendedor", ""),
            "vendedores": VENDEDORES_CHOICES,
            "erro_data": erro_data,
            "meses": meses,
            "receita_mensal": receita_mensal,
            "custos_mensal": custos_mensal,
            "despesas_mensal": despesas_mensal,
        },
    )


def get_itens_margem_lucro_filtrados(request):
    from django.utils.dateparse import parse_date

    inicio = request.GET.get("inicio")
    fim = request.GET.get("fim")
    categoria = request.GET.get("categoria", "")
    vendedor = request.GET.get("vendedor", "")
    # pyrefly: ignore  # missing-attribute
    itens = ItemPedido.objects.select_related("produto", "pedido")
    erro_data = None
    if inicio and fim:
        try:
            data_inicio = parse_date(inicio)
            data_fim = parse_date(fim)
            if data_inicio and data_fim and data_inicio > data_fim:
                erro_data = "Data inicial não pode ser maior que a final."
        except Exception:
            erro_data = "Formato de data inválido."
    if inicio:
        itens = itens.filter(pedido__data__gte=inicio)
    if fim:
        itens = itens.filter(pedido__data__lte=fim)
    if vendedor:
        itens = itens.filter(pedido__vendedor__nome=vendedor)
    if categoria:
        itens = itens.filter(produto__categoria__nome=categoria)
    return itens, erro_data


def relatorio_margem_lucro(request):
    itens, erro_data = get_itens_margem_lucro_filtrados(request)
    # Agregações por produto
    dados = (
        itens
        .values(nome_produto=F("produto__descricao"))
        .annotate(
            receita=Sum(F("quantidade") * F("preco_unitario"), output_field=FloatField()),
            custo=Sum(F("quantidade") * F("produto__preco_custo"), output_field=FloatField()),
        )
        .annotate(
            lucro_bruto=ExpressionWrapper(F("receita") - F("custo"), output_field=FloatField()),
            margem=ExpressionWrapper(
                100 * (F("receita") - F("custo")) / F("receita"),
                output_field=FloatField(),
            ),
        )
        .order_by("-margem")
    )
    # Paginação
    from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator

    page = request.GET.get("page", 1)
    paginator = Paginator(list(dados), 30)
    try:
        dados_paginados = paginator.page(page)
    except PageNotAnInteger:
        dados_paginados = paginator.page(1)
    except EmptyPage:
        dados_paginados = paginator.page(paginator.num_pages)
    categorias = CATEGORIAS_PRODUTO
    VENDEDORES_CHOICES = Pedido.VENDEDORES_CHOICES
    return render(
        request,
        "relatorios/margem_lucro.html",
        {
            "dados": dados_paginados,
            "inicio": request.GET.get("inicio"),
            "fim": request.GET.get("fim"),
            "categoria": request.GET.get("categoria", ""),
            "categorias": categorias,
            "vendedor": request.GET.get("vendedor", ""),
            "vendedores": VENDEDORES_CHOICES,
            "erro_data": erro_data,
        },
    )


def get_pedidos_vendas_por_vendedor_filtrados(request):
    from django.utils.dateparse import parse_date

    inicio = request.GET.get("inicio")
    fim = request.GET.get("fim")
    # pyrefly: ignore  # missing-attribute
    pedidos = Pedido.objects.all()
    erro_data = None
    if inicio and fim:
        try:
            data_inicio = parse_date(inicio)
            data_fim = parse_date(fim)
            if data_inicio and data_fim and data_inicio > data_fim:
                erro_data = "Data inicial não pode ser maior que a final."
        except Exception:
            erro_data = "Formato de data inválido."
    if inicio and fim:
        pedidos = pedidos.filter(data__range=[inicio, fim])
    elif inicio:
        pedidos = pedidos.filter(data__gte=inicio)
    elif fim:
        pedidos = pedidos.filter(data__lte=fim)
    return pedidos, erro_data


def relatorio_vendas_por_vendedor(request):
    pedidos, erro_data = get_pedidos_vendas_por_vendedor_filtrados(request)
    # Excluir pedidos cancelados
    pedidos = pedidos.exclude(status="C")
    meta = 10000  # Meta fixa para exemplo
    # Agrupamento eficiente por vendedor
    dados_vendedor = (
        pedidos.values("vendedor")
        .annotate(total_vendido=Sum(F("itens__quantidade") * F("itens__preco_unitario")), num_pedidos=Count("id"))
        .order_by("-total_vendido")
    )
    # Buscar nomes dos vendedores por ID
    # pyrefly: ignore  # missing-attribute
    vendedores_map = {v.id: v for v in Vendedor.objects.all()}
    resultado = []
    for item in dados_vendedor:
        vendedor_id = item["vendedor"]
        vendedor_obj = vendedores_map.get(vendedor_id)
        vendedor_nome = vendedor_obj.nome if vendedor_obj else "Desconhecido"
        comissao_percentual = vendedor_obj.comissao_percentual if vendedor_obj else 0
        # Comissão só sobre produtos vendidos (total_vendido - taxa_entrega)
        pedidos_vendedor = pedidos.filter(vendedor_id=vendedor_id)
        total_taxa_entrega = pedidos_vendedor.aggregate(total=Sum("taxa_entrega"))["total"] or 0
        base_comissao = (item["total_vendido"] or 0) - total_taxa_entrega
        resultado.append(
            {
                "vendedor": vendedor_nome,
                "total_vendido": item["total_vendido"] or 0,
                "num_pedidos": item["num_pedidos"],
                "ticket_medio": (item["total_vendido"] / item["num_pedidos"]) if item["num_pedidos"] else 0,
                "meta_atingida": (
                    (Decimal(item["total_vendido"]) * Decimal("100") / Decimal(str(meta)))
                    if meta and item["total_vendido"]
                    else 0
                ),
                "comissao_percentual": comissao_percentual,
                "valor_comissao": (
                    round(Decimal(base_comissao) * (comissao_percentual / Decimal("100")), 2)
                    if comissao_percentual
                    else 0
                ),
            }
        )
    # Paginação
    from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator

    page = request.GET.get("page", 1)
    paginator = Paginator(resultado, 30)
    try:
        resultado_paginado = paginator.page(page)
    except PageNotAnInteger:
        resultado_paginado = paginator.page(1)
    except EmptyPage:
        resultado_paginado = paginator.page(paginator.num_pages)
    return render(
        request,
        "relatorios/vendas_por_vendedor.html",
        {
            "dados": resultado_paginado,
            "inicio": request.GET.get("inicio"),
            "fim": request.GET.get("fim"),
            "meta": meta,
            "erro_data": erro_data,
        },
    )


def relatorio_abc_clientes_export(request):
    # Mesma lógica do relatorio_abc_clientes
    inicio = request.GET.get("inicio")
    fim = request.GET.get("fim")
    # pyrefly: ignore  # missing-attribute
    pedidos = Pedido.objects.all()
    if inicio:
        pedidos = pedidos.filter(data__gte=inicio)
    if fim:
        pedidos = pedidos.filter(data__lte=fim)
    dados = (
        pedidos.values("cliente__nome")
        .annotate(total=Sum(F("itens__quantidade") * F("itens__preco_unitario"), output_field=FloatField()))
        .order_by("-total")
    )
    total_geral = sum([d["total"] for d in dados]) or 1
    acumulado = 0
    resultado = []
    for d in dados:
        percentual = (d["total"] / total_geral) * 100
        acumulado += percentual
        if acumulado <= 80:
            grupo = "A"
        elif acumulado <= 95:
            grupo = "B"
        else:
            grupo = "C"
        resultado.append(
            {
                "Cliente": d["cliente__nome"],
                "Total Comprado": d["total"],
                "% Individual": percentual,
                "% Acumulado": acumulado,
                "Grupo": grupo,
            }
        )
    df = pd.DataFrame(resultado)
    response = HttpResponse(content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    response["Content-Disposition"] = "attachment; filename=relatorio_curva_abc.xlsx"
    df.to_excel(response, index=False)
    return response


def relatorio_clientes_sem_compras_export(request):
    # Mesma lógica do relatorio_clientes_sem_compras
    inicio = request.GET.get("inicio")
    fim = request.GET.get("fim")
    # pyrefly: ignore  # missing-attribute
    clientes = Cliente.objects.all()
    # pyrefly: ignore  # missing-attribute
    pedidos = Pedido.objects.all()
    if inicio:
        pedidos = pedidos.filter(data__gte=inicio)
    if fim:
        pedidos = pedidos.filter(data__lte=fim)
    clientes_com_pedido = pedidos.values_list("cliente_id", flat=True).distinct()
    clientes_sem_compras = clientes.exclude(id__in=clientes_com_pedido)
    resultado = []
    for cliente in clientes_sem_compras:
        # pyrefly: ignore  # missing-attribute
        ultimo_pedido = Pedido.objects.filter(cliente=cliente).order_by("-data").first()
        resultado.append(
            {
                "Nome": cliente.nome,
                "Contato": cliente.email or cliente.telefone,
                "Última Compra": (
                    ultimo_pedido.data.strftime("%d/%m/%Y") if ultimo_pedido and ultimo_pedido.data else ""
                ),
                "Vendedor": ultimo_pedido.vendedor.nome if ultimo_pedido and ultimo_pedido.vendedor else "",
            }
        )
    df = pd.DataFrame(resultado)
    response = HttpResponse(content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    response["Content-Disposition"] = "attachment; filename=clientes_sem_compras.xlsx"
    df.to_excel(response, index=False)
    return response


def relatorio_dre_export(request):
    # Mesma lógica do relatorio_dre
    inicio = request.GET.get("inicio")
    fim = request.GET.get("fim")
    # pyrefly: ignore  # missing-attribute
    pedidos = Pedido.objects.all()
    if inicio:
        pedidos = pedidos.filter(data__gte=inicio)
    if fim:
        pedidos = pedidos.filter(data__lte=fim)
    receita_bruta = (
        pedidos.aggregate(total=Sum(F("itens__quantidade") * F("itens__preco_unitario"), output_field=FloatField()))[
            "total"
        ]
        or 0
    )
    custos = receita_bruta * 0.5
    despesas = receita_bruta * 0.2
    lucro_operacional = receita_bruta - custos - despesas
    lucro_liquido = lucro_operacional
    dados = [
        {
            "Receita Bruta": receita_bruta,
            "Custos": custos,
            "Despesas": despesas,
            "Lucro Operacional": lucro_operacional,
            "Lucro Líquido": lucro_liquido,
        }
    ]
    df = pd.DataFrame(dados)
    response = HttpResponse(content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    response["Content-Disposition"] = "attachment; filename=dre.xlsx"
    df.to_excel(response, index=False)
    return response


def relatorio_margem_lucro_export(request):
    # Mesma lógica do relatorio_margem_lucro
    inicio = request.GET.get("inicio")
    fim = request.GET.get("fim")
    # pyrefly: ignore  # missing-attribute
    itens = ItemPedido.objects.select_related("produto", "pedido")
    if inicio:
        itens = itens.filter(pedido__data__gte=inicio)
    if fim:
        itens = itens.filter(pedido__data__lte=fim)
    receita = Sum(F("quantidade") * F("preco_unitario"), output_field=FloatField())
    custo = Sum(F("quantidade") * (F("preco_unitario") * 0.6), output_field=FloatField())
    dados = (
        itens.values("produto__descricao")
        .annotate(
            receita=receita,
            custo=custo,
            lucro_bruto=ExpressionWrapper(receita - custo, output_field=FloatField()),
            margem=ExpressionWrapper(100 * (receita - custo) / receita, output_field=FloatField()),
        )
        .order_by("-receita")
    )
    resultado = []
    for d in dados:
        resultado.append(
            {
                "Produto": d["produto__descricao"],
                "Receita": d["receita"] or 0,
                "Custo": d["custo"] or 0,
                "Lucro Bruto": d["lucro_bruto"] or 0,
                "Margem (%)": d["margem"] or 0,
            }
        )
    df = pd.DataFrame(resultado)
    response = HttpResponse(content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    response["Content-Disposition"] = "attachment; filename=margem_lucro.xlsx"
    df.to_excel(response, index=False)
    return response


def relatorio_vendas_por_vendedor_export(request):
    # Mesma lógica do relatorio_vendas_por_vendedor
    inicio = request.GET.get("inicio")
    fim = request.GET.get("fim")
    # pyrefly: ignore  # missing-attribute
    pedidos = Pedido.objects.all()
    if inicio:
        pedidos = pedidos.filter(data__gte=inicio)
    if fim:
        pedidos = pedidos.filter(data__lte=fim)
    meta = 10000  # Meta fixa para exemplo
    vendedores_dict = {}
    for pedido in pedidos:
        vendedor = pedido.vendedor or "Não informado"
        if vendedor not in vendedores_dict:
            vendedores_dict[vendedor] = {"total_vendido": 0, "num_pedidos": 0}
        vendedores_dict[vendedor]["total_vendido"] += pedido.total
        vendedores_dict[vendedor]["num_pedidos"] += 1
    resultado = []
    for vendedor, dados in vendedores_dict.items():
        ticket_medio = dados["total_vendido"] / dados["num_pedidos"] if dados["num_pedidos"] else 0
        meta_atingida = 100 * dados["total_vendido"] / meta if meta else 0
        vendedor_nome = dict(Pedido.VENDEDORES_CHOICES).get(vendedor, vendedor)
        resultado.append(
            {
                "Vendedor": vendedor_nome or "Não informado",
                "Total Vendido": dados["total_vendido"],
                "Nº Pedidos": dados["num_pedidos"],
                "Ticket Médio": ticket_medio,
                "Meta Atingida (%)": meta_atingida,
            }
        )
    # Busca vendedor e comissão
    # pyrefly: ignore  # missing-attribute
    vendedores_map = {v.nome: v for v in Vendedor.objects.all()}
    for item in resultado:
        vendedor_nome = item["vendedor"]
        vendedor_obj = vendedores_map.get(vendedor_nome)
        comissao_percentual = vendedor_obj.comissao_percentual if vendedor_obj else 0
        # Comissão só sobre produtos vendidos (total_vendido - taxa_entrega)
        pedidos_vendedor = pedidos.filter(vendedor=vendedor_nome)
        total_taxa_entrega = pedidos_vendedor.aggregate(total=Sum("taxa_entrega"))["total"] or 0
        base_comissao = (item["total_vendido"] or 0) - total_taxa_entrega
        item["comissao_percentual"] = comissao_percentual
        item["valor_comissao"] = (
            round(base_comissao * (float(comissao_percentual) / 100), 2) if comissao_percentual else 0
        )
    resultado = sorted(resultado, key=lambda x: x["Total Vendido"], reverse=True)
    df = pd.DataFrame(resultado)
    response = HttpResponse(content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    response["Content-Disposition"] = "attachment; filename=vendas_por_vendedor.xlsx"
    df.to_excel(response, index=False)
    return response
