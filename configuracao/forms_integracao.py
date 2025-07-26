from django import forms

from .models import Integracao


class IntegracaoForm(forms.ModelForm):
    class Meta:
        model = Integracao
        fields = ["nome", "tipo", "api_key", "endpoint", "usuario", "senha", "parametros", "ativo"]
        widgets = {
            "nome": forms.TextInput(attrs={"class": "form-control"}),
            "tipo": forms.Select(attrs={"class": "form-control"}),
            "api_key": forms.TextInput(attrs={"class": "form-control"}),
            "endpoint": forms.TextInput(attrs={"class": "form-control"}),
            "usuario": forms.TextInput(attrs={"class": "form-control"}),
            "senha": forms.PasswordInput(attrs={"class": "form-control"}),
            "parametros": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
            "ativo": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }
