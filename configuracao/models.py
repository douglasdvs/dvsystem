from django.contrib.auth.models import Group
from django.db import models


class ConfiguracaoSistema(models.Model):
    nome_empresa = models.CharField(max_length=100, default="Minha Empresa")
    cnpj = models.CharField(max_length=18, blank=True, null=True)
    endereco = models.CharField(max_length=200, blank=True, null=True)
    telefone = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    site = models.CharField(max_length=100, blank=True, null=True)
    instagram = models.CharField(max_length=100, blank=True, null=True)
    facebook = models.CharField(max_length=100, blank=True, null=True)
    whatsapp = models.CharField(max_length=100, blank=True, null=True)
    cor_primaria = models.CharField(max_length=20, blank=True, null=True, default="#2193b0")
    cor_secundaria = models.CharField(max_length=20, blank=True, null=True, default="#6dd5ed")
    cor_sucesso = models.CharField(max_length=20, blank=True, null=True, default="#28a745")
    cor_perigo = models.CharField(max_length=20, blank=True, null=True, default="#dc3545")
    cor_alerta = models.CharField(max_length=20, blank=True, null=True, default="#ffc107")
    cor_info = models.CharField(max_length=20, blank=True, null=True, default="#17a2b8")
    smtp_host = models.CharField(max_length=100, blank=True, null=True)
    smtp_port = models.IntegerField(blank=True, null=True)
    smtp_usuario = models.CharField(max_length=100, blank=True, null=True)
    smtp_senha = models.CharField(max_length=100, blank=True, null=True)
    email_remetente = models.EmailField(blank=True, null=True)
    api_melhor_envio_token = models.CharField(max_length=200, blank=True, null=True)
    api_melhor_envio_sandbox = models.BooleanField(blank=True, null=True)
    modelo_pedido = models.CharField(max_length=100, blank=True, null=True)
    modelo_orcamento = models.CharField(max_length=100, blank=True, null=True)
    descricao_sistema = models.CharField(max_length=200, blank=True, null=True)
    versao_sistema = models.CharField(max_length=20, blank=True, null=True)
    usar_tls = models.BooleanField(blank=True, null=True)
    tempo_sessao = models.IntegerField(blank=True, null=True)
    tentativas_login = models.IntegerField(blank=True, null=True)
    tempo_bloqueio = models.IntegerField(blank=True, null=True)
    requer_senha_forte = models.BooleanField(blank=True, null=True)
    nome_sistema = models.CharField(max_length=100, default="Meu Sistema")
    tema_primario = models.CharField(max_length=100, default="azul")
    tema_secundario = models.CharField(max_length=7, default="#6dd5ed")
    email_suporte = models.EmailField(blank=True, null=True)
    logo = models.ImageField(upload_to="configuracao/", blank=True, null=True)
    data_atualizacao = models.DateTimeField(auto_now=True)


class Empresa(models.Model):
    razao_social = models.CharField(max_length=100)
    cnpj = models.CharField(max_length=18)
    endereco = models.CharField(max_length=200)
    telefone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    logo = models.ImageField(upload_to="empresa/", blank=True, null=True)


class PermissaoCustomizada(models.Model):
    nome = models.CharField(max_length=100)
    codigo = models.CharField(max_length=50, unique=True)
    grupos = models.ManyToManyField(Group, blank=True)
    descricao = models.TextField(blank=True)


class ModeloImpressao(models.Model):
    nome = models.CharField(max_length=100)
    tipo = models.CharField(
        max_length=50, choices=[("pedido", "Pedido"), ("orcamento", "Orçamento"), ("nf", "Nota Fiscal")]
    )
    template_html = models.TextField()
    criado_em = models.DateTimeField(auto_now_add=True)


class Integracao(models.Model):
    nome = models.CharField(max_length=100)
    tipo = models.CharField(
        max_length=50, choices=[("ipi", "IPI"), ("email", "E-mail"), ("melhor_envio", "Melhor Envio")]
    )
    api_key = models.CharField(max_length=200, blank=True)
    endpoint = models.CharField(max_length=200, blank=True)
    usuario = models.CharField(max_length=100, blank=True)
    senha = models.CharField(max_length=100, blank=True)
    parametros = models.JSONField(blank=True, null=True)
    ativo = models.BooleanField(default=True)
    atualizado_em = models.DateTimeField(auto_now=True)
