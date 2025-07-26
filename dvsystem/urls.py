from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.contrib.auth.views import LogoutView
from django.urls import include, path

from core.forms import CustomAuthenticationForm
from core.views import register

urlpatterns = [
    path("admin/", admin.site.urls),
    # Autenticação
    path(
        "login/",
        auth_views.LoginView.as_view(
            template_name="registration/login.html", authentication_form=CustomAuthenticationForm
        ),
        name="login",
    ),
    path("logout/", LogoutView.as_view(next_page="login"), name="logout"),
    path("registro/", register, name="register"),
    # Apps
    path("", include("core.urls", namespace="core")),
    path("clientes/", include("clientes.urls", namespace="clientes")),
    path("produtos/", include("produtos.urls", namespace="produtos")),
    path("pedidos/", include("pedidos.urls", namespace="pedidos")),
    path("financeiro/", include("financeiro.urls", namespace="financeiro")),
    # path('agenda/', include('agenda.urls', namespace='agenda')), # Removido se não existir
    path("relatorios/", include("relatorios.urls", namespace="relatorios")),
    path("vendedores/", include("vendedores.urls", namespace="vendedores")),
    # Select2
    path("select2/", include("django_select2.urls")),
    path("configuracao/", include("configuracao.urls", namespace="configuracao")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    try:
        import debug_toolbar

        urlpatterns = [
            path("__debug__/", include(debug_toolbar.urls)),
        ] + urlpatterns
    except ImportError:
        pass
