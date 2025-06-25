from django.urls import path
from . import views

app_name = 'configuracao'

urlpatterns = [
    # path('sistema/', views.configuracao_sistema, name='configuracao_sistema'),
    # path('empresa/', views.configuracao_empresa, name='configuracao_empresa'),
    # path('integracoes/', views.lista_integracoes, name='lista_integracoes'),
    # path('integracoes/nova/', views.nova_integracao, name='nova_integracao'),
    # path('integracoes/<int:pk>/editar/', views.editar_integracao, name='editar_integracao'),

    # Modelos de Impressão
    path('modelos-impressao/', views.editar_modelo_impressao, name='modelos_impressao'),
    # (as rotas de CRUD antigas podem ser removidas ou mantidas para outros modelos)

    # Permissões Customizadas
    # path('permissoes/', views.lista_permissoes, name='lista_permissoes'),
    # path('permissoes/nova/', views.nova_permissao, name='nova_permissao'),
    # path('permissoes/<int:pk>/editar/', views.editar_permissao, name='editar_permissao'),
    # path('permissoes/<int:pk>/excluir/', views.excluir_permissao, name='excluir_permissao'),
]
