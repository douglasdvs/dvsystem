from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Sum, Count, Q
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.utils import timezone
from datetime import datetime, timedelta
from .models import Receita, Despesa, CentroCusto, FluxoCaixa
from .forms import ReceitaForm, DespesaForm, CentroCustoForm, RelatorioForm
from pedidos.models import Pedido
from django.contrib.auth.decorators import login_required
import json

# =======================
# Dashboard Principal
# =======================

@login_required
def dashboard(request):
    # Filtros de data
    hoje = timezone.now().date()
    inicio_mes = hoje.replace(day=1)
    fim_mes = (inicio_mes + timedelta(days=32)).replace(day=1) - timedelta(days=1)
    
    data_inicio = request.GET.get('data_inicio', inicio_mes)
    data_fim = request.GET.get('data_fim', fim_mes)
    # Validação de datas
    try:
        if isinstance(data_inicio, str):
            data_inicio = datetime.strptime(data_inicio, '%Y-%m-%d').date()
        if isinstance(data_fim, str):
            data_fim = datetime.strptime(data_fim, '%Y-%m-%d').date()
        if data_inicio > data_fim:
            messages.warning(request, 'A data inicial não pode ser maior que a final. Exibindo mês atual.')
            data_inicio = inicio_mes
            data_fim = fim_mes
    except Exception:
        messages.error(request, 'Formato de data inválido. Exibindo mês atual.')
        data_inicio = inicio_mes
        data_fim = fim_mes

    # Queries base
    receitas = Receita.objects.filter(
        usuario=request.user,
        data__range=[data_inicio, data_fim]
    )
    despesas = Despesa.objects.filter(
        usuario=request.user,
        data__range=[data_inicio, data_fim]
    )

    # KPIs principais
    total_receitas = receitas.filter(status='R').aggregate(total=Sum('valor'))['total'] or 0
    total_despesas = despesas.filter(status='R').aggregate(total=Sum('valor'))['total'] or 0
    saldo_periodo = total_receitas - total_despesas

    # Receitas/Despesas pendentes
    receitas_pendentes = receitas.filter(status='P').aggregate(total=Sum('valor'))['total'] or 0
    despesas_pendentes = despesas.filter(status='P').aggregate(total=Sum('valor'))['total'] or 0

    # Contas em atraso
    receitas_atraso = receitas.filter(
        status='P',
        data_vencimento__lt=hoje
    ).count()
    despesas_atraso = despesas.filter(
        status='P',
        data_vencimento__lt=hoje
    ).count()

    # Dados para gráficos
    receitas_por_categoria = list(receitas.filter(status='R').values('categoria').annotate(
        total=Sum('valor')
    ).order_by('-total'))

    despesas_por_categoria = list(despesas.filter(status='R').values('categoria').annotate(
        total=Sum('valor')
    ).order_by('-total'))

    # Fluxo de caixa dos últimos 30 dias
    fluxo_data = []
    for i in range(30):
        data = hoje - timedelta(days=i)
        receitas_dia = receitas.filter(data=data, status='R').aggregate(total=Sum('valor'))['total'] or 0
        despesas_dia = despesas.filter(data=data, status='R').aggregate(total=Sum('valor'))['total'] or 0
        fluxo_data.append({
            'data': data.strftime('%Y-%m-%d'),
            'receitas': float(receitas_dia),
            'despesas': float(despesas_dia),
            'saldo': float(receitas_dia - despesas_dia)
        })
    
    fluxo_data.reverse()

    # Converter Decimal para float para serialização JSON
    for item in receitas_por_categoria:
        item['total'] = float(item['total']) if item['total'] else 0
    
    for item in despesas_por_categoria:
        item['total'] = float(item['total']) if item['total'] else 0

    context = {
        'total_receitas': total_receitas,
        'total_despesas': total_despesas,
        'saldo_periodo': saldo_periodo,
        'receitas_pendentes': receitas_pendentes,
        'despesas_pendentes': despesas_pendentes,
        'receitas_atraso': receitas_atraso,
        'despesas_atraso': despesas_atraso,
        'receitas_por_categoria': json.dumps(receitas_por_categoria),
        'despesas_por_categoria': json.dumps(despesas_por_categoria),
        'fluxo_data': json.dumps(fluxo_data),
        'data_inicio': data_inicio,
        'data_fim': data_fim,
    }
    
    return render(request, 'financeiro/dashboard.html', context)

