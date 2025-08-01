# Generated by Django 5.2.2 on 2025-06-27 01:02

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [
        migrations.CreateModel(
            name="ConfiguracaoSistema",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("nome_empresa", models.CharField(default="Minha Empresa", max_length=100)),
                ("cnpj", models.CharField(blank=True, max_length=18, null=True)),
                ("endereco", models.CharField(blank=True, max_length=200, null=True)),
                ("telefone", models.CharField(blank=True, max_length=20, null=True)),
                ("email", models.EmailField(blank=True, max_length=254, null=True)),
                ("site", models.CharField(blank=True, max_length=100, null=True)),
                ("instagram", models.CharField(blank=True, max_length=100, null=True)),
                ("facebook", models.CharField(blank=True, max_length=100, null=True)),
                ("whatsapp", models.CharField(blank=True, max_length=100, null=True)),
                ("cor_primaria", models.CharField(blank=True, default="#2193b0", max_length=20, null=True)),
                ("cor_secundaria", models.CharField(blank=True, default="#6dd5ed", max_length=20, null=True)),
                ("cor_sucesso", models.CharField(blank=True, default="#28a745", max_length=20, null=True)),
                ("cor_perigo", models.CharField(blank=True, default="#dc3545", max_length=20, null=True)),
                ("cor_alerta", models.CharField(blank=True, default="#ffc107", max_length=20, null=True)),
                ("cor_info", models.CharField(blank=True, default="#17a2b8", max_length=20, null=True)),
                ("smtp_host", models.CharField(blank=True, max_length=100, null=True)),
                ("smtp_port", models.IntegerField(blank=True, null=True)),
                ("smtp_usuario", models.CharField(blank=True, max_length=100, null=True)),
                ("smtp_senha", models.CharField(blank=True, max_length=100, null=True)),
                ("email_remetente", models.EmailField(blank=True, max_length=254, null=True)),
                ("api_melhor_envio_token", models.CharField(blank=True, max_length=200, null=True)),
                ("api_melhor_envio_sandbox", models.BooleanField(blank=True, null=True)),
                ("modelo_pedido", models.CharField(blank=True, max_length=100, null=True)),
                ("modelo_orcamento", models.CharField(blank=True, max_length=100, null=True)),
                ("descricao_sistema", models.CharField(blank=True, max_length=200, null=True)),
                ("versao_sistema", models.CharField(blank=True, max_length=20, null=True)),
                ("usar_tls", models.BooleanField(blank=True, null=True)),
                ("tempo_sessao", models.IntegerField(blank=True, null=True)),
                ("tentativas_login", models.IntegerField(blank=True, null=True)),
                ("tempo_bloqueio", models.IntegerField(blank=True, null=True)),
                ("requer_senha_forte", models.BooleanField(blank=True, null=True)),
                ("nome_sistema", models.CharField(default="Meu Sistema", max_length=100)),
                ("tema_primario", models.CharField(default="azul", max_length=100)),
                ("tema_secundario", models.CharField(default="#6dd5ed", max_length=7)),
                ("email_suporte", models.EmailField(blank=True, max_length=254, null=True)),
                ("logo", models.ImageField(blank=True, null=True, upload_to="configuracao/")),
                ("data_atualizacao", models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name="Empresa",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("razao_social", models.CharField(max_length=100)),
                ("cnpj", models.CharField(max_length=18)),
                ("endereco", models.CharField(max_length=200)),
                ("telefone", models.CharField(blank=True, max_length=20)),
                ("email", models.EmailField(blank=True, max_length=254)),
                ("logo", models.ImageField(blank=True, null=True, upload_to="empresa/")),
            ],
        ),
        migrations.CreateModel(
            name="Integracao",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("nome", models.CharField(max_length=100)),
                (
                    "tipo",
                    models.CharField(
                        choices=[("ipi", "IPI"), ("email", "E-mail"), ("melhor_envio", "Melhor Envio")], max_length=50
                    ),
                ),
                ("api_key", models.CharField(blank=True, max_length=200)),
                ("endpoint", models.CharField(blank=True, max_length=200)),
                ("usuario", models.CharField(blank=True, max_length=100)),
                ("senha", models.CharField(blank=True, max_length=100)),
                ("parametros", models.JSONField(blank=True, null=True)),
                ("ativo", models.BooleanField(default=True)),
                ("atualizado_em", models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name="ModeloImpressao",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("nome", models.CharField(max_length=100)),
                (
                    "tipo",
                    models.CharField(
                        choices=[("pedido", "Pedido"), ("orcamento", "Orçamento"), ("nf", "Nota Fiscal")], max_length=50
                    ),
                ),
                ("template_html", models.TextField()),
                ("criado_em", models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name="PermissaoCustomizada",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("nome", models.CharField(max_length=100)),
                ("codigo", models.CharField(max_length=50, unique=True)),
                ("descricao", models.TextField(blank=True)),
                ("grupos", models.ManyToManyField(blank=True, to="auth.group")),
            ],
        ),
    ]
