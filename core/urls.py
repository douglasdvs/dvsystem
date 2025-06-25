from django.urls import path, include
from core import views as core_views
from . import views


app_name = 'core'

urlpatterns = [
    path('', core_views.dashboard, name='dashboard'),
    path('home/', core_views.dashboard, name='home'),
    path('clientes/', include('clientes.urls', namespace='clientes')),
    path('produtos/', include('produtos.urls', namespace='produtos')),
    path('pedidos/', include('pedidos.urls', namespace='pedidos')),
    path('financeiro/', include('financeiro.urls', namespace='financeiro')),
    path('relatorios/', include('relatorios.urls', namespace='relatorios')),
    path('', views.dashboard, name='dashboard'),  # ou index, se preferir
    path('', views.index, name='index')
    
]