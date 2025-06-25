from django.shortcuts import render
from django.db.models import Sum, Max, F, FloatField, ExpressionWrapper, Count
from pedidos.models import Pedido, Cliente, ItemPedido
from datetime import datetime
import pandas as pd
from django.http import HttpResponse
from produtos.models import Produto, CATEGORIAS_PRODUTO
from clientes.models import Cliente

def index(request):
    total_clientes = Cliente.objects.count()
    total_pedidos = Pedido.objects.count()
    total_vendido = sum(p.total for p in Pedido.objects.all())
    total_produtos = Produto.objects.count()
    total_vendedores = len(Pedido.VENDEDORES_CHOICES)
    return render(request, 'relatorios/index.html', {
        'total_clientes': total_clientes,
        'total_pedidos': total_pedidos,
        'total_vendido': total_vendido,
        'total_produtos': total_produtos,
        'total_vendedores': total_vendedores,
    })

def relatorio_abc_clientes(request):
    # Filtros de período, categoria e vendedor
    from django.utils.dateparse import parse_date
    inicio = request.GET.get('inicio')
    fim = request.GET.get('fim')
    categoria = request.GET.get('categoria', '')
    vendedor = request.GET.get('vendedor', '')
    erro_data = None
    # Validação de datas
    if inicio and fim:
        try:
            data_inicio = parse_date(inicio)
            data_fim = parse_date(fim)
            if data_inicio and data_fim and data_inicio > data_fim:
                erro_data = 'Data inicial não pode ser maior que a final.'
        except Exception:
            erro_data = 'Formato de data inválido.'
    pedidos = Pedido.objects.all()
    if inicio:
        pedidos = pedidos.filter(data__gte=inicio)
    if fim:
        pedidos = pedidos.filter(data__lte=fim)
    if vendedor:
        pedidos = pedidos.filter(vendedor=vendedor)
    if categoria:
        pedidos = pedidos.filter(itens__produto__categoria=categoria)
    # Soma total por cliente
    dados = (
        pedidos.values('cliente__nome')
        .annotate(total=Sum(F('itens__quantidade') * F('itens__preco_unitario'), output_field=FloatField()))
        .order_by('-total')
    )
    total_geral = sum([d['total'] for d in dados]) or 1
    acumulado = 0
    resultado = []
    for d in dados:
        percentual = (d['total'] / total_geral) * 100
        acumulado += percentual
        if acumulado <= 80:
            grupo = 'A'
        elif acumulado <= 95:
            grupo = 'B'
        else:
            grupo = 'C'
        resultado.append({
            'cliente': d['cliente__nome'],
            'total': d['total'],
            'percentual': percentual,
            'acumulado': acumulado,
            'grupo': grupo
        })
    # Opções de filtros
    categorias = CATEGORIAS_PRODUTO
    VENDEDORES_CHOICES = Pedido.VENDEDORES_CHOICES
    return render(request, 'relatorios/abc_clientes.html', {
        'dados': resultado,
        'inicio': inicio,
        'fim': fim,
        'categoria': categoria,
        'categorias': categorias,
        'vendedor': vendedor,
        'vendedores': VENDEDORES_CHOICES,
        'erro_data': erro_data
    })

def relatorio_clientes_sem_compras(request):
    # Filtros de período, categoria e vendedor
    from django.utils.dateparse import parse_date
    inicio = request.GET.get('inicio')
    fim = request.GET.get('fim')
    categoria = request.GET.get('categoria', '')
    vendedor = request.GET.get('vendedor', '')
    erro_data = None
    # Validação de datas
    if inicio and fim:
        try:
            data_inicio = parse_date(inicio)
            data_fim = parse_date(fim)
            if data_inicio and data_fim and data_inicio > data_fim:
                erro_data = 'Data inicial não pode ser maior que a final.'
        except Exception:
            erro_data = 'Formato de data inválido.'
    clientes = Cliente.objects.all()
    pedidos = Pedido.objects.all()
    if inicio:
        pedidos = pedidos.filter(data__gte=inicio)
    if fim:
        pedidos = pedidos.filter(data__lte=fim)
    if vendedor:
        pedidos = pedidos.filter(vendedor=vendedor)
    if categoria:
        pedidos = pedidos.filter(itens__produto__categoria=categoria)
    clientes_com_pedido = pedidos.values_list('cliente_id', flat=True).distinct()
    clientes_sem_compras = clientes.exclude(id__in=clientes_com_pedido)
    resultado = []
    for cliente in clientes_sem_compras:
        ultimo_pedido = Pedido.objects.filter(cliente=cliente).order_by('-data').first()
        resultado.append({
            'nome': cliente.nome,
            'contato': cliente.email or cliente.telefone,
            'ultima_compra': ultimo_pedido.data if ultimo_pedido else None,
            'vendedor': ultimo_pedido.vendedor if ultimo_pedido else '',
        })
    categorias = CATEGORIAS_PRODUTO
    VENDEDORES_CHOICES = Pedido.VENDEDORES_CHOICES
    return render(request, 'relatorios/clientes_sem_compras.html', {
        'dados': resultado,
        'inicio': inicio,
        'fim': fim,
        'categoria': categoria,
        'categorias': categorias,
        'vendedor': vendedor,
        'vendedores': VENDEDORES_CHOICES,
        'erro_data': erro_data
    })

