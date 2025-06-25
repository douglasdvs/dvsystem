# pedidos/urls.py
from django.urls import path
from . import views

app_name = 'pedidos'

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),
    
    # CRUD básico
    path('listar/', views.listar, name='listar'),
    path('novo/', views.novo_pedido, name='novo'),
    path('detalhes/<int:pk>/', views.detalhes_pedido, name='detalhes'),
    path('editar/<int:pk>/', views.editar_pedido, name='editar'),
    path('excluir/<int:pk>/', views.excluir_pedido, name='excluir'),
    
    # PDF do pedido
    path('<int:pedido_id>/pdf/', views.pedido_pdf, name='pedido_pdf'),
    
    # Ações rápidas
    path('status/<int:pk>/<str:novo_status>/', views.alterar_status, name='alterar_status'),
    path('observacao/<int:pk>/', views.adicionar_observacao, name='adicionar_observacao'),
    
    # Ajax
    path('ajax/preco-produto/', views.get_preco_produto, name='ajax_preco_produto'),
    path('ajax/buscar-produtos/', views.buscar_produtos_ajax, name='buscar_produtos_ajax'),
]
