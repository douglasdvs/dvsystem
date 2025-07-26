from django.urls import path

from . import views

urlpatterns = [
    path("receitas/", views.lista_receitas, name="lista_receitas"),
    path("receitas/novo/", views.nova_receita, name="nova_receita"),
    path("receitas/editar/<int:pk>/", views.editar_receita, name="editar_receita"),
    path("receitas/deletar/<int:pk>/", views.deletar_receita, name="deletar_receita"),
    path("despesas/", views.lista_despesas, name="lista_despesas"),
    path("despesas/novo/", views.nova_despesa, name="nova_despesa"),
    path("despesas/editar/<int:pk>/", views.editar_despesa, name="editar_despesa"),
    path("despesas/deletar/<int:pk>/", views.deletar_despesa, name="deletar_despesa"),
]
