from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.utils.text import slugify
from .utils import (
    validar_cpf_cnpj, formatar_cpf_cnpj,
    validar_telefone, formatar_telefone,
    validar_email, validar_cep, formatar_cep
)
from decimal import Decimal

User = get_user_model()

UF_CHOICES = [
    ('AC', 'Acre'), ('AL', 'Alagoas'), ('AP', 'Amapá'), ('AM', 'Amazonas'),
    ('BA', 'Bahia'), ('CE', 'Ceará'), ('DF', 'Distrito Federal'), ('ES', 'Espírito Santo'),
    ('GO', 'Goiás'), ('MA', 'Maranhão'), ('MT', 'Mato Grosso'), ('MS', 'Mato Grosso do Sul'),
    ('MG', 'Minas Gerais'), ('PA', 'Pará'), ('PB', 'Paraíba'), ('PR', 'Paraná'),
    ('PE', 'Pernambuco'), ('PI', 'Piauí'), ('RJ', 'Rio de Janeiro'), ('RN', 'Rio Grande do Norte'),
    ('RS', 'Rio Grande do Sul'), ('RO', 'Rondônia'), ('RR', 'Roraima'), ('SC', 'Santa Catarina'),
    ('SP', 'São Paulo'), ('SE', 'Sergipe'), ('TO', 'Tocantins')
]

class Segmento(models.Model):
    nome = models.CharField(max_length=100, unique=True)
    descricao = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.nome

    class Meta:
        verbose_name = "Segmento"
        verbose_name_plural = "Segmentos"

class TipoCliente(models.Model):
    nome = models.CharField(max_length=100, unique=True)
    descricao = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return self.nome
    
    class Meta:
        verbose_name = "Tipo de Cliente"
        verbose_name_plural = "Tipos de Cliente"

class Tag(models.Model):
    """Modelo para tags de clientes."""
    
    nome = models.CharField('Nome', max_length=50, unique=True)
    slug = models.SlugField('Slug', max_length=50, unique=True, blank=True)
    cor = models.CharField('Cor', max_length=7, default='#000000',
                          help_text='Cor em formato hexadecimal (ex: #FF0000)')
    descricao = models.TextField('Descrição', blank=True)
    criado_em = models.DateTimeField('Criado em', auto_now_add=True)
    atualizado_em = models.DateTimeField('Atualizado em', auto_now=True)
    
    class Meta:
        verbose_name = 'Tag'
        verbose_name_plural = 'Tags'
        ordering = ['nome']
    
    def __str__(self):
        return self.nome
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nome)
        super().save(*args, **kwargs)
    
    def clean(self):
        super().clean()
        # Validar formato da cor
        if not self.cor.startswith('#') or len(self.cor) != 7:
            raise ValidationError({
                'cor': 'Cor deve estar no formato hexadecimal (ex: #FF0000)'
            })

class ProgramaFidelidade(models.Model):
    nome = models.CharField(max_length=100)
    pontos_por_real = models.DecimalField(max_digits=5, decimal_places=2, default=1.0)
    valor_por_ponto = models.DecimalField(max_digits=5, decimal_places=2, default=0.01)
    pontos_minimos_resgate = models.IntegerField(default=100)
    ativo = models.BooleanField(default=True)
    
    def __str__(self):
        return self.nome

