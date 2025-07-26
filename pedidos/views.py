import json
from datetime import datetime, timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Count, F, Q, Sum
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_GET

from clientes.models import Cliente
from configuracao.models import ConfiguracaoSistema
from produtos.models import Produto

from .forms import AnexoPedidoForm, FiltrosPedidoForm, HistoricoPedidoForm, ItemPedidoFormSet, PedidoForm
from .models import AnexoPedido, HistoricoPedido, ItemPedido, Pedido


# Função auxiliar para unificar os filtros de pedidos
def get_pedidos_queryset(request, use_date_filter=True, exclude_cancelled=True):
    # pyrefly: ignore  # missing-attribute
    pedidos = Pedido.objects.select_related("cliente", "usuario").prefetch_related("itens", "historico", "anexos")
    
    # Só exclui cancelados se não estiver filtrando especificamente por eles
    if exclude_cancelled:
        status_filtro = request.GET.get("status")
        if status_filtro != "C":  # Se não está filtrando por cancelados, exclui eles
            pedidos = pedidos.exclude(status="C")
    
    data_inicio = request.GET.get("data_inicio")
    data_fim = request.GET.get("data_fim")
    if use_date_filter:
        hoje = timezone.now().date()
        inicio_mes = hoje.replace(day=1)
        fim_mes = (inicio_mes + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        if not data_inicio:
            data_inicio = inicio_mes
        if not data_fim:
            data_fim = fim_mes
        if isinstance(data_inicio, str):
            data_inicio = datetime.strptime(data_inicio, "%Y-%m-%d").date()
        if isinstance(data_fim, str):
            data_fim = datetime.strptime(data_fim, "%Y-%m-%d").date()
        pedidos = pedidos.filter(data__range=[data_inicio, data_fim])
    return pedidos


@login_required
def dashboard(request):
    pedidos = get_pedidos_queryset(request, use_date_filter=True)
    hoje = timezone.now().date()
    data_inicio = request.GET.get("data_inicio")
    data_fim = request.GET.get("data_fim")
    if not data_inicio:
        data_inicio = hoje.replace(day=1)
    if not data_fim:
        data_fim = (data_inicio + timedelta(days=32)).replace(day=1) - timedelta(days=1)
    if isinstance(data_inicio, str):
        data_inicio = datetime.strptime(data_inicio, "%Y-%m-%d").date()
    if isinstance(data_fim, str):
        data_fim = datetime.strptime(data_fim, "%Y-%m-%d").date()

    total_pedidos = pedidos.count()
    # Usa agregação SQL para calcular o total de vendas
    total_agg = pedidos.aggregate(total=Sum(F('itens__quantidade') * F('itens__preco_unitario')))['total'] or 0
    valor_total = total_agg
    valor_medio = valor_total / total_pedidos if total_pedidos > 0 else 0

    entregas_em_atraso = pedidos.filter(data_entrega__lt=hoje, status__in=["P", "A", "E"]).count()

    pedidos_em_atraso = pedidos.filter(data_entrega_prevista__lt=hoje, status__in=["P", "A", "E"]).count()

    pedidos_urgentes = pedidos.filter(prioridade="U").count()

    # Gráficos e KPIs agrupados
    pedidos_por_status = []
    for status_code, status_label in Pedido.Status.choices:
        pedidos_status = [p for p in pedidos if p.status == status_code]
        pedidos_por_status.append(
            {
                "status": status_code,
                "status_display": status_label,
                "count": len(pedidos_status),
                "valor": float(sum(p.total for p in pedidos_status)),
            }
        )

    pedidos_por_vendedor = []
    vendedores = set(p.vendedor for p in pedidos)
    for vendedor_nome in vendedores:
        pedidos_vendedor = [p for p in pedidos if p.vendedor == vendedor_nome]
        pedidos_por_vendedor.append(
            {
                "vendedor": vendedor_nome,
                "count": len(pedidos_vendedor),
                "valor": float(sum(p.total for p in pedidos_vendedor)),
            }
        )
    pedidos_por_vendedor.sort(key=lambda x: x["valor"], reverse=True)

    # pyrefly: ignore  # missing-attribute
    produtos_vendidos = (
        ItemPedido.objects.filter(pedido__in=pedidos)
        .values("produto__descricao")
        .annotate(quantidade_total=Sum("quantidade"), valor_total=Sum(F("quantidade") * F("preco_unitario")))
        .order_by("-quantidade_total")[:10]
    )

    # Vendas diárias
    from collections import defaultdict

    vendas_diarias_dict = defaultdict(lambda: {"quantidade": 0, "valor": 0.0})
    vendas_por_dia = {}
    for p in pedidos:
        data_str = p.data.strftime("%Y-%m-%d")
        # pyrefly: ignore  # missing-attribute
        vendas_por_dia.setdefault(data_str, {"quantidade": 0, "valor": 0.0})
        vendas_por_dia[data_str]["quantidade"] += 1
        vendas_por_dia[data_str]["valor"] += float(p.total)
    vendas_diarias = []
    for i in range(30):
        data = hoje - timedelta(days=i)
        data_str = data.strftime("%Y-%m-%d")
        vendas_diarias.append(
            {
                "data": data_str,
                "quantidade": vendas_por_dia.get(data_str, {"quantidade": 0})["quantidade"],
                "valor": vendas_por_dia.get(data_str, {"valor": 0.0})["valor"],
            }
        )
    vendas_diarias.reverse()

    context = {
        "total_pedidos": total_pedidos,
        "valor_total": valor_total,
        "valor_medio": valor_medio,
        "entregas_em_atraso": entregas_em_atraso,
        "pedidos_em_atraso": pedidos_em_atraso,
        "pedidos_urgentes": pedidos_urgentes,
        "pedidos_por_status": json.dumps(pedidos_por_status),
        "pedidos_por_vendedor": pedidos_por_vendedor,
        "produtos_vendidos": produtos_vendidos,
        "vendas_diarias": json.dumps(vendas_diarias),
        "data_inicio": data_inicio,
        "data_fim": data_fim,
    }

    return render(request, "pedidos/dashboard.html", context)


@login_required
def listar(request):
    form = FiltrosPedidoForm(request.GET or None)
    
    # Se há um filtro de status específico, não exclui cancelados automaticamente
    status_filtro = request.GET.get("status")
    exclude_cancelled = status_filtro != "C"  # Só exclui cancelados se não estiver filtrando por eles
    
    pedidos = get_pedidos_queryset(request, use_date_filter=False, exclude_cancelled=exclude_cancelled)
    
    if form.is_valid():
        # Só mostra "Entregue" se o filtro for usado
        if not form.cleaned_data.get("status"):
            pedidos = pedidos.exclude(status="T")
        else:
            if form.cleaned_data["status"]:
                pedidos = pedidos.filter(status=form.cleaned_data["status"])
        if form.cleaned_data["prioridade"]:
            pedidos = pedidos.filter(prioridade=form.cleaned_data["prioridade"])
        if form.cleaned_data["vendedor"]:
            pedidos = pedidos.filter(vendedor=form.cleaned_data["vendedor"])
        if form.cleaned_data["data_inicio"]:
            pedidos = pedidos.filter(data__gte=form.cleaned_data["data_inicio"])
        if form.cleaned_data["data_fim"]:
            pedidos = pedidos.filter(data__lte=form.cleaned_data["data_fim"])
        if form.cleaned_data["busca"]:
            query = form.cleaned_data["busca"]
            pedidos = pedidos.filter(
                # pyrefly: ignore  # missing-attribute
                Q(cliente__nome__icontains=query)
                | Q(cliente__nome_loja__icontains=query)
                | Q(codigo__icontains=query)
                | Q(observacoes__icontains=query)
            )
    else:
        # Caso o form não seja válido/exista, também oculta entregues
        pedidos = pedidos.exclude(status="T")

    # Ordena por data de previsão de entrega
    pedidos = pedidos.order_by("data_entrega_prevista", "codigo")
    total_pedidos = pedidos.count()
    # Usa agregação SQL para calcular o total de vendas
    total_agg = pedidos.aggregate(total=Sum(F('itens__quantidade') * F('itens__preco_unitario')))['total'] or 0
    valor_total = total_agg
    valor_medio = valor_total / total_pedidos if total_pedidos > 0 else 0

    context = {
        "pedidos": pedidos,
        "form": form,
        "total_pedidos": total_pedidos,
        "valor_total": valor_total,
        "valor_medio": valor_medio,
        # pyrefly: ignore  # no-matching-overload
        "status_choices": dict(Pedido.Status.choices),
    }
    return render(request, "pedidos/listar.html", context)


@login_required
@transaction.atomic
def novo_pedido(request):
    # Se houver um cliente_id na URL, pré-seleciona o cliente
    cliente_id = request.GET.get("cliente_id")
    initial = {}
    if cliente_id:
        try:
            # pyrefly: ignore  # missing-attribute
            cliente = Cliente.objects.get(pk=cliente_id)
            initial["cliente"] = cliente
        # pyrefly: ignore  # missing-attribute
        except Cliente.DoesNotExist:
            messages.warning(request, "Cliente não encontrado.")

    form = PedidoForm(request.POST or None, request.FILES or None, initial=initial)
    formset = ItemPedidoFormSet(request.POST or None)

    if request.method == "POST":
        if not form.is_valid() or not formset.is_valid():
            if not form.is_valid():
                # pyrefly: ignore  # missing-attribute
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f"Erro no campo {field}: {error}")
            if not formset.is_valid():
                messages.error(request, "Itens do pedido inválidos. Verifique os campos dos produtos.")
        else:
            # 1️⃣ Salva o pedido sem commitar tudo ainda
            pedido = form.save(commit=False)
            pedido.usuario = request.user
            # Garante que o cliente está presente
            if not pedido.cliente:
                messages.error(request, "Selecione um cliente para o pedido.")
                return render(request, "pedidos/form.html", {"form": form, "formset": formset, "action": "Criar"})
            pedido.save()

            # 2️⃣ Salva campos ManyToMany e uploads
            form.save_m2m()

            # 3️⃣ Agora associe e salve os itens do formset
            formset.instance = pedido
            formset.save()
            # Salva novamente para atualizar totais com os itens já salvos
            pedido.save()

            # 4️⃣ Registra o histórico de criação
            # pyrefly: ignore  # missing-attribute
            HistoricoPedido.objects.create(
                pedido=pedido,
                tipo="criacao",
                descricao=f"Pedido criado por {request.user.username}",
                usuario=request.user,
            )

            # 5️⃣ Cria a receita no módulo financeiro
            try:
                from financeiro.models import Receita

                if pedido.valor_recebido > 0:
                    # pyrefly: ignore  # missing-attribute
                    Receita.objects.create(
                        descricao=f"Receita referente ao pedido {pedido.codigo} (valor recebido)",
                        data=pedido.data,
                        valor=pedido.valor_recebido,
                        categoria="pedido",
                        cliente=pedido.cliente,
                        pedido=pedido,
                        usuario=request.user,
                        status="R",
                    )
                valor_pendente = pedido.valor_total - pedido.valor_recebido
                if valor_pendente > 0:
                    # pyrefly: ignore  # missing-attribute
                    Receita.objects.create(
                        descricao=f"Receita pendente referente ao pedido {pedido.codigo}",
                        data=pedido.data,
                        valor=valor_pendente,
                        categoria="pedido",
                        cliente=pedido.cliente,
                        pedido=pedido,
                        usuario=request.user,
                        status="P",
                    )
            except Exception as e:
                messages.error(request, f"Erro ao criar receita no financeiro: {e}")

            messages.success(request, f"Pedido {pedido.codigo} cadastrado com sucesso!")
            return redirect("pedidos:detalhes", pk=pedido.pk)

    return render(request, "pedidos/form.html", {"form": form, "formset": formset, "action": "Criar"})


