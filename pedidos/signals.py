# pedidos/signals.py

from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .models import ItemPedido


@receiver([post_save, post_delete], sender=ItemPedido)
def atualizar_total_pedido_on_item_change(sender, instance, **kwargs):
    # O argumento 'raw' é True quando os dados estão sendo carregados de uma fixture (loaddata)
    # Isso evita que o signal seja executado durante a migração de dados.
    if kwargs.get("raw", False):
        return

    pedido = instance.pedido
    if pedido:
        # A lógica de salvar o pedido já recalcula os totais através do método save() do modelo Pedido.
        pedido.save()
