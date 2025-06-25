from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from core.views import register
from django.contrib.auth.views import LogoutView
from django.conf import settings
from django.conf.urls.static import static
from core.forms import CustomAuthenticationForm

urlpatterns = [
    path('admin/', admin.site.urls),

    # Core com namespace
    path('', include(('core.urls', 'core'), namespace='core')),

    # Autenticação
    path('registro/', register, name='register'),
    path('login/', auth_views.LoginView.as_view(
        template_name='registration/login.html',
        authentication_form=CustomAuthenticationForm), name='login'),
    path('logout/', LogoutView.as_view(next_page='login'), name='logout'),

    # Módulos
    path('clientes/', include(('clientes.urls', 'clientes'), namespace='clientes')),
    path('produtos/', include(('produtos.urls', 'produtos'), namespace='produtos')),
    path('pedidos/', include(('pedidos.urls', 'pedidos'), namespace='pedidos')),
    path('financeiro/', include(('financeiro.urls', 'financeiro'), namespace='financeiro')),
    path('agenda/', include(('agenda.urls', 'agenda'), namespace='agenda')),
    path('relatorios/', include(('relatorios.urls', 'relatorios'), namespace='relatorios')),

    # Select2
    path('select2/', include('django_select2.urls')),
    path('configuracao/', include('configuracao.urls', namespace='configuracao')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