@login_required
@transaction.atomic
def editar_pedido(request, pk):
    pedido = get_object_or_404(Pedido, pk=pk)
    status_anterior = pedido.status

    form = PedidoForm(request.POST or None, request.FILES or None, instance=pedido)
    formset = ItemPedidoFormSet(request.POST or None, instance=pedido)

    if request.method == "POST" and form.is_valid() and formset.is_valid():
        pedido = form.save()
        formset.save()

        # Criar histórico se status mudou
        if status_anterior != pedido.status:
            # pyrefly: ignore  # missing-attribute
            HistoricoPedido.objects.create(
                pedido=pedido,
                tipo="status",
                status_anterior=status_anterior,
                status_novo=pedido.status,
                # pyrefly: ignore  # no-matching-overload
                descricao=f"Status alterado de {dict(Pedido.Status.choices)[status_anterior]} para {dict(Pedido.Status.choices)[pedido.status]}",
                usuario=request.user,
            )
        else:
            # pyrefly: ignore  # missing-attribute
            HistoricoPedido.objects.create(
                pedido=pedido,
                tipo="edicao",
                descricao=f"Pedido editado por {request.user.username}",
                usuario=request.user,
            )

        # Se o pedido foi marcado como concluído, verificar se criou receita e atualizar usuário
        if pedido.status == "C" and status_anterior != "C":
            from financeiro.models import Receita

            # pyrefly: ignore  # missing-attribute
            receita = Receita.objects.filter(pedido=pedido).first()
            if receita and receita.usuario_id == 1:  # Se foi criado com usuário padrão
                receita.usuario = request.user
                receita.save()
            messages.info(request, "Receita criada automaticamente no módulo financeiro!")

        messages.success(request, f"Pedido {pedido.codigo} atualizado com sucesso!")
        return redirect("pedidos:detalhes", pk=pedido.pk)

    return render(
        request, "pedidos/form.html", {"form": form, "formset": formset, "pedido": pedido, "action": "Editar"}
    )


