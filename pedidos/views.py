from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_GET
from django.contrib.auth.decorators import login_required
from django.db.models import Max, Q, Sum, Count, Avg
from django.utils import timezone
from datetime import datetime, timedelta
import json
from django.db import transaction
from django.template.loader import render_to_string

from .models import Pedido, ItemPedido, HistoricoPedido, AnexoPedido
from .forms import PedidoForm, ItemPedidoFormSet, FiltrosPedidoForm, HistoricoPedidoForm, AnexoPedidoForm
from produtos.models import Produto # Certifique-se de que Produto é importado corretamente
# Se CategoriaProduto é um modelo separado, você pode precisar importá-lo aqui também,
# dependendo de onde ele está definido.
# from produtos.models import CategoriaProduto # Exemplo se CategoriaProduto está em produtos/models.py
from clientes.models import Cliente     

def gerar_numero_pedido():
    ultimo = Pedido.objects.aggregate(max_num=Max('id'))['max_num'] or 0
    return f'PED-{ultimo+1:04d}'

@login_required
def dashboard(request):
    """Dashboard com métricas e KPIs de pedidos"""
    hoje = timezone.now().date()
    inicio_mes = hoje.replace(day=1)
    fim_mes = (inicio_mes + timedelta(days=32)).replace(day=1) - timedelta(days=1)
    
    # Filtros de período
    data_inicio = request.GET.get('data_inicio', inicio_mes)
    data_fim = request.GET.get('data_fim', fim_mes)
    
    if isinstance(data_inicio, str):
        data_inicio = datetime.strptime(data_inicio, '%Y-%m-%d').date()
    if isinstance(data_fim, str):
        data_fim = datetime.strptime(data_fim, '%Y-%m-%d').date()

    # Queries base
    pedidos = Pedido.objects.filter(
        data__range=[data_inicio, data_fim]
    ).exclude(status='C').prefetch_related('itens')  # Excluir cancelados

    # KPIs principais
    total_pedidos = pedidos.count()
    
    # Calcular valores usando uma lista para otimizar
    pedidos_list = list(pedidos)
    valor_total = sum(p.valor_total for p in pedidos_list)
    valor_medio = valor_total / total_pedidos if total_pedidos > 0 else 0
    
    # Agrupar pedidos por status e criado_por usando a lista já carregada
    from collections import defaultdict
    
    pedidos_por_status_dict = defaultdict(lambda: {'count': 0, 'valor': 0})
    pedidos_por_vendedor_dict = defaultdict(lambda: {'count': 0, 'valor': 0})
    
    for pedido in pedidos_list:
        # Por status
        pedidos_por_status_dict[pedido.status]['count'] += 1
        pedidos_por_status_dict[pedido.status]['valor'] += pedido.valor_total
        
        # Por vendedor (usando criado_por)
        vendedor = pedido.usuario.username if pedido.usuario else 'Sem vendedor'
        pedidos_por_vendedor_dict[vendedor]['count'] += 1
        pedidos_por_vendedor_dict[vendedor]['valor'] += pedido.valor_total
    
    # Converter para lista para o template
    pedidos_por_status = []
    for status, dados in pedidos_por_status_dict.items():
        pedidos_por_status.append({
            'status': status,
            'count': dados['count'],
            'valor': dados['valor']
        })
    
    pedidos_por_vendedor = []
    for vendedor, dados in pedidos_por_vendedor_dict.items():
        pedidos_por_vendedor.append({
            'vendedor': vendedor,
            'count': dados['count'],
            'valor': dados['valor']
        })
    
    # Ordenar por valor
    pedidos_por_vendedor = sorted(pedidos_por_vendedor, key=lambda x: x['valor'], reverse=True)
    
    # Alertas e pendências
    pedidos_em_atraso = pedidos.filter(
        data_entrega__lt=hoje,
        status__in=['P', 'A', 'E'],
        arte_aprovada=False
    ).count()
    
    entregas_em_atraso = pedidos.filter(
        data_entrega__lt=hoje,
        status__in=['P', 'A', 'E']
    ).count()
    
    pedidos_urgentes = pedidos.filter(status='P').count()
    
    # Produtos mais vendidos
    produtos_vendidos = ItemPedido.objects.filter(
        pedido__in=pedidos
    ).values('produto__descricao').annotate(
        quantidade_total=Sum('quantidade')
    ).order_by('-quantidade_total')[:10]
    
    # Calcular valor total manually para cada produto
    for produto in produtos_vendidos:
        itens = ItemPedido.objects.filter(
            pedido__in=pedidos,
            produto__descricao=produto['produto__descricao']
        )
        produto['valor_total'] = sum(item.valor_total for item in itens)
    
    # Dados para gráficos
    vendas_diarias_dict = defaultdict(lambda: {'quantidade': 0, 'valor': 0})
    
    # Agrupar pedidos por data
    for pedido in pedidos_list:
        data_str = pedido.data.strftime('%Y-%m-%d')
        vendas_diarias_dict[data_str]['quantidade'] += 1
        vendas_diarias_dict[data_str]['valor'] += pedido.valor_total
    
    # Gerar lista dos últimos 30 dias
    vendas_diarias = []
    for i in range(30):
        data = hoje - timedelta(days=i)
        data_str = data.strftime('%Y-%m-%d')
        vendas_diarias.append({
            'data': data_str,
            'quantidade': vendas_diarias_dict[data_str]['quantidade'],
            'valor': float(vendas_diarias_dict[data_str]['valor'])
        })
    
    vendas_diarias.reverse()
    
    # Converter para JSON
    pedidos_por_status_json = []
    for item in pedidos_por_status:
        status_display = dict(Pedido.STATUS_CHOICES).get(item['status'], 'Status Desconhecido')
        pedidos_por_status_json.append({
            'status': item['status'],
            'status_display': status_display,
            'count': item['count'],
            'valor': float(item['valor'] or 0)
        })

    context = {
        'total_pedidos': total_pedidos,
        'valor_total': valor_total,
        'valor_medio': valor_medio,
        'pedidos_em_atraso': pedidos_em_atraso,
        'entregas_em_atraso': entregas_em_atraso,
        'pedidos_urgentes': pedidos_urgentes,
        'pedidos_por_status': json.dumps(pedidos_por_status_json),
        'pedidos_por_vendedor': pedidos_por_vendedor,
        'produtos_vendidos': produtos_vendidos,
        'vendas_diarias': json.dumps(vendas_diarias),
        'data_inicio': data_inicio,
        'data_fim': data_fim,
    }
    
    return render(request, 'pedidos/dashboard.html', context)


