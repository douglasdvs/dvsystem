# produtos/urls.py
from django.urls import path

from . import views

app_name = "produtos"

urlpatterns = [
    # Listagem e CRUD de produtos
    path("", views.listar_produtos, name="index"),
    path("novo/", views.criar_produto, name="novo"),
    path("editar/<int:id>/", views.editar_produto, name="editar"),
    path("excluir/<int:id>/", views.excluir_produto, name="excluir"),
    path("detalhe/<int:id>/", views.detalhe_produto, name="detalhe"),
    # Ações especiais
    path("duplicar/<int:id>/", views.duplicar_produto, name="duplicar"),
    path("estoque/<int:id>/", views.atualizar_estoque, name="atualizar_estoque"),
    path("codigo-barras/<int:id>/", views.gerar_codigo_barras, name="codigo_barras"),
    path("etiqueta/<int:id>/", views.gerar_etiqueta, name="etiqueta"),
    path("etiqueta/multiplos/", views.gerar_etiquetas_multiplas, name="etiquetas_multiplas"),
    # Importação e Exportação
    path("importar/", views.importar_produtos, name="importar"),
    path("exportar/excel/", views.exportar_excel, name="exportar_excel"),
    path("exportar/csv/", views.exportar_csv, name="exportar_csv"),
    path("modelo/importacao/", views.download_modelo_importacao, name="modelo_importacao"),
    # Categorias
    path("categorias/", views.CategoriaProdutoListView.as_view(), name="listar_categorias"),
    path("categorias/nova/", views.CategoriaProdutoCreateView.as_view(), name="nova_categoria"),
    path("categorias/<int:pk>/editar/", views.CategoriaProdutoUpdateView.as_view(), name="editar_categoria"),
    path("categorias/<int:pk>/excluir/", views.CategoriaProdutoDeleteView.as_view(), name="excluir_categoria"),
    # Estoque e Histórico
    path("estoque/movimentos/", views.listar_movimentos_estoque, name="movimentos_estoque"),
    path("historico/precos/", views.listar_historico_precos, name="historico_precos"),
    path("relatorios/estoque/", views.relatorio_estoque, name="relatorio_estoque"),
    # API interna
    path("api/produtos/", views.api_produtos, name="api_produtos"),
    path("api/buscar/", views.api_buscar_produto, name="api_buscar_produto"),
    path("api/categorias/", views.api_categorias, name="api_categorias"),
]
