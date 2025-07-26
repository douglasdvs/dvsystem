from django.urls import path

from . import views
from .views import VendedorCreateView, VendedorDeleteView, VendedorListView, VendedorUpdateView

app_name = "vendedores"

urlpatterns = [
    path("", VendedorListView.as_view(), name="list"),
    path("novo/", VendedorCreateView.as_view(), name="create"),
    path("<int:pk>/editar/", VendedorUpdateView.as_view(), name="update"),
    path("<int:pk>/excluir/", VendedorDeleteView.as_view(), name="delete"),
]