def relatorio_dre(request):
    # Filtros de período, categoria e vendedor
    from django.utils.dateparse import parse_date
    inicio = request.GET.get('inicio')
    fim = request.GET.get('fim')
    categoria = request.GET.get('categoria', '')
    vendedor = request.GET.get('vendedor', '')
    erro_data = None
    # Validação de datas
    if inicio and fim:
        try:
            data_inicio = parse_date(inicio)
            data_fim = parse_date(fim)
            if data_inicio and data_fim and data_inicio > data_fim:
                erro_data = 'Data inicial não pode ser maior que a final.'
        except Exception:
            erro_data = 'Formato de data inválido.'
    pedidos = Pedido.objects.all()
    if inicio:
        pedidos = pedidos.filter(data__gte=inicio)
    if fim:
        pedidos = pedidos.filter(data__lte=fim)
    if vendedor:
        pedidos = pedidos.filter(vendedor=vendedor)
    if categoria:
        pedidos = pedidos.filter(itens__produto__categoria=categoria)
    receita_bruta = pedidos.aggregate(total=Sum(F('itens__quantidade') * F('itens__preco_unitario'), output_field=FloatField()))['total'] or 0
    custos = receita_bruta * 0.5  # Exemplo: 50% do faturamento
    despesas = receita_bruta * 0.2  # Exemplo: 20% do faturamento
    lucro_operacional = receita_bruta - custos - despesas
    lucro_liquido = lucro_operacional
    dados = {
        'receita_bruta': receita_bruta,
        'custos': custos,
        'despesas': despesas,
        'lucro_operacional': lucro_operacional,
        'lucro_liquido': lucro_liquido,
    }
    categorias = CATEGORIAS_PRODUTO
    VENDEDORES_CHOICES = Pedido.VENDEDORES_CHOICES
    return render(request, 'relatorios/dre.html', {
        'dados': dados,
        'inicio': inicio,
        'fim': fim,
        'categoria': categoria,
        'categorias': categorias,
        'vendedor': vendedor,
        'vendedores': VENDEDORES_CHOICES,
        'erro_data': erro_data
    })

def relatorio_margem_lucro(request):
    # Filtros de período, categoria e vendedor
    from django.utils.dateparse import parse_date
    inicio = request.GET.get('inicio')
    fim = request.GET.get('fim')
    categoria = request.GET.get('categoria', '')
    vendedor = request.GET.get('vendedor', '')
    erro_data = None
    # Validação de datas
    if inicio and fim:
        try:
            data_inicio = parse_date(inicio)
            data_fim = parse_date(fim)
            if data_inicio and data_fim and data_inicio > data_fim:
                erro_data = 'Data inicial não pode ser maior que a final.'
        except Exception:
            erro_data = 'Formato de data inválido.'
    itens = ItemPedido.objects.select_related('produto', 'pedido')
    if inicio:
        itens = itens.filter(pedido__data__gte=inicio)
    if fim:
        itens = itens.filter(pedido__data__lte=fim)
    if vendedor:
        itens = itens.filter(pedido__vendedor=vendedor)
    if categoria:
        itens = itens.filter(produto__categoria=categoria)
    receita = Sum(F('quantidade') * F('preco_unitario'), output_field=FloatField())
    custo = Sum(F('quantidade') * (F('preco_unitario') * 0.6), output_field=FloatField())
    dados = (
        itens.values('produto__descricao')
        .annotate(
            receita=receita,
            custo=custo,
            lucro_bruto=ExpressionWrapper(
                receita - custo, output_field=FloatField()
            ),
            margem=ExpressionWrapper(
                100 * (receita - custo) / receita, output_field=FloatField()
            )
        )
        .order_by('-receita')
    )
    resultado = []
    for d in dados:
        resultado.append({
            'produto': d['produto__descricao'],
            'receita': d['receita'] or 0,
            'custo': d['custo'] or 0,
            'lucro_bruto': d['lucro_bruto'] or 0,
            'margem': d['margem'] or 0,
        })
    categorias = CATEGORIAS_PRODUTO
    VENDEDORES_CHOICES = Pedido.VENDEDORES_CHOICES
    return render(request, 'relatorios/margem_lucro.html', {
        'dados': resultado,
        'inicio': inicio,
        'fim': fim,
        'categoria': categoria,
        'categorias': categorias,
        'vendedor': vendedor,
        'vendedores': VENDEDORES_CHOICES,
        'erro_data': erro_data
    })

