from django import forms

from .models import Despesa, Receita


class ReceitaForm(forms.ModelForm):
    class Meta:
        model = Receita
        fields = "__all__"

    def clean_anexo(self):
        anexo = self.cleaned_data.get("anexo")
        if anexo:
            if anexo.size > 2 * 1024 * 1024:
                raise forms.ValidationError("O anexo deve ter no máximo 2MB.")
            if not anexo.name.lower().endswith((".png", ".jpg", ".jpeg", ".pdf")):
                raise forms.ValidationError("Formato de anexo inválido.")
        return anexo


class DespesaForm(forms.ModelForm):
    class Meta:
        model = Despesa
        fields = "__all__"

    def clean_anexo(self):
        anexo = self.cleaned_data.get("anexo")
        if anexo:
            if anexo.size > 2 * 1024 * 1024:
                raise forms.ValidationError("O anexo deve ter no máximo 2MB.")
            if not anexo.name.lower().endswith((".png", ".jpg", ".jpeg", ".pdf")):
                raise forms.ValidationError("Formato de anexo inválido.")
        return anexo
