from django.urls import path

from . import views

app_name = "core"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("home/", views.dashboard, name="home"),
    path("index/", views.index, name="index"),  # Página de exemplo
]
