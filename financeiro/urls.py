# financeiro/urls.py

from django.urls import path

from . import views

app_name = "financeiro"

urlpatterns = [
    # Dashboard
    path("", views.dashboard, name="dashboard"),
    path("", views.dashboard, name="index"),  # Alias para compatibilidade
    path("listar/", views.listar, name="listar"),
    # CRUD de Receitas
    path("receitas/novo/", views.nova_receita, name="nova_receita"),
    path("receitas/editar/<int:pk>/", views.editar_receita, name="editar_receita"),
    path("receitas/deletar/<int:pk>/", views.deletar_receita, name="deletar_receita"),
    # CRUD de Despesas
    path("despesas/novo/", views.nova_despesa, name="nova_despesa"),
    path("despesas/editar/<int:pk>/", views.editar_despesa, name="editar_despesa"),
    path("despesas/deletar/<int:pk>/", views.deletar_despesa, name="deletar_despesa"),
    # Centro de Custos
    path("centros-custo/", views.centros_custo, name="centros_custo"),
    path("centros-custo/novo/", views.novo_centro_custo, name="novo_centro_custo"),
    path("centros-custo/editar/<int:pk>/", views.editar_centro_custo, name="editar_centro_custo"),
    path("centros-custo/excluir/<int:pk>/", views.excluir_centro_custo, name="excluir_centro_custo"),
    # Relatórios
    path("relatorios/", views.relatorios, name="relatorios"),
    # APIs
    path("api/fluxo-caixa/", views.api_fluxo_caixa, name="api_fluxo_caixa"),
    # Utilitários
    path("marcar-realizado/<str:tipo>/<int:pk>/", views.marcar_realizado, name="marcar_realizado"),
]