def relatorio_vendas_por_vendedor(request):
    # Filtros de período
    from django.core.exceptions import ValidationError
    from django.utils.dateparse import parse_date
    inicio = request.GET.get('inicio')
    fim = request.GET.get('fim')
    meta = 10000  # Meta fixa para exemplo
    erro_data = None
    # Validação de datas
    if inicio and fim:
        try:
            data_inicio = parse_date(inicio)
            data_fim = parse_date(fim)
            if data_inicio and data_fim and data_inicio > data_fim:
                erro_data = 'Data inicial não pode ser maior que a final.'
        except Exception:
            erro_data = 'Formato de data inválido.'
    pedidos = Pedido.objects.all()
    if inicio:
        pedidos = pedidos.filter(data__gte=inicio)
    if fim:
        pedidos = pedidos.filter(data__lte=fim)
    # Agrupamento eficiente por vendedor
    dados = (
        pedidos.values('vendedor')
        .annotate(
            total_vendido=Sum('total'),
            num_pedidos=Count('id'),
        )
        .order_by('-total_vendido')
    )
    resultado = []
    for d in dados:
        ticket_medio = d['total_vendido'] / d['num_pedidos'] if d['num_pedidos'] else 0
        meta_atingida = 100 * d['total_vendido'] / meta if meta else 0
        vendedor_nome = dict(Pedido.VENDEDORES_CHOICES).get(d['vendedor'], d['vendedor'])
        resultado.append({
            'vendedor': vendedor_nome or 'Não informado',
            'total_vendido': d['total_vendido'],
            'num_pedidos': d['num_pedidos'],
            'ticket_medio': ticket_medio,
            'meta_atingida': meta_atingida,
        })
    return render(request, 'relatorios/vendas_por_vendedor.html', {
        'dados': resultado,
        'inicio': inicio,
        'fim': fim,
        'meta': meta,
        'erro_data': erro_data
    })

def relatorio_abc_clientes_export(request):
    # Mesma lógica do relatorio_abc_clientes
    inicio = request.GET.get('inicio')
    fim = request.GET.get('fim')
    pedidos = Pedido.objects.all()
    if inicio:
        pedidos = pedidos.filter(data__gte=inicio)
    if fim:
        pedidos = pedidos.filter(data__lte=fim)
    dados = (
        pedidos.values('cliente__nome')
        .annotate(total=Sum(F('itens__quantidade') * F('itens__preco_unitario'), output_field=FloatField()))
        .order_by('-total')
    )
    total_geral = sum([d['total'] for d in dados]) or 1
    acumulado = 0
    resultado = []
    for d in dados:
        percentual = (d['total'] / total_geral) * 100
        acumulado += percentual
        if acumulado <= 80:
            grupo = 'A'
        elif acumulado <= 95:
            grupo = 'B'
        else:
            grupo = 'C'
        resultado.append({
            'Cliente': d['cliente__nome'],
            'Total Comprado': d['total'],
            '% Individual': percentual,
            '% Acumulado': acumulado,
            'Grupo': grupo
        })
    df = pd.DataFrame(resultado)
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=relatorio_curva_abc.xlsx'
    df.to_excel(response, index=False)
    return response

def relatorio_clientes_sem_compras_export(request):
    # Mesma lógica do relatorio_clientes_sem_compras
    inicio = request.GET.get('inicio')
    fim = request.GET.get('fim')
    clientes = Cliente.objects.all()
    pedidos = Pedido.objects.all()
    if inicio:
        pedidos = pedidos.filter(data__gte=inicio)
    if fim:
        pedidos = pedidos.filter(data__lte=fim)
    clientes_com_pedido = pedidos.values_list('cliente_id', flat=True).distinct()
    clientes_sem_compras = clientes.exclude(id__in=clientes_com_pedido)
    resultado = []
    for cliente in clientes_sem_compras:
        ultimo_pedido = Pedido.objects.filter(cliente=cliente).order_by('-data').first()
        resultado.append({
            'Nome': cliente.nome,
            'Contato': cliente.email or cliente.telefone,
            'Última Compra': ultimo_pedido.data.strftime('%d/%m/%Y') if ultimo_pedido and ultimo_pedido.data else '',
            'Vendedor': ultimo_pedido.vendedor.nome if ultimo_pedido and ultimo_pedido.vendedor else '',
        })
    df = pd.DataFrame(resultado)
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=clientes_sem_compras.xlsx'
    df.to_excel(response, index=False)
    return response

