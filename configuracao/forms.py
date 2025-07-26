from django import forms
from django.contrib.auth import get_user_model

from .models import ConfiguracaoSistema

User = get_user_model()


class ConfiguracaoSistemaForm(forms.ModelForm):
    class Meta:
        model = ConfiguracaoSistema
        fields = "__all__"
        widgets = {
            "nome_sistema": forms.TextInput(attrs={"class": "form-control"}),
            "descricao_sistema": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "versao_sistema": forms.TextInput(attrs={"class": "form-control"}),
            "host_banco": forms.TextInput(attrs={"class": "form-control"}),
            "porta_banco": forms.NumberInput(attrs={"class": "form-control"}),
            "nome_banco": forms.TextInput(attrs={"class": "form-control"}),
            "usuario_banco": forms.TextInput(attrs={"class": "form-control"}),
            "senha_banco": forms.PasswordInput(attrs={"class": "form-control"}),
            "host_email": forms.TextInput(attrs={"class": "form-control"}),
            "porta_email": forms.NumberInput(attrs={"class": "form-control"}),
            "usuario_email": forms.TextInput(attrs={"class": "form-control"}),
            "senha_email": forms.PasswordInput(attrs={"class": "form-control"}),
            "usar_tls": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "tempo_sessao": forms.NumberInput(attrs={"class": "form-control"}),
            "tentativas_login": forms.NumberInput(attrs={"class": "form-control"}),
            "tempo_bloqueio": forms.NumberInput(attrs={"class": "form-control"}),
            "requer_senha_forte": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }
