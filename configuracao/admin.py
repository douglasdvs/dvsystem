from django.contrib import admin

from .models import ConfiguracaoSistema, Empresa, Integracao, ModeloImpressao, PermissaoCustomizada


@admin.register(ConfiguracaoSistema)
class ConfiguracaoSistemaAdmin(admin.ModelAdmin):
    list_display = ("nome_sistema", "tema_primario", "tema_secundario", "email_suporte", "data_atualizacao")


@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    list_display = ("razao_social", "cnpj", "email")


@admin.register(PermissaoCustomizada)
class PermissaoCustomizadaAdmin(admin.ModelAdmin):
    list_display = ("nome", "codigo", "descricao")
    filter_horizontal = ("grupos",)


@admin.register(ModeloImpressao)
class ModeloImpressaoAdmin(admin.ModelAdmin):
    list_display = ("nome", "tipo", "criado_em")
    search_fields = ("nome", "tipo")


@admin.register(Integracao)
class IntegracaoAdmin(admin.ModelAdmin):
    list_display = ("nome", "tipo", "api_key", "ativo", "atualizado_em")
    list_filter = ("tipo", "ativo")
