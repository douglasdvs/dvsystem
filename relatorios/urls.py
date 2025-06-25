from django.urls import path
from . import views

app_name = 'relatorios'

urlpatterns = [
    path('', views.index, name='index'),
    path('clientes/abc/', views.relatorio_abc_clientes, name='relatorio_abc_clientes'),
    path('clientes/abc/export/', views.relatorio_abc_clientes_export, name='relatorio_abc_clientes_export'),
    path('clientes/sem-compras/', views.relatorio_clientes_sem_compras, name='relatorio_clientes_sem_compras'),
    path('clientes/sem-compras/export/', views.relatorio_clientes_sem_compras_export, name='relatorio_clientes_sem_compras_export'),
    path('dre/', views.relatorio_dre, name='relatorio_dre'),
    path('dre/export/', views.relatorio_dre_export, name='relatorio_dre_export'),
    path('margem-lucro/', views.relatorio_margem_lucro, name='relatorio_margem_lucro'),
    path('margem-lucro/export/', views.relatorio_margem_lucro_export, name='relatorio_margem_lucro_export'),
    path('vendas-por-vendedor/', views.relatorio_vendas_por_vendedor, name='relatorio_vendas_por_vendedor'),
    path('vendas-por-vendedor/export/', views.relatorio_vendas_por_vendedor_export, name='relatorio_vendas_por_vendedor_export'),
]