@login_required
def listar(request):
    """Lista pedidos com filtros avançados"""
    form = FiltrosPedidoForm(request.GET or None)
    pedidos = Pedido.objects.select_related('cliente').prefetch_related('itens')

    # Aplicar filtros
    if form.is_valid():
        if form.cleaned_data['status']:
            pedidos = pedidos.filter(status=form.cleaned_data['status'])
        
        if form.cleaned_data['prioridade']:
            pedidos = pedidos.filter(prioridade=form.cleaned_data['prioridade'])
        
        if form.cleaned_data['vendedor']:
            pedidos = pedidos.filter(vendedor=form.cleaned_data['vendedor'])
        
        if form.cleaned_data['data_inicio']:
            pedidos = pedidos.filter(data__gte=form.cleaned_data['data_inicio'])
        
        if form.cleaned_data['data_fim']:
            pedidos = pedidos.filter(data__lte=form.cleaned_data['data_fim'])
        
        if form.cleaned_data['busca']:
            query = form.cleaned_data['busca']
            pedidos = pedidos.filter(
                Q(cliente__nome__icontains=query) |
                Q(codigo__icontains=query) |
                Q(observacoes__icontains=query)
            )

    # Ordenação
    ordenacao = request.GET.get('ordem', '-criado_em')
    pedidos = pedidos.order_by(ordenacao)

    # Estatísticas rápidas
    total_pedidos = pedidos.count()
    valor_total = sum(p.total for p in pedidos)
    
    context = {
        'pedidos': pedidos,
        'form': form,
        'total_pedidos': total_pedidos,
        'valor_total': valor_total,
        'status_choices': dict(Pedido.STATUS_CHOICES),
    }
    
    return render(request, 'pedidos/listar.html', context)