# =======================
# Listagem
# =======================

@login_required
def listar(request):
    tipo = request.GET.get('tipo', 'todos')  # receitas, despesas, todos
    categoria = request.GET.get('categoria', '')
    status = request.GET.get('status', '')
    busca = request.GET.get('busca', '')

    receitas = Receita.objects.filter(usuario=request.user)
    despesas = Despesa.objects.filter(usuario=request.user)

    # Aplicar filtros
    if categoria:
        receitas = receitas.filter(categoria=categoria)
        despesas = despesas.filter(categoria=categoria)
    
    if status:
        receitas = receitas.filter(status=status)
        despesas = despesas.filter(status=status)
    
    if busca:
        receitas = receitas.filter(
            Q(descricao__icontains=busca) | 
            Q(cliente__nome__icontains=busca)
        )
        despesas = despesas.filter(descricao__icontains=busca)

    # Ordenação
    receitas = receitas.order_by('-data')
    despesas = despesas.order_by('-data')

    context = {
        'receitas': receitas if tipo in ['receitas', 'todos'] else [],
        'despesas': despesas if tipo in ['despesas', 'todos'] else [],
        'tipo': tipo,
        'categoria': categoria,
        'status': status,
        'busca': busca,
    }
    
    return render(request, 'financeiro/listar.html', context)

# =======================
# CRUD Receitas
# =======================

@login_required
def nova_receita(request):
    form = ReceitaForm(request.POST or None, request.FILES or None)
    if form.is_valid():
        receita = form.save(commit=False)
        receita.usuario = request.user
        receita.save()
        messages.success(request, 'Receita cadastrada com sucesso!')
        return redirect('financeiro:listar')
    return render(request, 'financeiro/form.html', {'form': form, 'tipo': 'Receita'})

@login_required
def editar_receita(request, pk):
    receita = get_object_or_404(Receita, pk=pk, usuario=request.user)
    form = ReceitaForm(request.POST or None, request.FILES or None, instance=receita)
    if form.is_valid():
        form.save()
        messages.success(request, 'Receita atualizada com sucesso!')
        return redirect('financeiro:listar')
    return render(request, 'financeiro/form.html', {'form': form, 'tipo': 'Receita'})

@login_required
def deletar_receita(request, pk):
    receita = get_object_or_404(Receita, pk=pk, usuario=request.user)
    if request.method == 'POST':
        receita.delete()
        messages.success(request, 'Receita excluída com sucesso!')
        return redirect('financeiro:listar')
    return render(request, 'financeiro/confirmar_exclusao.html', {'objeto': receita, 'tipo': 'receita'})

# =======================
# CRUD Despesas
# =======================

@login_required
def nova_despesa(request):
    form = DespesaForm(request.POST or None, request.FILES or None)
    if form.is_valid():
        despesa = form.save(commit=False)
        despesa.usuario = request.user
        despesa.save()
        messages.success(request, 'Despesa cadastrada com sucesso!')
        return redirect('financeiro:listar')
    return render(request, 'financeiro/form.html', {'form': form, 'tipo': 'Despesa'})

@login_required
def editar_despesa(request, pk):
    despesa = get_object_or_404(Despesa, pk=pk, usuario=request.user)
    form = DespesaForm(request.POST or None, request.FILES or None, instance=despesa)
    if form.is_valid():
        form.save()
        messages.success(request, 'Despesa atualizada com sucesso!')
        return redirect('financeiro:listar')
    return render(request, 'financeiro/form.html', {'form': form, 'tipo': 'Despesa'})

@login_required
def deletar_despesa(request, pk):
    despesa = get_object_or_404(Despesa, pk=pk, usuario=request.user)
    if request.method == 'POST':
        despesa.delete()
        messages.success(request, 'Despesa excluída com sucesso!')
        return redirect('financeiro:listar')
    return render(request, 'financeiro/confirmar_exclusao.html', {'objeto': despesa, 'tipo': 'despesa'})

