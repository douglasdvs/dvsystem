from functools import wraps

from django.contrib import messages
from django.shortcuts import redirect

from configuracao.models import PermissaoCustomizada


def usuario_tem_permissao(user, codigo_permissao):
    if not user.is_authenticated:
        return False
    try:
        permissao = PermissaoCustomizada.objects.get(codigo=codigo_permissao)
        return permissao.grupos.filter(id__in=user.groups.all()).exists() or user.is_superuser
    except PermissaoCustomizada.DoesNotExist:
        return False


def permissao_necessaria(codigo_permissao):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not usuario_tem_permissao(request.user, codigo_permissao):
                messages.error(request, "Você não tem permissão para acessar esta funcionalidade.")
                return redirect("core:home")  # Ajuste para a página desejada
            return view_func(request, *args, **kwargs)

        return _wrapped_view

    return decorator