@login_required
@transaction.atomic
def novo_pedido(request):
    # Se houver um cliente_id na URL, pré-seleciona o cliente
    cliente_id = request.GET.get('cliente_id')
    initial = {}
    if cliente_id:
        try:
            cliente = Cliente.objects.get(pk=cliente_id)
            initial['cliente'] = cliente
        except Cliente.DoesNotExist:
            messages.warning(request, 'Cliente não encontrado.')
    
    form = PedidoForm(request.POST or None, request.FILES or None, initial=initial)
    formset = ItemPedidoFormSet(request.POST or None)

    if request.method == 'POST':
        if not form.is_valid() or not formset.is_valid():
            if not form.is_valid():
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f'Erro no campo {field}: {error}')
            if not formset.is_valid():
                messages.error(request, 'Itens do pedido inválidos. Verifique os campos dos produtos.')
        else:
            # 1️⃣ Salva o pedido sem commitar tudo ainda
            pedido = form.save(commit=False)
            pedido.numero_pedido = gerar_numero_pedido()
            pedido.usuario = request.user
            # Garante que o cliente está presente
            if not pedido.cliente:
                messages.error(request, 'Selecione um cliente para o pedido.')
                return render(request, 'pedidos/form.html', {
                    'form': form,
                    'formset': formset,
                    'action': 'Criar'
                })
            pedido.save()

            # 2️⃣ Salva campos ManyToMany e uploads
            form.save_m2m()

            # 3️⃣ Agora associe e salve os itens do formset
            formset.instance = pedido
            formset.save()
            # Salva novamente para atualizar totais com os itens já salvos
            pedido.save()
            
            # 4️⃣ Registra o histórico de criação
            HistoricoPedido.objects.create(
                pedido=pedido,
                tipo='criacao',
                descricao=f'Pedido criado por {request.user.username}',
                usuario=request.user
            )

            # 5️⃣ Cria a receita no módulo financeiro
            try:
                from financeiro.models import Receita
                Receita.objects.create(
                    descricao=f'Receita referente ao pedido {pedido.codigo}',
                    data=pedido.data,
                    valor=pedido.valor_total,
                    categoria='pedido',
                    cliente=pedido.cliente,
                    pedido=pedido,
                    usuario=request.user
                )
            except Exception as e:
                messages.error(request, f'Erro ao criar receita no financeiro: {e}')

            messages.success(request, f'Pedido {pedido.codigo} cadastrado com sucesso!')
            return redirect('pedidos:detalhes', pk=pedido.pk)

    return render(request, 'pedidos/form.html', {
        'form': form,
        'formset': formset,
        'action': 'Criar'
    })


@login_required
def editar_pedido(request, pk):
    pedido = get_object_or_404(Pedido, pk=pk)
    status_anterior = pedido.status
    
    form = PedidoForm(request.POST or None, request.FILES or None, instance=pedido)
    formset = ItemPedidoFormSet(request.POST or None, instance=pedido)

    if request.method == 'POST' and form.is_valid() and formset.is_valid():
        pedido = form.save()
        formset.save()
        
        # Criar histórico se status mudou
        if status_anterior != pedido.status:
            HistoricoPedido.objects.create(
                pedido=pedido,
                tipo='status',
                status_anterior=status_anterior,
                status_novo=pedido.status,
                descricao=f'Status alterado de {dict(Pedido.STATUS_CHOICES)[status_anterior]} para {dict(Pedido.STATUS_CHOICES)[pedido.status]}',
                usuario=request.user
            )
        else:
            HistoricoPedido.objects.create(
                pedido=pedido,
                tipo='edicao',
                descricao=f'Pedido editado por {request.user.username}',
                usuario=request.user
            )
        
        # Se o pedido foi marcado como concluído, verificar se criou receita e atualizar usuário
        if pedido.status == 'C' and status_anterior != 'C':
            from financeiro.models import Receita
            receita = Receita.objects.filter(pedido=pedido).first()
            if receita and receita.usuario_id == 1:  # Se foi criado com usuário padrão
                receita.usuario = request.user
                receita.save()
            messages.info(request, 'Receita criada automaticamente no módulo financeiro!')
        
        messages.success(request, f'Pedido {pedido.codigo} atualizado com sucesso!')
        return redirect('pedidos:detalhes', pk=pedido.pk)

    return render(request, 'pedidos/form.html', {
        'form': form,
        'formset': formset,
        'pedido': pedido,
        'action': 'Editar'
    })


