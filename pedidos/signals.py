# pedidos/signals.py

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import ItemPedido

@receiver([post_save, post_delete], sender=ItemPedido)
def atualizar_total_pedido_on_item_change(sender, instance, **kwargs):
    pedido = instance.pedido
    # Se você quiser recalcular e armazenar num campo, faça:
    # total = pedido.calcular_total()
    # pedido.total = total
    # pedido.save()
    #
    # Mas como não há campo total na tabela, basta re‐salvar
    pedido.save()
