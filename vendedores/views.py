from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from .models import Vendedor


class VendedorListView(ListView):
    model = Vendedor
    template_name = "vendedores/vendedor_list.html"
    context_object_name = "vendedores"
    paginate_by = 30

    def get_queryset(self):
        queryset = super().get_queryset()
        busca = self.request.GET.get("busca", "").strip()
        if busca:
            queryset = queryset.filter(nome__icontains=busca)
        return queryset


class VendedorCreateView(CreateView):
    model = Vendedor
    fields = ["nome", "telefone", "comissao_percentual"]
    template_name = "vendedores/vendedor_form.html"
    success_url = reverse_lazy("vendedores:list")


class VendedorUpdateView(UpdateView):
    model = Vendedor
    fields = ["nome", "telefone", "comissao_percentual"]
    template_name = "vendedores/vendedor_form.html"
    success_url = reverse_lazy("vendedores:list")


class VendedorDeleteView(DeleteView):
    model = Vendedor
    template_name = "vendedores/vendedor_confirm_delete.html"
    success_url = reverse_lazy("vendedores:list")