@login_required
def detalhes_pedido(request, pk):
    """View detalhada do pedido com histórico e anexos"""
    pedido = get_object_or_404(Pedido, pk=pk)
    historico = pedido.historico.all()
    anexos = pedido.anexos.all()

    context = {
        "pedido": pedido,
        "historico": historico,
        "anexos": anexos,
        "proximos_status": pedido.proximo_status_disponivel(),
        # pyrefly: ignore  # no-matching-overload
        "status_choices": dict(Pedido.Status.choices),
        # Diagnóstico extra
        "status_atual": pedido.status,
        "proximos_status_debug": pedido.proximo_status_disponivel(),
    }

    return render(request, "pedidos/detalhes.html", context)


@login_required
def excluir_pedido(request, pk):
    pedido = get_object_or_404(Pedido, pk=pk)
    if request.method == "POST":
        codigo = pedido.codigo  # antes era pedido.numero_pedido
        pedido.delete()
        messages.success(request, f"Pedido {codigo} excluído com sucesso!")
        return redirect("pedidos:listar")
    return render(request, "pedidos/confirmar_exclusao.html", {"pedido": pedido})


@login_required
def alterar_status(request, pk, novo_status):
    """Altera o status do pedido conforme regras de negócio"""
    pedido = get_object_or_404(Pedido, pk=pk)

    # Verificar se o novo status é válido
    # pyrefly: ignore  # no-matching-overload
    if novo_status not in dict(Pedido.Status.choices):
        messages.error(request, "Status inválido.")
        return redirect("pedidos:detalhes", pk=pedido.pk)

    # Verificar se a transição é permitida
    if novo_status not in pedido.proximo_status_disponivel():
        # pyrefly: ignore  # no-matching-overload
        messages.error(
            request,
            f"Não é possível alterar o status de {pedido.get_status_display()} para {dict(Pedido.Status.choices)[novo_status]}.",
        )
        return redirect("pedidos:detalhes", pk=pedido.pk)

    # Validações específicas por status
    if novo_status == "A":  # Aprovado
        # Arte aprovada não é mais obrigatória
        if not pedido.sinal_pago:
            messages.warning(request, "O sinal (60%) ainda não foi pago, mas o pedido foi aprovado.")

    elif novo_status == "E":  # Enviado
        if not pedido.forma_envio:
            messages.error(request, "A forma de envio precisa ser definida.")
            return redirect("pedidos:detalhes", pk=pedido.pk)

        from financeiro.models import Receita

        # Encontra e atualiza todas as receitas pendentes para este pedido
        # pyrefly: ignore  # missing-attribute
        receitas_pendentes = Receita.objects.filter(pedido=pedido, status="P")

        if receitas_pendentes.exists():
            # Atualiza todas as receitas pendentes de uma vez
            receitas_pendentes.update(status="R", data=timezone.now().date())

            # Atualiza o pedido para refletir o pagamento total
            pedido.valor_recebido = pedido.total
            pedido.restante_pago = True
            pedido.data_restante_pago = timezone.now()
            pedido.save(update_fields=["valor_recebido", "restante_pago", "data_restante_pago"])

            messages.info(request, "Receitas pendentes do pedido foram marcadas como realizadas no financeiro.")

        # Como garantia, certifica que todas as receitas do pedido estão como 'Realizado'
        # pyrefly: ignore  # missing-attribute
        Receita.objects.filter(pedido=pedido).exclude(status="R").update(status="R")

    elif novo_status == "T":  # Entregue
        if not pedido.data_entrega:
            pedido.data_entrega = timezone.now()

    # Registrar status anterior
    status_anterior = pedido.status

    # Se for cancelamento, marcar receitas como canceladas
    if novo_status == "C":
        from financeiro.models import Receita

        # pyrefly: ignore  # missing-attribute
        receitas_afetadas = Receita.objects.filter(pedido=pedido).update(status="C")
        messages.info(request, f"{receitas_afetadas} receita(s) do financeiro marcadas como canceladas.")

    # Atualizar status
    pedido.status = novo_status
    pedido.save()

    # Mensagem de sucesso
    messages.success(request, f"Status alterado com sucesso para {pedido.get_status_display()}.")

    return redirect("pedidos:detalhes", pk=pedido.pk)


