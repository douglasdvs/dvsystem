from django.contrib.auth.models import User
from django.db import models

from clientes.models import Cliente
from pedidos.models import Pedido

CATEGORIAS_DESPESA = [
    ("devolucao", "Devolução"),
    ("fornecedor", "Fornecedor"),
    ("marketing", "Marketing"),
    ("operacional", "Operacional"),
    ("administrativo", "Administrativo"),
    ("impostos", "Impostos"),
    ("outros", "Outros"),
]

CATEGORIAS_RECEITA = [
    ("pedido", "Venda de Pedido"),
    ("servico", "Prestação de Serviços"),
    ("outros", "Outros"),
]

STATUS_CHOICES = [
    ("P", "Pendente"),
    ("R", "Realizado"),
    ("C", "Cancelado"),
]

FORMA_PAGAMENTO = [
    ("dinheiro", "Dinheiro"),
    ("pix", "PIX"),
    ("debito", "Cartão Débito"),
    ("credito", "Cartão Crédito"),
    ("transferencia", "Transferência"),
    ("boleto", "Boleto"),
    ("cheque", "Cheque"),
]


class CentroCusto(models.Model):
    """Centro de custos para melhor organização financeira"""

    nome = models.CharField(max_length=100)
    descricao = models.TextField(blank=True)
    ativo = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Centro de Custo"
        verbose_name_plural = "Centros de Custo"

    def __str__(self):
        return self.nome

    def save(self, *args, **kwargs):
        if self.nome:
            self.nome = self.nome.upper()
        super().save(*args, **kwargs)

    @property
    def total_despesas(self):
        return self.despesa_set.count()


class Despesa(models.Model):
    descricao = models.CharField(max_length=255)
    data = models.DateField()
    data_vencimento = models.DateField(null=True, blank=True, help_text="Data de vencimento para contas a pagar")
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    categoria = models.CharField(max_length=20, choices=CATEGORIAS_DESPESA)
    centro_custo = models.ForeignKey(CentroCusto, on_delete=models.SET_NULL, null=True, blank=True)
    forma_pagamento = models.CharField(max_length=20, choices=FORMA_PAGAMENTO, default="dinheiro")
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default="P")
    observacoes = models.TextField(blank=True)
    anexo = models.FileField(upload_to="financeiro/anexos/", null=True, blank=True)
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Despesa"
        verbose_name_plural = "Despesas"
        ordering = ["-data"]
        indexes = [
            models.Index(fields=["data"]),
            models.Index(fields=["categoria"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return f"Despesa: {self.descricao} - R$ {self.valor}"

    @property
    def em_atraso(self):
        """Verifica se a despesa está em atraso"""
        from django.utils import timezone

        return self.status == "P" and self.data_vencimento and self.data_vencimento < timezone.now().date()


class Receita(models.Model):
    descricao = models.CharField(max_length=255)
    data = models.DateField()
    data_vencimento = models.DateField(null=True, blank=True, help_text="Data de vencimento para contas a receber")
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    categoria = models.CharField(max_length=20, choices=CATEGORIAS_RECEITA)
    cliente = models.ForeignKey(Cliente, on_delete=models.SET_NULL, null=True, blank=True)
    pedido = models.ForeignKey(
        Pedido, on_delete=models.SET_NULL, null=True, blank=True, help_text="Pedido relacionado a esta receita"
    )
    forma_pagamento = models.CharField(max_length=20, choices=FORMA_PAGAMENTO, default="dinheiro")
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default="P")
    observacoes = models.TextField(blank=True)
    anexo = models.FileField(upload_to="financeiro/anexos/", null=True, blank=True)
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Receita"
        verbose_name_plural = "Receitas"
        ordering = ["-data"]

    def __str__(self):
        return f"Receita: {self.descricao} - R$ {self.valor}"

    @property
    def em_atraso(self):
        """Verifica se a receita está em atraso"""
        from django.utils import timezone

        return self.status == "P" and self.data_vencimento and self.data_vencimento < timezone.now().date()


class FluxoCaixa(models.Model):
    """Registro do fluxo de caixa diário"""

    data = models.DateField(unique=True)
    saldo_inicial = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    entradas = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    saidas = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    saldo_final = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Fluxo de Caixa"
        verbose_name_plural = "Fluxo de Caixa"
        ordering = ["-data"]

    def __str__(self):
        return f"Fluxo {self.data} - Saldo: R$ {self.saldo_final}"

    def calcular_saldo_final(self):
        """Calcula o saldo final do dia"""
        self.saldo_final = self.saldo_inicial + self.entradas - self.saidas
        return self.saldo_final