# =======================
# Centro de Custos
# =======================

@login_required
def centros_custo(request):
    centros = CentroCusto.objects.all().order_by('nome')
    return render(request, 'financeiro/centros_custo.html', {'centros': centros})

@login_required
def novo_centro_custo(request):
    form = CentroCustoForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, 'Centro de custo criado com sucesso!')
        return redirect('financeiro:centros_custo')
    return render(request, 'financeiro/form.html', {'form': form, 'tipo': 'Centro de Custo'})

@login_required
def editar_centro_custo(request, pk):
    centro = get_object_or_404(CentroCusto, pk=pk)
    form = CentroCustoForm(request.POST or None, instance=centro)
    if form.is_valid():
        form.save()
        messages.success(request, 'Centro de custo atualizado com sucesso!')
        return redirect('financeiro:centros_custo')
    return render(request, 'financeiro/form.html', {'form': form, 'tipo': 'Centro de Custo'})

# =======================
# Relatórios
# =======================

@login_required
def relatorios(request):
    form = RelatorioForm(request.GET or None)
    context = {'form': form}
    
    if form.is_valid():
        data_inicio = form.cleaned_data['data_inicio']
        data_fim = form.cleaned_data['data_fim']
        
        # Dados do relatório
        receitas = Receita.objects.filter(
            usuario=request.user,
            data__range=[data_inicio, data_fim]
        )
        despesas = Despesa.objects.filter(
            usuario=request.user,
            data__range=[data_inicio, data_fim]
        )
        
        # Totais
        total_receitas = receitas.aggregate(total=Sum('valor'))['total'] or 0
        total_despesas = despesas.aggregate(total=Sum('valor'))['total'] or 0
        
        # Por categoria
        receitas_categoria = receitas.values('categoria').annotate(
            total=Sum('valor'), count=Count('id')
        ).order_by('-total')
        
        despesas_categoria = despesas.values('categoria').annotate(
            total=Sum('valor'), count=Count('id')
        ).order_by('-total')
        
        context.update({
            'dados_carregados': True,
            'data_inicio': data_inicio,
            'data_fim': data_fim,
            'total_receitas': total_receitas,
            'total_despesas': total_despesas,
            'saldo': total_receitas - total_despesas,
            'receitas_categoria': receitas_categoria,
            'despesas_categoria': despesas_categoria,
            'receitas': receitas[:10],  # Últimas 10
            'despesas': despesas[:10],  # Últimas 10
        })
    
    return render(request, 'financeiro/relatorios.html', context)

# =======================
# APIs para gráficos
# =======================

@login_required
def api_fluxo_caixa(request):
    """API para dados do gráfico de fluxo de caixa"""
    dias = int(request.GET.get('dias', 30))
    hoje = timezone.now().date()
    
    dados = []
    for i in range(dias):
        data = hoje - timedelta(days=i)
        receitas = Receita.objects.filter(
            usuario=request.user,
            data=data,
            status='R'
        ).aggregate(total=Sum('valor'))['total'] or 0
        
        despesas = Despesa.objects.filter(
            usuario=request.user,
            data=data,
            status='R'
        ).aggregate(total=Sum('valor'))['total'] or 0
        
        dados.append({
            'data': data.strftime('%Y-%m-%d'),
            'receitas': float(receitas),
            'despesas': float(despesas),
            'saldo': float(receitas - despesas)
        })
    
    dados.reverse()
    return JsonResponse({'dados': dados})

# =======================
# Utilitários
# =======================

@login_required
def marcar_realizado(request, tipo, pk):
    """Marca receita/despesa como realizada"""
    if tipo == 'receita':
        obj = get_object_or_404(Receita, pk=pk, usuario=request.user)
    else:
        obj = get_object_or_404(Despesa, pk=pk, usuario=request.user)
    
    obj.status = 'R'
    obj.save()
    
    messages.success(request, f'{tipo.title()} marcada como realizada!')
    return redirect('financeiro:listar')