@login_required
def detalhes_pedido(request, pk):
    """View detalhada do pedido com histórico e anexos"""
    pedido = get_object_or_404(Pedido, pk=pk)
    historico = pedido.historico.all()
    anexos = pedido.anexos.all()
    
    context = {
        'pedido': pedido,
        'historico': historico,
        'anexos': anexos,
        'proximos_status': pedido.proximo_status_disponivel(),
        'status_choices': dict(Pedido.STATUS_CHOICES),
    }
    
    return render(request, 'pedidos/detalhes.html', context)

@login_required
def excluir_pedido(request, pk):
    pedido = get_object_or_404(Pedido, pk=pk)
    if request.method == 'POST':
        codigo = pedido.codigo  # antes era pedido.numero_pedido
        pedido.delete()
        messages.success(request, f'Pedido {codigo} excluído com sucesso!')
        return redirect('pedidos:listar')
    return render(request, 'pedidos/confirmar_exclusao.html', {'pedido': pedido})


@login_required
def alterar_status(request, pk, novo_status):
    """Altera o status do pedido conforme regras de negócio"""
    pedido = get_object_or_404(Pedido, pk=pk)
    
    # Verificar se o novo status é válido
    if novo_status not in dict(Pedido.STATUS_CHOICES):
        messages.error(request, 'Status inválido.')
        return redirect('pedidos:detalhes', pk=pedido.pk)
    
    # Verificar se a transição é permitida
    if novo_status not in pedido.proximo_status_disponivel():
        messages.error(request, f'Não é possível alterar o status de {pedido.get_status_display()} para {dict(Pedido.STATUS_CHOICES)[novo_status]}.')
        return redirect('pedidos:detalhes', pk=pedido.pk)
    
    # Validações específicas por status
    if novo_status == 'A':  # Aprovado
        # Arte aprovada não é mais obrigatória
        if not pedido.sinal_pago:
            messages.error(request, 'O sinal (60%) precisa ser pago antes de aprovar o pedido.')
            return redirect('pedidos:detalhes', pk=pedido.pk)
    
    elif novo_status == 'E':  # Enviado
        if not pedido.forma_envio:
            messages.error(request, 'A forma de envio precisa ser definida.')
            return redirect('pedidos:detalhes', pk=pedido.pk)
        # Se houver valor restante a receber, criar receita pendente no financeiro
        valor_restante = pedido.valor_total - (pedido.valor_sinal or 0)
        if valor_restante > 0:
            try:
                from financeiro.models import Receita
                Receita.objects.create(
                    descricao=f'Receita pendente referente ao pedido {pedido.codigo}',
                    data=timezone.now().date(),
                    valor=valor_restante,
                    categoria='pedido',
                    cliente=pedido.cliente,
                    pedido=pedido,
                    usuario=request.user,
                    status='P',
                )
                messages.info(request, f'Receita pendente de R$ {valor_restante:.2f} criada no financeiro.')
            except Exception as e:
                messages.error(request, f'Erro ao criar receita pendente no financeiro: {e}')
    
    elif novo_status == 'T':  # Entregue
        if not pedido.data_entrega:
            pedido.data_entrega = timezone.now()
    
    # Registrar status anterior
    status_anterior = pedido.status
    
    # Atualizar status
    pedido.status = novo_status
    pedido.save()
    
    # Mensagem de sucesso
    messages.success(request, f'Status alterado com sucesso para {pedido.get_status_display()}.')
    
    return redirect('pedidos:detalhes', pk=pedido.pk)

