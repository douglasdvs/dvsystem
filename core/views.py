# core/views.py
from django.shortcuts import render
from django.db.models import Sum, F, FloatField
from datetime import datetime, timedelta
from clientes.models import Cliente
from produtos.models import Produto
from financeiro.models import Despesa
from pedidos.models import ItemPedido, Pedido
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.contrib.auth import login
from django.shortcuts import redirect
from decimal import Decimal
from .forms import CustomUserCreationForm
import logging

logger = logging.getLogger(__name__)

def custom_logout(request):
    if request.method == 'POST':
        logout(request)
        return redirect('login')
    return redirect('dashboard')  # Se alguém tentar acessar direto

def index(request):
    return render(request, 'core/index.html')

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            try:
                user = form.save()
                login(request, user)
                messages.success(request, 'Conta criada com sucesso! Bem-vindo ao sistema.')
                logger.info(f'Novo usuário registrado: {user.username}')
                return redirect('core:dashboard')
            except Exception as e:
                logger.error(f'Erro ao criar usuário: {str(e)}')
                messages.error(request, 'Erro ao criar conta. Por favor, tente novamente.')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'registration/register.html', {'form': form})

def dashboard(request):
    hoje = datetime.today().date()
    trinta_cinco_dias = hoje - timedelta(days=35)
    sesenta_dias = hoje - timedelta(days=60)
    cento_vinte_dias = hoje - timedelta(days=120)
    um_ano = hoje - timedelta(days=365)
    
    # Totais financeiros
    total_receitas = (Pedido.objects
        .filter(data__gte=sesenta_dias, status__in=['P','C','E'])
        .aggregate(total=Sum(F('itens__preco_unitario') * F('itens__quantidade'), output_field=FloatField()))['total']) or 0.0
    total_despesas_dec = (Despesa.objects
        .filter(data__gte=sesenta_dias)
        .aggregate(total=Sum('valor'))['total']) or 0
    total_despesas = float(total_despesas_dec)
    diferenca = total_receitas - total_despesas
    
    # Indicadores de alerta
    alerta_prejuizo = diferenca < 0
    
    # 1. Top 10 clientes com maior frequência de pedidos
    from django.db.models import Count
    top_clientes_frequencia = (Cliente.objects
        .filter(pedido__data__gte=um_ano)
        .annotate(frequencia=Count('pedido'))
        .order_by('-frequencia')[:10])
    clientes_frequentes = []
    for cliente in top_clientes_frequencia:
        clientes_frequentes.append({
            'id': cliente.id,
            'nome': cliente.nome,
            'frequencia': cliente.frequencia,
            'telefone': cliente.telefone
        })
    
    # 2. Top 10 clientes sem pedidos há mais de 35 dias
    clientes_sem_pedidos = []
    clientes_com_pedidos = set(Pedido.objects.filter(data__gte=trinta_cinco_dias).values_list('cliente_id', flat=True))
    clientes_inativos = Cliente.objects.filter(
        pedido__data__lte=trinta_cinco_dias
    ).exclude(
        id__in=clientes_com_pedidos
    ).distinct()
    
    # Ordenar por data do último pedido
    from django.db.models import Max
    clientes_inativos = (clientes_inativos
        .annotate(ultimo_pedido=Max('pedido__data'))
        .order_by('ultimo_pedido')[:10])
    
    for cliente in clientes_inativos:
        dias_sem_pedido = (hoje - cliente.ultimo_pedido).days if cliente.ultimo_pedido else 0
        clientes_sem_pedidos.append({
            'id': cliente.id,
            'nome': cliente.nome,
            'ultimo_pedido': cliente.ultimo_pedido,
            'dias_sem_pedido': dias_sem_pedido,
            'telefone': cliente.telefone
        })
    
    # 3. Top 10 produtos mais vendidos (com valor e quantidade)
    top_produtos_vendidos = (Produto.objects
        .filter(itempedido__pedido__data__gte=um_ano)
        .annotate(
            qtd_total=Sum('itempedido__quantidade'),
            valor_total=Sum(F('itempedido__quantidade') * F('itempedido__preco_unitario'), output_field=FloatField())
        )
        .order_by('-qtd_total')[:10])
    
    produtos_mais_vendidos = []
    max_qtd = top_produtos_vendidos[0].qtd_total if top_produtos_vendidos else 0
    
    for produto in top_produtos_vendidos:
        produtos_mais_vendidos.append({
            'id': produto.id,
            'descricao': produto.descricao,
            'quantidade': produto.qtd_total,
            'valor_total': float(produto.valor_total or 0),
            'porcentagem': int((produto.qtd_total / max_qtd * 100) if max_qtd else 0),
            'estoque_atual': produto.estoque
        })
    
    # 4. Dados financeiros para gráficos
    # Dados dos últimos 12 meses
    import calendar
    from datetime import date
    from collections import defaultdict
    
    # Receitas por mês
    dados_financeiros = {}
    for i in range(12):
        mes_atual = hoje.replace(day=1) - timedelta(days=i*30)
        primeiro_dia = mes_atual.replace(day=1)
        if mes_atual.month == 12:
            ultimo_dia = mes_atual.replace(year=mes_atual.year+1, month=1, day=1) - timedelta(days=1)
        else:
            ultimo_dia = mes_atual.replace(month=mes_atual.month+1, day=1) - timedelta(days=1)
            
        # Nome do mês no formato "Jan/2023"
        nome_mes = f"{calendar.month_abbr[mes_atual.month]}/{mes_atual.year}"
        
        # Receitas (valor total dos pedidos)
        receitas = Pedido.objects.filter(
            data__gte=primeiro_dia,
            data__lte=ultimo_dia,
            status__in=['P', 'C', 'E']
        ).aggregate(
            total=Sum(F('itens__preco_unitario') * F('itens__quantidade'), output_field=FloatField())
        )['total'] or 0
        
        # Despesas
        despesas = Despesa.objects.filter(
            data__gte=primeiro_dia,
            data__lte=ultimo_dia
        ).aggregate(total=Sum('valor'))['total'] or 0
        
        float_receitas = float(receitas)
        float_despesas = float(despesas)
        dados_financeiros[nome_mes] = {
         'receitas': float_receitas,
         'despesas': float_despesas,
          'lucro': float_receitas - float_despesas
}
    
    # Ordenar por data (mais antigo para mais recente)
    from collections import OrderedDict
    dados_financeiros_ordenados = OrderedDict(sorted(dados_financeiros.items(), 
                                                  key=lambda x: datetime.strptime(x[0], "%b/%Y")))
    
    # Converter para listas para uso no gráfico
    labels_meses = list(dados_financeiros_ordenados.keys())
    receitas_mensais = [dados['receitas'] for dados in dados_financeiros_ordenados.values()]
    despesas_mensais = [dados['despesas'] for dados in dados_financeiros_ordenados.values()]
    lucro_mensal = [dados['lucro'] for dados in dados_financeiros_ordenados.values()]
    
    # Top 10 clientes por valor (mantido do código original)
    top_clientes_valor = (Cliente.objects
        .filter(pedido__data__gte=sesenta_dias)
        .annotate(total=Sum(F('pedido__itens__preco_unitario') * F('pedido__itens__quantidade'), output_field=FloatField()))
        .order_by('-total')[:10])
    
    top_clientes = []
    max_cliente = top_clientes_valor[0].total if top_clientes_valor else 0
    
    for cliente in top_clientes_valor:
        top_clientes.append({
            'id': cliente.id,
            'nome': cliente.nome,
            'total': float(cliente.total or 0),
            'porcentagem': int((cliente.total / max_cliente * 100) if max_cliente else 0),
            'telefone': cliente.telefone
        })

    return render(request, 'core/dashboard.html', {
        # Dados financeiros
        'total_receitas': total_receitas,
        'total_despesas': total_despesas,
        'diferenca': diferenca,
        'alerta_prejuizo': alerta_prejuizo,
        
        # Top clientes e produtos
        'top_clientes_valor': top_clientes,
        'clientes_frequentes': clientes_frequentes,
        'clientes_inativos': clientes_sem_pedidos,
        'produtos_mais_vendidos': produtos_mais_vendidos,
        
        # Dados para gráficos
        'labels_meses': labels_meses,
        'receitas_mensais': receitas_mensais,
        'despesas_mensais': despesas_mensais,
        'lucro_mensal': lucro_mensal,
    })