@login_required
def adicionar_observacao(request, pk):
    """Adiciona observação ao histórico do pedido"""
    pedido = get_object_or_404(Pedido, pk=pk)

    if request.method == "POST":
        form = HistoricoPedidoForm(request.POST)
        if form.is_valid():
            historico = form.save(commit=False)
            historico.pedido = pedido
            historico.usuario = request.user
            historico.save()
            messages.success(request, "Observação adicionada com sucesso!")
            return redirect("pedidos:detalhes", pk=pk)
    else:
        form = HistoricoPedidoForm()

    return render(request, "pedidos/adicionar_observacao.html", {"pedido": pedido, "form": form})


@require_GET
@login_required
def get_preco_produto(request):
    produto_id = request.GET.get("produto_id")
    try:
        # pyrefly: ignore  # missing-attribute
        prod = Produto.objects.get(pk=produto_id)
        return JsonResponse({"preco": float(prod.preco_venda)})
    # pyrefly: ignore  # missing-attribute
    except Produto.DoesNotExist:
        return JsonResponse({"error": "Produto não encontrado"}, status=404)


@require_GET
@login_required
def buscar_produtos_ajax(request):
    """View para busca de produtos via AJAX"""
    term = request.GET.get("term", "").strip()

    if not term:
        return JsonResponse({"results": []})

    palavras = term.split()

    query = Q()

    # pyrefly: ignore  # bad-assignment
    for palavra in palavras:
        query &= (
            # pyrefly: ignore  # missing-attribute
            Q(descricao__icontains=palavra)
            | Q(codigo__icontains=palavra)
            |
            # CORREÇÃO AQUI: Agora que 'categoria' é um objeto CategoriaProduto (ForeignKey)
            # você deve acessar um campo string dele, como 'nome'.
            Q(categoria__nome__icontains=palavra)
        )

    # pyrefly: ignore  # missing-attribute
    produtos = Produto.objects.filter(query).order_by("descricao")[:10]

    results = [
        {
            "id": produto.id,
            "text": produto.descricao,
            "descricao": produto.descricao,
            "preco_custo": float(produto.preco_custo) if produto.preco_custo else None,
            "preco_venda": float(produto.preco_venda) if produto.preco_venda else "0",
            "estoque": produto.estoque,
            "estoque_minimo": produto.estoque_minimo,
            # CORREÇÃO AQUI: Acessa o atributo 'nome' do objeto CategoriaProduto,
            # e verifica se o objeto existe para evitar erro se for nulo.
            "categoria": produto.categoria.nome if produto.categoria else None,
        }
        for produto in produtos
    ]

    return JsonResponse({"results": results})


from io import BytesIO

# ==== PDF DO PEDIDO ====
from django.template.loader import render_to_string
from xhtml2pdf import pisa


@login_required
def pedido_pdf(request, pedido_id):
    pedido = get_object_or_404(Pedido, pk=pedido_id)
    # pyrefly: ignore  # missing-attribute
    configuracao = ConfiguracaoSistema.objects.first()
    html_string = render_to_string(
        "pedidos/modelo_pedido.html",
        {
            "pedido": pedido,
            "cliente": pedido.cliente,
            "vendedor": pedido.vendedor,
            "configuracao": configuracao,
            "pdf_export": True,
        },
        request=request,
    )
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html_string.encode("utf-8")), result, encoding="utf-8")
    # pyrefly: ignore  # missing-attribute
    if not pdf.err:
        response = HttpResponse(result.getvalue(), content_type="application/pdf")
        response["Content-Disposition"] = f"filename=pedido_{pedido.codigo}.pdf"
        return response
    return HttpResponse("Erro ao gerar PDF", status=500)
