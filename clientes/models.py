from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models
from django.utils import timezone
from django.utils.text import slugify

from .utils import (
    formatar_cep,
    formatar_cpf_cnpj,
    formatar_telefone,
    validar_cep,
    validar_cpf_cnpj,
    validar_email,
    validar_telefone,
)

User = get_user_model()

UF_CHOICES = [
    ("AC", "Acre"),
    ("AL", "Alagoas"),
    ("AP", "Amapá"),
    ("AM", "Amazonas"),
    ("BA", "Bahia"),
    ("CE", "Ceará"),
    ("DF", "Distrito Federal"),
    ("ES", "Espírito Santo"),
    ("GO", "Goiás"),
    ("MA", "Maranhão"),
    ("MT", "Mato Grosso"),
    ("MS", "Mato Grosso do Sul"),
    ("MG", "Minas Gerais"),
    ("PA", "Pará"),
    ("PB", "Paraíba"),
    ("PR", "Paraná"),
    ("PE", "Pernambuco"),
    ("PI", "Piauí"),
    ("RJ", "Rio de Janeiro"),
    ("RN", "Rio Grande do Norte"),
    ("RS", "Rio Grande do Sul"),
    ("RO", "Rondônia"),
    ("RR", "Roraima"),
    ("SC", "Santa Catarina"),
    ("SP", "São Paulo"),
    ("SE", "Sergipe"),
    ("TO", "Tocantins"),
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

    nome = models.CharField("Nome", max_length=50, unique=True)
    slug = models.SlugField("Slug", max_length=50, unique=True, blank=True)
    cor = models.CharField("Cor", max_length=7, default="#000000", help_text="Cor em formato hexadecimal (ex: #FF0000)")
    descricao = models.TextField("Descrição", blank=True)
    criado_em = models.DateTimeField("Criado em", auto_now_add=True)
    atualizado_em = models.DateTimeField("Atualizado em", auto_now=True)

    class Meta:
        verbose_name = "Tag"
        verbose_name_plural = "Tags"
        ordering = ["nome"]

    def __str__(self):
        return self.nome

    def save(self, *args, **kwargs):
        if not self.slug:
            # pyrefly: ignore  # bad-assignment
            self.slug = slugify(self.nome)
        super().save(*args, **kwargs)

    def clean(self):
        super().clean()
        # Validar formato da cor
        # pyrefly: ignore  # missing-attribute, bad-argument-type
        if not self.cor.startswith("#") or len(self.cor) != 7:
            raise ValidationError({"cor": "Cor deve estar no formato hexadecimal (ex: #FF0000)"})


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
        "CPF/CNPJ", max_length=18, blank=True, null=True, help_text="Formato: 000.000.000-00 ou 00.000.000/0000-00"
    )
    nome = models.CharField("Nome", max_length=100)
    email = models.EmailField("E-mail", max_length=100, blank=True, null=True)
    telefone = models.CharField(
        "Telefone (WhatsApp)",
        max_length=15,
        help_text="Formato: (00) 00000-0000",
        validators=[RegexValidator(regex=r"^\(\d{2}\) \d{5}-\d{4}$", message="Formato válido: (00) 00000-0000")],
    )
    tipo_cliente = models.ForeignKey(
        TipoCliente, on_delete=models.SET_NULL, null=True, blank=True, related_name="clientes"
    )
    segmento = models.ForeignKey(Segmento, on_delete=models.SET_NULL, null=True, blank=True, related_name="clientes")
    ativo = models.BooleanField("Ativo", default=True)
    observacao = models.TextField("Observação", blank=True, null=True)
    data_cadastro = models.DateTimeField("Data de Cadastro", default=timezone.now)
    criado_por = models.ForeignKey(
        User, verbose_name="Criado por", on_delete=models.SET_NULL, null=True, editable=False
    )
    tags = models.ManyToManyField(Tag, verbose_name="Tags", blank=True, related_name="clientes")
    programa_fidelidade = models.ForeignKey(ProgramaFidelidade, on_delete=models.SET_NULL, null=True, blank=True)
    pontos_fidelidade = models.IntegerField(default=0)
    nome_loja = models.CharField("Nome da Loja", max_length=100, blank=True, null=True)

    def __str__(self):
        return self.nome

    def save(self, *args, **kwargs):
        # Força campos principais para maiúsculo
        if self.nome:
            # pyrefly: ignore  # missing-attribute
            self.nome = self.nome.upper()
        if self.nome_loja:
            # pyrefly: ignore  # missing-attribute
            self.nome_loja = self.nome_loja.upper()
        if self.email:
            # pyrefly: ignore  # missing-attribute
            self.email = self.email.upper()
        if not self.codigo:
            # pyrefly: ignore  # missing-attribute
            ultimo = Cliente.objects.order_by("-codigo").first()
            if ultimo and ultimo.codigo.isdigit():
                proximo_codigo = str(int(ultimo.codigo) + 1).zfill(5)
            else:
                proximo_codigo = "00001"
            # pyrefly: ignore  # bad-assignment
            self.codigo = proximo_codigo
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"
        ordering = ["nome"]
        indexes = [
            models.Index(fields=["nome"]),
            models.Index(fields=["cpf_cnpj"]),
            models.Index(fields=["email"]),
            models.Index(fields=["ativo"]),
            models.Index(fields=["data_cadastro"]),
        ]

    def clean(self):
        super().clean()
        if self.cpf_cnpj:
            # pyrefly: ignore  # bad-argument-type
            valido, tipo = validar_cpf_cnpj(self.cpf_cnpj)
            if not valido:
                raise ValidationError({"cpf_cnpj": f"{tipo} inválido"})

        # pyrefly: ignore  # bad-argument-type
        if self.telefone and not validar_telefone(self.telefone):
            raise ValidationError({"telefone": "Telefone inválido"})

        # pyrefly: ignore  # bad-argument-type
        if self.email and not validar_email(self.email):
            raise ValidationError({"email": "Email inválido"})

    @property
    def telefone_formatado(self):
        if not self.telefone:
            return ""
        # pyrefly: ignore  # bad-argument-type
        return formatar_telefone(self.telefone)

    @property
    def cpf_cnpj_formatado(self):
        if not self.cpf_cnpj:
            return ""
        # pyrefly: ignore  # bad-argument-type
        return formatar_cpf_cnpj(self.cpf_cnpj)

    def get_ultima_compra(self):
        """Retorna a data da última compra do cliente."""
        try:
            from pedidos.models import Pedido

            ultimo_pedido = (
                Pedido.objects.filter(cliente=self, status__in=["P", "E", "F"])  # Pendente, Em produção, Finalizado
                .order_by("-data")
                .first()
            )
            return ultimo_pedido.data if ultimo_pedido else None
        except ImportError:
            # Módulo de pedidos não disponível
            return None

    def get_total_compras(self):
        """Retorna o número total de compras do cliente."""
        try:
            from pedidos.models import Pedido

            return Pedido.objects.filter(
                cliente=self, status__in=["P", "E", "F"]  # Pendente, Em produção, Finalizado
            ).count()
        except ImportError:
            # Módulo de pedidos não disponível
            return 0

    def get_valor_total_compras(self):
        """Retorna o valor total de todas as compras do cliente."""
        try:
            from django.db.models import Sum

            from pedidos.models import Pedido

            pedidos = Pedido.objects.filter(
                cliente=self, status__in=["P", "E", "F"]  # Pendente, Em produção, Finalizado
            )

            total = sum(pedido.total for pedido in pedidos)
            return total if total else Decimal("0.00")
        except ImportError:
            # Módulo de pedidos não disponível
            return Decimal("0.00")

    @property
    def endereco_completo(self):
        """Retorna o endereço completo do primeiro endereço cadastrado."""
        # pyrefly: ignore  # missing-attribute
        primeiro_endereco = self.enderecos.first()
        if primeiro_endereco:
            return str(primeiro_endereco)
        return "Nenhum endereço cadastrado"

    def get_tags_por_cor(self):
        """Retorna as tags agrupadas por cor."""
        return {
            tag.cor: tag.nome
            # pyrefly: ignore  # missing-attribute
            for tag in self.tags.all()
        }

    def adicionar_tag(self, tag):
        """Adiciona uma tag ao cliente."""
        # pyrefly: ignore  # missing-attribute
        self.tags.add(tag)

    def remover_tag(self, tag):
        """Remove uma tag do cliente."""
        # pyrefly: ignore  # missing-attribute
        self.tags.remove(tag)

    def tem_tag(self, tag):
        """Verifica se o cliente tem uma determinada tag."""
        # pyrefly: ignore  # missing-attribute
        return self.tags.filter(id=tag.id).exists()

    def adicionar_pontos(self, valor_compra):
        """Adiciona pontos de fidelidade baseado no valor da compra"""
        # pyrefly: ignore  # missing-attribute
        if self.programa_fidelidade and self.programa_fidelidade.ativo:
            # pyrefly: ignore  # missing-attribute
            pontos = int(valor_compra * self.programa_fidelidade.pontos_por_real)
            # pyrefly: ignore  # bad-assignment, bad-argument-type
            self.pontos_fidelidade += pontos
            self.save()
            return pontos
        return 0

    def resgatar_pontos(self, pontos):
        """Resgata pontos de fidelidade por desconto"""
        # pyrefly: ignore  # missing-attribute
        if not self.programa_fidelidade or not self.programa_fidelidade.ativo:
            return 0

        # pyrefly: ignore  # missing-attribute
        if pontos < self.programa_fidelidade.pontos_minimos_resgate:
            # pyrefly: ignore  # missing-attribute
            raise ValidationError(f"Mínimo de {self.programa_fidelidade.pontos_minimos_resgate} pontos para resgate")

        if pontos > self.pontos_fidelidade:
            raise ValidationError("Pontos insuficientes")

        # pyrefly: ignore  # missing-attribute
        valor_desconto = pontos * self.programa_fidelidade.valor_por_ponto
        self.pontos_fidelidade -= pontos
        self.save()
        return valor_desconto

    @property
    def valor_disponivel_resgate(self):
        """Retorna o valor disponível para resgate em pontos"""
        # pyrefly: ignore  # missing-attribute
        if not self.programa_fidelidade or not self.programa_fidelidade.ativo:
            return Decimal("0.00")
        # pyrefly: ignore  # missing-attribute
        return self.pontos_fidelidade * self.programa_fidelidade.valor_por_ponto


class Endereco(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name="enderecos")
    cep = models.CharField("CEP", max_length=9)
    logradouro = models.CharField("Logradouro", max_length=255)
    numero = models.CharField("Número", max_length=10)
    complemento = models.CharField("Complemento", max_length=100, blank=True, null=True)
    bairro = models.CharField("Bairro", max_length=100)
    cidade = models.CharField("Cidade", max_length=100)
    uf = models.CharField("UF", max_length=2, choices=UF_CHOICES)

    def clean(self):
        super().clean()
        # pyrefly: ignore  # bad-argument-type
        if self.cep and not validar_cep(self.cep):
            raise ValidationError({"cep": "CEP inválido"})

    @property
    def cep_formatado(self):
        if not self.cep:
            return ""
        # pyrefly: ignore  # bad-argument-type
        return formatar_cep(self.cep)

    def __str__(self):
        endereco_str = f"{self.logradouro}, {self.numero}"
        if self.complemento:
            endereco_str += f", {self.complemento}"
        return f"{endereco_str} - {self.bairro}, {self.cidade} - {self.uf}"