@login_required
def adicionar_observacao(request, pk):
    """Adiciona observação ao histórico do pedido"""
    pedido = get_object_or_404(Pedido, pk=pk)
    
    if request.method == 'POST':
        form = HistoricoPedidoForm(request.POST)
        if form.is_valid():
            historico = form.save(commit=False)
            historico.pedido = pedido
            historico.usuario = request.user
            historico.save()
            messages.success(request, 'Observação adicionada com sucesso!')
            return redirect('pedidos:detalhes', pk=pk)
    else:
        form = HistoricoPedidoForm()
    
    return render(request, 'pedidos/adicionar_observacao.html', {
        'pedido': pedido,
        'form': form
    })


@require_GET
@login_required
def get_preco_produto(request):
    produto_id = request.GET.get('produto_id')
    try:
        prod = Produto.objects.get(pk=produto_id)
        return JsonResponse({'preco': float(prod.preco_venda)})
    except Produto.DoesNotExist:
        return JsonResponse({'error': 'Produto não encontrado'}, status=404)

@require_GET
@login_required
def buscar_produtos_ajax(request):
    """View para busca de produtos via AJAX"""
    term = request.GET.get('term', '').strip()
    
    if not term:
        return JsonResponse({'results': []})
    
    palavras = term.split()
    
    query = Q()
    
    for palavra in palavras:
        query &= (
            Q(descricao__icontains=palavra) |
            Q(codigo__icontains=palavra) |
            # CORREÇÃO AQUI: Agora que 'categoria' é um objeto CategoriaProduto (ForeignKey)
            # você deve acessar um campo string dele, como 'nome'.
            Q(categoria__nome__icontains=palavra) 
        )
    
    produtos = Produto.objects.filter(query).order_by('descricao')[:10]
    
    results = [{
        'id': produto.id,
        'text': produto.descricao,
        'descricao': produto.descricao,
        'preco_custo': float(produto.preco_custo) if produto.preco_custo else None,
        'preco_venda': float(produto.preco_venda) if produto.preco_venda else  '0',
        'estoque': produto.estoque,
        'estoque_minimo': produto.estoque_minimo,
                # CORREÇÃO AQUI: Acessa o atributo 'nome' do objeto CategoriaProduto,
        # e verifica se o objeto existe para evitar erro se for nulo.
        'categoria': produto.categoria.nome if produto.categoria else None 
    } for produto in produtos]
    
    return JsonResponse({'results': results})

# ==== PDF DO PEDIDO ====
from django.template.loader import render_to_string
from xhtml2pdf import pisa
from io import BytesIO

@login_required
def pedido_pdf(request, pedido_id):
    pedido = get_object_or_404(Pedido, pk=pedido_id)
    html_string = render_to_string('pedidos/modelo_pedido.html', {
        'pedido': pedido,
        'cliente': pedido.cliente,
        'vendedor': pedido.vendedor,
    }, request=request)
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html_string.encode('utf-8')), result, encoding='utf-8')
    if not pdf.err:
        response = HttpResponse(result.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'filename=pedido_{pedido.codigo}.pdf'
        return response
    return HttpResponse('Erro ao gerar PDF', status=500)
def gerar_pedido_pdf(request, pedido_id):
    pedido = Pedido.objects.get(id=pedido_id)
    
    # Adiciona o atributo .total somando os itens + taxas - descontos
    total = sum([item.total for item in pedido.itens.all()]) + pedido.taxa_entrega - pedido.desconto
    pedido.total = total

    html_string = render_to_string('pedidos/pedido_pdf.html', {'pedido': pedido})
    html = HTML(string=html_string)
    
    pdf_file = html.write_pdf()
    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = f'filename=pedido_{pedido.codigo}.pdf'
    return response