def relatorio_dre_export(request):
    # Mesma lógica do relatorio_dre
    inicio = request.GET.get('inicio')
    fim = request.GET.get('fim')
    pedidos = Pedido.objects.all()
    if inicio:
        pedidos = pedidos.filter(data__gte=inicio)
    if fim:
        pedidos = pedidos.filter(data__lte=fim)
    receita_bruta = pedidos.aggregate(total=Sum(F('itens__quantidade') * F('itens__preco_unitario'), output_field=FloatField()))['total'] or 0
    custos = receita_bruta * 0.5
    despesas = receita_bruta * 0.2
    lucro_operacional = receita_bruta - custos - despesas
    lucro_liquido = lucro_operacional
    dados = [{
        'Receita Bruta': receita_bruta,
        'Custos': custos,
        'Despesas': despesas,
        'Lucro Operacional': lucro_operacional,
        'Lucro Líquido': lucro_liquido,
    }]
    df = pd.DataFrame(dados)
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=dre.xlsx'
    df.to_excel(response, index=False)
    return response

def relatorio_margem_lucro_export(request):
    # Mesma lógica do relatorio_margem_lucro
    inicio = request.GET.get('inicio')
    fim = request.GET.get('fim')
    itens = ItemPedido.objects.select_related('produto', 'pedido')
    if inicio:
        itens = itens.filter(pedido__data__gte=inicio)
    if fim:
        itens = itens.filter(pedido__data__lte=fim)
    receita = Sum(F('quantidade') * F('preco_unitario'), output_field=FloatField())
    custo = Sum(F('quantidade') * (F('preco_unitario') * 0.6), output_field=FloatField())
    dados = (
        itens.values('produto__descricao')
        .annotate(
            receita=receita,
            custo=custo,
            lucro_bruto=ExpressionWrapper(
                receita - custo, output_field=FloatField()
            ),
            margem=ExpressionWrapper(
                100 * (receita - custo) / receita, output_field=FloatField()
            )
        )
        .order_by('-receita')
    )
    resultado = []
    for d in dados:
        resultado.append({
            'Produto': d['produto__descricao'],
            'Receita': d['receita'] or 0,
            'Custo': d['custo'] or 0,
            'Lucro Bruto': d['lucro_bruto'] or 0,
            'Margem (%)': d['margem'] or 0,
        })
    df = pd.DataFrame(resultado)
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=margem_lucro.xlsx'
    df.to_excel(response, index=False)
    return response

def relatorio_vendas_por_vendedor_export(request):
    # Mesma lógica do relatorio_vendas_por_vendedor
    inicio = request.GET.get('inicio')
    fim = request.GET.get('fim')
    pedidos = Pedido.objects.all()
    if inicio:
        pedidos = pedidos.filter(data__gte=inicio)
    if fim:
        pedidos = pedidos.filter(data__lte=fim)
    meta = 10000  # Meta fixa para exemplo
    vendedores_dict = {}
    for pedido in pedidos:
        vendedor = pedido.vendedor or 'Não informado'
        if vendedor not in vendedores_dict:
            vendedores_dict[vendedor] = {
                'total_vendido': 0,
                'num_pedidos': 0
            }
        vendedores_dict[vendedor]['total_vendido'] += pedido.total
        vendedores_dict[vendedor]['num_pedidos'] += 1
    resultado = []
    for vendedor, dados in vendedores_dict.items():
        ticket_medio = dados['total_vendido'] / dados['num_pedidos'] if dados['num_pedidos'] else 0
        meta_atingida = 100 * dados['total_vendido'] / meta if meta else 0
        vendedor_nome = dict(Pedido.VENDEDORES_CHOICES).get(vendedor, vendedor)
        resultado.append({
            'Vendedor': vendedor_nome or 'Não informado',
            'Total Vendido': dados['total_vendido'],
            'Nº Pedidos': dados['num_pedidos'],
            'Ticket Médio': ticket_medio,
            'Meta Atingida (%)': meta_atingida,
        })
    resultado = sorted(resultado, key=lambda x: x['Total Vendido'], reverse=True)
    df = pd.DataFrame(resultado)
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=vendas_por_vendedor.xlsx'
    df.to_excel(response, index=False)
    return response
