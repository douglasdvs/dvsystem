# core/views.py
import logging
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.db.models import Count, F, Max, Q, Sum
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.cache import cache_page

from clientes.models import Cliente
from financeiro.models import Despesa
from pedidos.models import ItemPedido, Pedido
from produtos.models import Produto

from .forms import CustomUserCreationForm

logger = logging.getLogger(__name__)


@login_required
def index(request):
    return render(request, "core/index.html")


@login_required
@cache_page(60)  # Cache de 1 minuto para o dashboard
def dashboard(request):
    hoje = timezone.now().date()
    trinta_dias_atras = hoje - timezone.timedelta(days=30)
    sessenta_dias_atras = hoje - timezone.timedelta(days=60)
    um_ano_atras = hoje - timezone.timedelta(days=365)

    # 1. Dados financeiros (últimos 60 dias)
    pedidos_60d = (
        Pedido.objects.filter(data__gte=sessenta_dias_atras).exclude(status="C").prefetch_related("itens", "cupom")
    )
    total_receitas = sum(p.total for p in pedidos_60d)

    total_despesas = Despesa.objects.filter(data__gte=sessenta_dias_atras).aggregate(total=Sum("valor"))[
        "total"
    ] or Decimal("0.0")

    diferenca = total_receitas - total_despesas
    alerta_prejuizo = diferenca < 0

    # 2. Top clientes (frequência e valor)
    top_clientes_frequencia = (
        Cliente.objects.filter(pedido__data__gte=um_ano_atras)
        .annotate(frequencia=Count("pedido", filter=Q(pedido__data__gte=um_ano_atras)))
        .order_by("-frequencia")[:10]
        .values("id", "nome", "telefone", "frequencia")
    )

    top_clientes_valor = (
        Cliente.objects.filter(pedido__data__gte=sessenta_dias_atras)
        .annotate(total=Sum(F("pedido__itens__preco_unitario") * F("pedido__itens__quantidade")))
        .order_by("-total")[:10]
        .values("id", "nome", "telefone", "total")
    )

    max_cliente_valor = top_clientes_valor[0]["total"] if top_clientes_valor else Decimal("0.0")
    top_clientes_valor_list = [
        {**c, "porcentagem": int((c["total"] / max_cliente_valor * 100) if max_cliente_valor else 0)}
        for c in top_clientes_valor
    ]

    # 3. Clientes inativos
    clientes_com_pedidos_recentes = set(
        Pedido.objects.filter(data__gte=trinta_dias_atras).values_list("cliente_id", flat=True)
    )
    clientes_inativos = (
        Cliente.objects.filter(ativo=True)
        .exclude(id__in=clientes_com_pedidos_recentes)
        .annotate(ultimo_pedido=Max("pedido__data"))
        .filter(ultimo_pedido__isnull=False)
        .order_by("ultimo_pedido")[:10]
        .values("id", "nome", "telefone", "ultimo_pedido")
    )

    clientes_inativos_list = [{**c, "dias_sem_pedido": (hoje - c["ultimo_pedido"]).days} for c in clientes_inativos]

    # 4. Top produtos vendidos
    top_produtos_vendidos = (
        Produto.objects.filter(itempedido__pedido__data__gte=um_ano_atras)
        .annotate(
            qtd_total=Sum("itempedido__quantidade"),
            valor_total=Sum(F("itempedido__quantidade") * F("itempedido__preco_unitario")),
        )
        .order_by("-qtd_total")[:10]
        .values("id", "descricao", "estoque", "qtd_total", "valor_total")
    )

    max_qtd = top_produtos_vendidos[0]["qtd_total"] if top_produtos_vendidos else 0
    produtos_mais_vendidos_list = [
        {**p, "porcentagem": int((p["qtd_total"] / max_qtd * 100) if max_qtd else 0)} for p in top_produtos_vendidos
    ]

    # 5. Dados financeiros para gráfico (últimos 12 meses)
    from collections import defaultdict
    from datetime import datetime

    from django.db.models.functions import TruncMonth

    dados_mensais = defaultdict(lambda: {"receitas": 0, "despesas": 0})

    pedidos_ano = Pedido.objects.filter(data__gte=um_ano_atras).exclude(status="C").prefetch_related("itens", "cupom")
    for p in pedidos_ano:
        mes_str = p.data.strftime("%b/%Y")
        dados_mensais[mes_str]["receitas"] += float(p.total)

    despesas_q = (
        Despesa.objects.filter(data__gte=um_ano_atras, status="R")  # Apenas despesas realizadas
        .annotate(mes=TruncMonth("data"))
        .values("mes")
        .annotate(total=Sum("valor"))
    )

    for d in despesas_q:
        if d["mes"]:
            dados_mensais[d["mes"].strftime("%b/%Y")]["despesas"] = float(d["total"] or 0)

    # Ordena os dados por data para garantir a ordem correta no gráfico
    sorted_items = sorted(dados_mensais.items(), key=lambda item: datetime.strptime(item[0], "%b/%Y"))

    labels_meses = [item[0] for item in sorted_items]
    receitas_mensais = [item[1]["receitas"] for item in sorted_items]
    despesas_mensais = [item[1]["despesas"] for item in sorted_items]
    lucro_mensal = [item[1]["receitas"] - item[1]["despesas"] for item in sorted_items]

    # 6. Alerta de recompra de Sacolas (25-30 dias)
    periodo_inicio_alerta = hoje - timezone.timedelta(days=30)
    periodo_fim_alerta = hoje - timezone.timedelta(days=25)

    # Encontra os pedidos de sacola no período de alerta
    pedidos_alerta = (
        Pedido.objects.filter(
            data__range=[periodo_inicio_alerta, periodo_fim_alerta], itens__produto__categoria__nome__icontains="sacola"
        )
        .select_related("cliente")
        .distinct()
    )

    clientes_recompra = []
    clientes_processados = set()

    # Itera sobre os pedidos para encontrar o último pedido de cada cliente
    for pedido in pedidos_alerta.order_by("cliente_id", "-data"):
        cliente_id = pedido.cliente_id
        if cliente_id in clientes_processados:
            continue

        # Verifica se existe algum pedido mais recente para este cliente
        pedido_mais_recente = Pedido.objects.filter(cliente_id=cliente_id, data__gt=pedido.data).exists()

        # Se não houver pedido mais recente, o cliente está elegível para o alerta
        if not pedido_mais_recente:
            clientes_recompra.append(
                {
                    "id": pedido.cliente.id,
                    "nome": pedido.cliente.nome,
                    "telefone": pedido.cliente.telefone,
                    "ultimo_pedido": pedido.data,
                    "dias_desde_pedido": (hoje - pedido.data).days,
                }
            )
            clientes_processados.add(cliente_id)

    return render(
        request,
        "core/dashboard.html",
        {
            # Dados financeiros
            "total_receitas": total_receitas,
            "total_despesas": total_despesas,
            "diferenca": diferenca,
            "alerta_prejuizo": alerta_prejuizo,
            # Top clientes e produtos
            "top_clientes_valor": top_clientes_valor_list,
            "clientes_frequentes": top_clientes_frequencia,
            "clientes_inativos": clientes_inativos_list,
            "produtos_mais_vendidos": produtos_mais_vendidos_list,
            "clientes_recompra_sacola": clientes_recompra,
            # Dados para gráficos
            "labels_meses": labels_meses,
            "receitas_mensais": receitas_mensais,
            "despesas_mensais": despesas_mensais,
            "lucro_mensal": lucro_mensal,
        },
    )


def register(request):
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            try:
                user = form.save()
                login(request, user)
                messages.success(request, "Conta criada com sucesso! Bem-vindo ao sistema.")
                logger.info(f"Novo usuário registrado: {user.username}")
                return redirect("core:dashboard")
            except Exception as e:
                logger.error(f"Erro ao criar usuário: {str(e)}")
                messages.error(request, "Erro ao criar conta. Por favor, tente novamente.")
    else:
        form = CustomUserCreationForm()
    return render(request, "registration/register.html", {"form": form})
