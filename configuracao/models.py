from django.db import models
from django.contrib.auth.models import Group

class ConfiguracaoSistema(models.Model):
    nome_sistema = models.CharField(max_length=100, default='Meu Sistema')
    tema_primario = models.CharField(max_length=100, default='azul') 
    tema_secundario = models.CharField(max_length=7, default='#6dd5ed')
    email_suporte = models.EmailField(blank=True, null=True)
    logo = models.ImageField(upload_to='configuracao/', blank=True, null=True)
    data_atualizacao = models.DateTimeField(auto_now=True)

class Empresa(models.Model):
    razao_social = models.CharField(max_length=100)
    cnpj = models.CharField(max_length=18)
    endereco = models.CharField(max_length=200)
    telefone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    logo = models.ImageField(upload_to='empresa/', blank=True, null=True)

class PermissaoCustomizada(models.Model):
    nome = models.CharField(max_length=100)
    codigo = models.CharField(max_length=50, unique=True)
    grupos = models.ManyToManyField(Group, blank=True)
    descricao = models.TextField(blank=True)

class ModeloImpressao(models.Model):
    nome = models.CharField(max_length=100)
    tipo = models.CharField(max_length=50, choices=[('pedido', 'Pedido'), ('orcamento', 'Orçamento'), ('nf', 'Nota Fiscal')])
    template_html = models.TextField()
    criado_em = models.DateTimeField(auto_now_add=True)

class Integracao(models.Model):
    nome = models.CharField(max_length=100)
    tipo = models.CharField(max_length=50, choices=[('ipi', 'IPI'), ('email', 'E-mail'), ('melhor_envio', 'Melhor Envio')])
    api_key = models.CharField(max_length=200, blank=True)
    endpoint = models.CharField(max_length=200, blank=True)
    usuario = models.CharField(max_length=100, blank=True)
    senha = models.CharField(max_length=100, blank=True)
    parametros = models.JSONField(blank=True, null=True)
    ativo = models.BooleanField(default=True)
    atualizado_em = models.DateTimeField(auto_now=True)
