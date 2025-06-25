from django.db import models
from django.db.models import Max, Sum
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import datetime, timedelta
from clientes.models import Cliente
from produtos.models import Produto
from django.core.exceptions import ValidationError
from decimal import Decimal

User = get_user_model()

class Pedido(models.Model):
    STATUS_CHOICES = [
        ('P', 'Pendente'),
        ('A', 'Aprovado'),
        ('E', 'Enviado'),
        ('T', 'Entregue'),
        ('D', 'Devolução'),
        ('R', 'Reenviar'),
        ('C', 'Cancelado'),
    ]
    
    PRIORIDADE_CHOICES = [
        ('B', 'Baixa'),
        ('N', 'Normal'),
        ('A', 'Alta'),
        ('U', 'Urgente'),
    ]
    
    FORMA_PAGAMENTO_CHOICES = [
        ('pix', 'PIX'),
        ('cartao_credito', 'Cartão Crédito'),
    ]
    
    VENDEDORES_CHOICES = [
        ('Douglas', 'Douglas'),
        ('Jussara', 'Jussara'),
    ]

    # Informações básicas
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    data = models.DateField(auto_now_add=True)
    codigo = models.CharField(max_length=20, blank=True, unique=True, editable=False)
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='P')
    prioridade = models.CharField(max_length=1, choices=PRIORIDADE_CHOICES, default='N')
    
    # Valores
    desconto = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    taxa_entrega = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    
    # Pessoal
    vendedor = models.CharField(max_length=20, choices=VENDEDORES_CHOICES)
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Pagamento e entrega
    forma_pagamento = models.CharField(max_length=20, choices=FORMA_PAGAMENTO_CHOICES, default='pix')
    data_entrega_prevista = models.DateField(null=True, blank=True)
    data_entrega_realizada = models.DateField(null=True, blank=True)
    
    # Arte
    arquivo_arte = models.FileField(
        upload_to='pedidos/artes/',
        null=True, blank=True,
        help_text='JPG, PNG ou PDF até 2MB'
    )
    arte_aprovada = models.BooleanField(default=False, help_text='Arte aprovada pelo cliente?')
    data_arte_aprovada = models.DateTimeField(null=True, blank=True)
    arquivo_arte_aprovada = models.FileField(upload_to='pedidos/artes_aprovadas/', null=True, blank=True)
    observacoes_arte = models.TextField(blank=True, help_text='Observações do cliente sobre a arte')
    
    # Observações
    observacoes = models.TextField(blank=True)
    observacoes_internas = models.TextField(blank=True, help_text='Observações internas (não aparece no pedido)')

    # Pagamento
    valor_sinal = models.DecimalField(max_digits=8, decimal_places=2, default=0, help_text='Valor do sinal (60%)')
    valor_restante = models.DecimalField(max_digits=8, decimal_places=2, default=0, help_text='Valor restante (40%)')
    valor_recebido = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text='Valor recebido do cliente')
    sinal_pago = models.BooleanField(default=False)
    data_sinal_pago = models.DateTimeField(null=True, blank=True)
    restante_pago = models.BooleanField(default=False)
    data_restante_pago = models.DateTimeField(null=True, blank=True)

    # Envio
    FORMA_ENVIO_CHOICES = [
        ('correios', 'Correios'),
        ('loggi', 'LOGGI'),
        ('uber', 'Uber'),
        ('proprio', 'Entrega Própria'),
    ]
    forma_envio = models.CharField(max_length=20, choices=FORMA_ENVIO_CHOICES, blank=True)
    codigo_rastreio = models.CharField(max_length=50, blank=True)
    data_envio = models.DateTimeField(null=True, blank=True)
    data_entrega = models.DateTimeField(null=True, blank=True)
    
    # Controle
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)
    
    cupom = models.ForeignKey('CupomDesconto', on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        verbose_name = 'Pedido'
        verbose_name_plural = 'Pedidos'
        ordering = ['-criado_em']

    def save(self, *args, **kwargs):
        from decimal import Decimal

        primeira = self.pk is None
        if not self.codigo:
            ultimo = Pedido.objects.aggregate(max_num=Max('id'))['max_num']
            proximo = (ultimo + 1) if ultimo else 1
            self.codigo = f'PED-{str(proximo).zfill(5)}'

        super().save(*args, **kwargs)

        if not primeira and self.itens.exists():
            total = self.total
            self.valor_sinal = (total * Decimal('0.6')).quantize(Decimal('0.01'))
            self.valor_restante = (total - self.valor_sinal).quantize(Decimal('0.01'))
            super().save(update_fields=['valor_sinal', 'valor_restante'])



    @property
    def subtotal(self):
        return sum(item.quantidade * item.preco_unitario for item in self.itens.all())
    
    @property
    def total(self):
        return self.subtotal - self.desconto - self.desconto_cupom + self.taxa_entrega
    
    @property
    def total_itens(self):
        return sum(item.quantidade for item in self.itens.all())
    
    @property
    def dias_ate_entrega(self):
        if not self.data_entrega_prevista:
            return None
        return (self.data_entrega_prevista - timezone.now().date()).days
    
    @property
    def entrega_em_atraso(self):
        if not self.data_entrega_prevista or self.data_entrega_realizada:
            return False
        return (self.status not in ['T', 'C'] and 
                self.data_entrega_prevista < timezone.now().date())
    
    @property
    def cor_status(self):
        cores = {
            'P': 'warning', 'A': 'info', 'E': 'primary',
            'T': 'success', 'D': 'danger', 'R': 'warning',
            'C': 'danger'
        }
        return cores.get(self.status, 'secondary')
    
    @property
    def cor_prioridade(self):
        cores = {'B': 'secondary', 'N': 'primary', 'A': 'warning', 'U': 'danger'}
        return cores.get(self.prioridade, 'primary')
    
    def pode_ser_editado(self):
        return self.status in ['P', 'A']
    
    def pode_ser_cancelado(self):
        return self.status not in ['T', 'C']
    
    def proximo_status_disponivel(self):
        fluxo = {
            'P': ['A','R','E','T','C'],
            'A': ['E','T','C'],
            'E': ['T','D','P'],
            'D': ['P','R','C'],
            'R': ['T','C'],
            'C': [], 'T': []
        }
        return fluxo.get(self.status, [])

    def get_status_display_from_code(self, code):
        """Retorna o label do status a partir do código."""
        return dict(self.STATUS_CHOICES).get(code, code)

    def __str__(self):
        return f"Pedido #{self.codigo} - {self.cliente.nome}"
    
    @property
    def valor_total(self):
        return sum(item.valor_total for item in self.itens.all())

    @property
    def valor_pendente(self):
        return self.valor_total - (self.valor_sinal or 0)

    def aplicar_cupom(self, codigo_cupom):
        from .models import CupomDesconto
        cupom = CupomDesconto.objects.get(codigo=codigo_cupom)
        if not cupom.esta_valido():
            raise ValidationError('Cupom inválido ou expirado')
        if self.subtotal < cupom.valor_minimo_pedido:
            raise ValidationError(f'Valor mínimo: R$ {cupom.valor_minimo_pedido}')
        self.cupom = cupom
        self.save()
        return cupom.calcular_desconto(self.subtotal)

    @property
    def desconto_cupom(self):
        if not self.cupom:
            return 0
        return self.cupom.calcular_desconto(self.subtotal)


class ItemPedido(models.Model):
    pedido = models.ForeignKey(Pedido, related_name='itens', on_delete=models.CASCADE)
    produto = models.ForeignKey(Produto, on_delete=models.PROTECT)
    quantidade = models.PositiveIntegerField(default=1)
    preco_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    desconto_item = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    observacoes = models.TextField(blank=True)

    @property
    def subtotal(self):
        return (self.quantidade * self.preco_unitario) - self.desconto_item
    
    @property
    def desconto_percentual(self):
        valor_total = self.quantidade * self.preco_unitario
        return (self.desconto_item / valor_total * 100) if valor_total else 0

    @property
    def valor_total(self):
        return self.quantidade * self.preco_unitario

    def __str__(self):
        return f"{self.quantidade}x {self.produto.descricao}"


class HistoricoPedido(models.Model):
    TIPO_CHOICES = [
        ('criacao', 'Criação'), ('edicao', 'Edição'),
        ('status', 'Mudança de Status'), ('cancelamento', 'Cancelamento'),
        ('observacao', 'Observação'),
    ]
    pedido = models.ForeignKey(Pedido, related_name='historico', on_delete=models.CASCADE)
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    status_anterior = models.CharField(max_length=1, choices=Pedido.STATUS_CHOICES, null=True, blank=True)
    status_novo = models.CharField(max_length=1, choices=Pedido.STATUS_CHOICES, null=True, blank=True)
    descricao = models.TextField()
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    data = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-data']

    def __str__(self):
        return f"{self.pedido.codigo} - {self.get_tipo_display()} - {self.data:%d/%m/%Y %H:%M}"


class AnexoPedido(models.Model):
    pedido = models.ForeignKey(Pedido, related_name='anexos', on_delete=models.CASCADE)
    arquivo = models.FileField(upload_to='pedidos/anexos/')
    descricao = models.CharField(max_length=255, blank=True)
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-criado_em']

    def __str__(self):
        return f"{self.pedido.codigo} - {self.descricao or 'Anexo'}"


class CupomDesconto(models.Model):
    TIPO_CHOICES = [('percentual', 'Percentual'), ('valor', 'Valor Fixo')]

    codigo = models.CharField(max_length=20, unique=True)
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    data_inicio = models.DateTimeField()
    data_fim = models.DateTimeField()
    quantidade_maxima = models.IntegerField(default=1)
    quantidade_usada = models.IntegerField(default=0)
    valor_minimo_pedido = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    ativo = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.codigo} - {self.get_tipo_display()}"

    def clean(self):
        if self.data_fim <= self.data_inicio:
            raise ValidationError('Data de fim deve ser posterior à de início')
        if self.tipo == 'percentual' and self.valor > 100:
            raise ValidationError('Desconto percentual não pode exceder 100%')

    def esta_valido(self):
        agora = timezone.now()
        return (
            self.ativo and
            self.data_inicio <= agora <= self.data_fim and
            self.quantidade_usada < self.quantidade_maxima
        )

    def calcular_desconto(self, valor_pedido):
        if not self.esta_valido() or valor_pedido < self.valor_minimo_pedido:
            return 0
        if self.tipo == 'percentual':
            return valor_pedido * (self.valor / 100)
        return min(self.valor, valor_pedido)
