from django.urls import path

from . import views

app_name = "clientes"

urlpatterns = [
    # URLs para Clientes
    path("", views.listar_clientes, name="listar"),
    path("novo/", views.ClienteCreateView.as_view(), name="novo"),
    path("<int:pk>/editar/", views.ClienteUpdateView.as_view(), name="editar"),
    path("<int:pk>/excluir/", views.ClienteDeleteView.as_view(), name="excluir"),
    path("<int:pk>/", views.ClienteDetailView.as_view(), name="detalhe"),
    path("buscar-cep/", views.buscar_cep, name="buscar_cep"),
    path("exportar/", views.exportar_clientes, name="exportar"),
    # URLs para Tipos de Cliente
    path("tipos/", views.TipoClienteListView.as_view(), name="tipos_cliente"),
    path("tipos/nova/", views.TipoClienteCreateView.as_view(), name="criar_tipo_cliente"),
    path("tipos/<int:pk>/editar/", views.TipoClienteUpdateView.as_view(), name="editar_tipo_cliente"),
    path("tipos/<int:pk>/excluir/", views.TipoClienteDeleteView.as_view(), name="excluir_tipo_cliente"),
    # URLs para Tags
    path("tags/", views.TagListView.as_view(), name="tags"),
    path("tags/novo/", views.TagCreateView.as_view(), name="novo_tag"),
    path("tags/<int:pk>/editar/", views.TagUpdateView.as_view(), name="editar_tag"),
    path("tags/<int:pk>/excluir/", views.TagDeleteView.as_view(), name="excluir_tag"),
    path("<int:cliente_id>/tags/adicionar/", views.adicionar_tag_cliente, name="adicionar_tag"),
    path("<int:cliente_id>/tags/remover/", views.remover_tag_cliente, name="remover_tag"),
    # URLs para Endereços
    path("<int:cliente_id>/enderecos/novo/", views.adicionar_endereco, name="novo_endereco"),
    path("enderecos/<int:pk>/editar/", views.editar_endereco, name="editar_endereco"),
    path("enderecos/<int:pk>/excluir/", views.excluir_endereco, name="excluir_endereco"),
    path("api/buscar/", views.api_buscar_cliente, name="api_buscar_cliente"),
    # URL para cadastro de segmento
    path("segmentos/novo/", views.novo_segmento, name="novo_segmento"),
    path("segmentos/<int:pk>/editar/", views.SegmentoUpdateView.as_view(), name="editar_segmento"),
    path("segmentos/<int:pk>/excluir/", views.SegmentoDeleteView.as_view(), name="excluir_segmento"),
]

# Removido: rotas duplicadas e obsoletas para tipos de cliente
