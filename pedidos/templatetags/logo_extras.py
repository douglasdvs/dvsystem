import os

from django import template

register = template.Library()


@register.filter
def to_unix_path(value):
    """Converte caminho Windows para formato unix (barra normal)."""
    if isinstance(value, str):
        return value.replace("\\", "/")
    return value
