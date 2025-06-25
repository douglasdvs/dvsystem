from django.db import models
from django.db.models import Max
from django.utils import timezone
import uuid
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings

# Mantemos as categorias antigas para compatibilidade
CATEGORIAS_PRODUTO = [
    ('camiseta', 'Camiseta'),
    ('caneca', 'Caneca'),
    ('sacola', 'Sacola'),
    ('brinde', 'Brinde'),
    ('outros', 'Outros'),
]

class CategoriaProduto(models.Model):
    nome = models.CharField(max_length=100, unique=True)
    descricao = models.TextField(blank=True, null=True)
    cor = models.CharField(max_length=20, default="#6c757d")  # Cor para uso na UI
    ativo = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.nome
    
    class Meta:
        verbose_name = "Categoria"
        verbose_name_plural = "Categorias"
        ordering = ['nome']

class MovimentoEstoque(models.Model):
    TIPO_CHOICES = (
        ('entrada', 'Entrada'),
        ('saida', 'Saída'),
        ('ajuste', 'Ajuste de Inventário'),
    )
    
    produto = models.ForeignKey('Produto', on_delete=models.CASCADE, related_name='movimentos')
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)
    quantidade = models.IntegerField()
    estoque_anterior = models.IntegerField()
    estoque_atual = models.IntegerField()
    observacao = models.TextField(blank=True, null=True)
    referencia = models.CharField(max_length=50, blank=True, null=True, help_text="Ex: Número do Pedido, NF")
    criado_por = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.get_tipo_display()} de {self.quantidade} unidades - {self.produto}"
    
    class Meta:
        verbose_name = "Movimento de Estoque"
        verbose_name_plural = "Movimentos de Estoque"
        ordering = ['-criado_em']

class HistoricoPreco(models.Model):
    produto = models.ForeignKey('Produto', on_delete=models.CASCADE, related_name='historico_precos')
    preco_custo_anterior = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    preco_custo_novo = models.DecimalField(max_digits=10, decimal_places=2)
    preco_venda_anterior = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    preco_venda_novo = models.DecimalField(max_digits=10, decimal_places=2)
    margem_anterior = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    margem_nova = models.DecimalField(max_digits=5, decimal_places=2)
    data_alteracao = models.DateTimeField(auto_now_add=True)
    alterado_por = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True)
    observacao = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"Alteração de preço em {self.data_alteracao.strftime('%d/%m/%Y')}"
    
    class Meta:
        verbose_name = "Histórico de Preço"
        verbose_name_plural = "Histórico de Preços"
        ordering = ['-data_alteracao']

class Produto(models.Model):
    codigo = models.CharField(max_length=10, unique=True, editable=False)
    codigo_barras = models.CharField(max_length=20, blank=True, null=True, unique=True, verbose_name="Código de Barras")
    descricao = models.CharField(max_length=255)
    categoria = models.ForeignKey(CategoriaProduto, on_delete=models.SET_NULL, null=True, blank=True, related_name='produtos')
    preco_custo = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    margem_lucro = models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(0)])
    preco_venda = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    despesas = models.DecimalField(max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    impostos = models.DecimalField(max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    estoque = models.IntegerField(default=0)
    estoque_minimo = models.IntegerField(default=5)
    unidade_medida = models.CharField(max_length=10, default="UN", verbose_name="Unidade de Medida")
    peso = models.DecimalField(max_digits=8, decimal_places=3, default=1, help_text="Peso em kg")
    ativo = models.BooleanField(default=True, verbose_name="Ativo")

    def clean(self):
        errors = {}
        if self.estoque is not None and self.estoque < 0:
            errors['estoque'] = 'O estoque não pode ser negativo.'
        if self.preco_venda is not None and self.preco_custo is not None and self.preco_venda < self.preco_custo:
            errors['preco_venda'] = 'O preço de venda não pode ser menor que o preço de custo.'
        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return f"{self.descricao}"

    def save(self, *args, **kwargs):
        if not self.codigo:
            # Busca o último código usado
            ultimo = Produto.objects.order_by('-codigo').first()
            if ultimo and ultimo.codigo:
                try:
                    # Tenta converter o último código para número e incrementa
                    ultimo_numero = int(ultimo.codigo)
                    proximo_codigo = str(ultimo_numero + 1).zfill(5)
                except ValueError:
                    # Se não conseguir converter, usa o ID
                    proximo_codigo = str((ultimo.id + 1) if ultimo else 1).zfill(5)
            else:
                # Se não houver produtos, começa com 1
                proximo_codigo = '00001'
            self.codigo = proximo_codigo
        super().save(*args, **kwargs)

    @property
    def estoque_baixo(self):
        """Verifica se o estoque está abaixo do mínimo"""
        return self.estoque <= self.estoque_minimo

    def notificar_estoque_baixo(self):
        """Envia notificação quando o estoque está baixo"""
        if self.estoque_baixo:
            subject = f'Alerta: Estoque baixo - {self.descricao}'
            message = f'O produto {self.descricao} (Código: {self.codigo}) está com estoque baixo.\n'
            message += f'Estoque atual: {self.estoque}\n'
            message += f'Estoque mínimo: {self.estoque_minimo}'
            
            # Envia email para os administradores
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [admin[1] for admin in settings.ADMINS],
                fail_silently=True,
            )

    class Meta:
        verbose_name = "Produto"
        verbose_name_plural = "Produtos"
        ordering = ['descricao']

@receiver(post_save, sender=Produto)
def notificar_estoque_baixo(sender, instance, **kwargs):
    """Signal para notificar quando o estoque estiver baixo"""
    instance.notificar_estoque_baixo()
