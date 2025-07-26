from django.urls import path

from . import views

app_name = "configuracao"

urlpatterns = [
    path("", views.index, name="index"),
    path("parametros-gerais/", views.parametros_gerais, name="parametros_gerais"),
    path("integracoes/", views.lista_integracoes, name="lista_integracoes"),
    path("integracoes/nova/", views.nova_integracao, name="nova_integracao"),
    path("modelos-impressao/", views.editar_modelo_impressao, name="modelos_impressao"),
    path("backup/", views.backup, name="backup"),
    path("fazer-backup/", views.fazer_backup, name="fazer_backup"),
    path("restaurar-backup/", views.restaurar_backup, name="restaurar_backup"),
    path("listar-backups/", views.listar_backups, name="listar_backups"),
    path("excluir-backup/", views.excluir_backup, name="excluir_backup"),
]