class Cliente(models.Model):
    codigo = models.CharField(max_length=10, editable=False, blank=True, unique=True)
    cpf_cnpj = models.CharField(
        "CPF/CNPJ",
        max_length=18,
        blank=True,
        null=True,
        help_text="Formato: 000.000.000-00 ou 00.000.000/0000-00"
    )
    nome = models.CharField("Nome", max_length=100)
    email = models.EmailField("E-mail", max_length=100, blank=True, null=True)
    telefone = models.CharField(
        "Telefone (WhatsApp)",
        max_length=15,
        help_text="Formato: (00) 00000-0000",
        validators=[RegexValidator(regex=r'^\(\d{2}\) \d{5}-\d{4}$', message='Formato válido: (00) 00000-0000')]
    )
    cep = models.CharField("CEP", max_length=9)
    endereco = models.CharField("Endereço", max_length=255)
    numero = models.CharField("Número", max_length=10)
    complemento = models.CharField("Complemento", max_length=100, blank=True, null=True)
    bairro = models.CharField("Bairro", max_length=100)
    cidade = models.CharField("Cidade", max_length=100)
    uf = models.CharField("UF", max_length=2, choices=UF_CHOICES)
    tipo_cliente = models.ForeignKey(TipoCliente, on_delete=models.SET_NULL, null=True, blank=True, related_name='clientes')
    segmento = models.ForeignKey(Segmento, on_delete=models.SET_NULL, null=True, blank=True, related_name='clientes')
    ativo = models.BooleanField("Ativo", default=True)
    observacao = models.TextField("Observação", blank=True, null=True)
    data_cadastro = models.DateTimeField("Data de Cadastro", default=timezone.now)
    criado_por = models.ForeignKey(
        User,
        verbose_name="Criado por",
        on_delete=models.SET_NULL,
        null=True,
        editable=False
    )
    tags = models.ManyToManyField(
        Tag,
        verbose_name='Tags',
        blank=True,
        related_name='clientes'
    )
    programa_fidelidade = models.ForeignKey(ProgramaFidelidade, on_delete=models.SET_NULL, null=True, blank=True)
    pontos_fidelidade = models.IntegerField(default=0)

    def __str__(self):
        return self.nome

    def save(self, *args, **kwargs):
        if not self.codigo:
            ultimo = Cliente.objects.order_by('-id').first()
            proximo_codigo = str((ultimo.id + 1) if ultimo else 1).zfill(5)
            self.codigo = proximo_codigo
        super().save(*args, **kwargs)
    
    class Meta:
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"
        ordering = ['nome']
        indexes = [
            models.Index(fields=['nome']),
            models.Index(fields=['cpf_cnpj']),
            models.Index(fields=['email']),
            models.Index(fields=['ativo']),
            models.Index(fields=['data_cadastro']),
        ]

    def clean(self):
        super().clean()
        if self.cpf_cnpj:
            valido, tipo = validar_cpf_cnpj(self.cpf_cnpj)
            if not valido:
                raise ValidationError({
                    'cpf_cnpj': f'{tipo} inválido'
                })
        
        if self.telefone and not validar_telefone(self.telefone):
            raise ValidationError({
                'telefone': 'Telefone inválido'
            })
        
        if self.email and not validar_email(self.email):
            raise ValidationError({
                'email': 'Email inválido'
            })

    @property
    def telefone_formatado(self):
        if not self.telefone:
            return ''
        return formatar_telefone(self.telefone)

    @property
    def cpf_cnpj_formatado(self):
        if not self.cpf_cnpj:
            return ''
        return formatar_cpf_cnpj(self.cpf_cnpj)

    def get_ultima_compra(self):
        # TODO: Implementar quando tiver o módulo de vendas
        return None

    def get_total_compras(self):
        # TODO: Implementar quando tiver o módulo de vendas
        return 0

    def get_valor_total_compras(self):
        # TODO: Implementar quando tiver o módulo de vendas
        return 0

    @property
    def endereco_completo(self):
        """Retorna o endereço completo do cliente"""
        parts = [self.endereco]
        if self.numero:
            parts.append(f"nº {self.numero}")
        if self.complemento:
            parts.append(f"- {self.complemento}")
        parts.append(f"- {self.bairro}")
        parts.append(f"- {self.cidade}/{self.uf}")
        parts.append(f"- CEP: {self.cep}")
        return ", ".join(parts)

    def get_tags_por_cor(self):
        """Retorna as tags agrupadas por cor."""
        return {
            tag.cor: tag.nome
            for tag in self.tags.all()
        }
    
    def adicionar_tag(self, tag):
        """Adiciona uma tag ao cliente."""
        self.tags.add(tag)
    
    def remover_tag(self, tag):
        """Remove uma tag do cliente."""
        self.tags.remove(tag)
    
    def tem_tag(self, tag):
        """Verifica se o cliente tem uma determinada tag."""
        return self.tags.filter(id=tag.id).exists()

    def adicionar_pontos(self, valor_compra):
        """Adiciona pontos de fidelidade baseado no valor da compra"""
        if self.programa_fidelidade and self.programa_fidelidade.ativo:
            pontos = int(valor_compra * self.programa_fidelidade.pontos_por_real)
            self.pontos_fidelidade += pontos
            self.save()
            return pontos
        return 0
    
    def resgatar_pontos(self, pontos):
        """Resgata pontos de fidelidade por desconto"""
        if not self.programa_fidelidade or not self.programa_fidelidade.ativo:
            return 0
        
        if pontos < self.programa_fidelidade.pontos_minimos_resgate:
            raise ValidationError(f'Mínimo de {self.programa_fidelidade.pontos_minimos_resgate} pontos para resgate')
        
        if pontos > self.pontos_fidelidade:
            raise ValidationError('Pontos insuficientes')
        
        valor_desconto = pontos * self.programa_fidelidade.valor_por_ponto
        self.pontos_fidelidade -= pontos
        self.save()
        return valor_desconto
    
    @property
    def valor_disponivel_resgate(self):
        """Retorna o valor disponível para resgate em pontos"""
        if not self.programa_fidelidade or not self.programa_fidelidade.ativo:
            return Decimal('0.00')
        return self.pontos_fidelidade * self.programa_fidelidade.valor_por_ponto

class Endereco(models.Model):
    cep = models.CharField("CEP", max_length=9)
    logradouro = models.CharField("Logradouro", max_length=255)
    numero = models.CharField("Número", max_length=10)
    complemento = models.CharField("Complemento", max_length=100, blank=True, null=True)
    bairro = models.CharField("Bairro", max_length=100)
    cidade = models.CharField("Cidade", max_length=100)
    uf = models.CharField("UF", max_length=2, choices=UF_CHOICES)

    def clean(self):
        super().clean()
        if self.cep and not validar_cep(self.cep):
            raise ValidationError({
                'cep': 'CEP inválido'
            })

    @property
    def cep_formatado(self):
        if not self.cep:
            return ''
        return formatar_cep(self.cep)

    def __str__(self):
        endereco_str = f"{self.logradouro}, {self.numero}"
        if self.complemento:
            endereco_str += f" - {self.complemento}"
        return endereco_str
