from django import template

from pedidos.models import Pedido

register = template.Library()


@register.filter
def status_label(code):
    """Retorna o label do status a partir do código."""
    return dict(Pedido.STATUS_CHOICES).get(code, code)
