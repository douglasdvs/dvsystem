from django import forms
from django_select2.forms import Select2Widget
from .models import Receita, Despesa, CentroCusto

class ReceitaForm(forms.ModelForm):
    class Meta:
        model = Receita
        fields = [
            'descricao', 'data', 'data_vencimento', 'valor', 'categoria',
            'cliente', 'pedido', 'forma_pagamento', 'status', 'observacoes', 'anexo'
        ]
        widgets = {
            'descricao': forms.TextInput(attrs={'class': 'form-control'}),
            'data': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'data_vencimento': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'valor': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'categoria': forms.Select(attrs={'class': 'form-control'}),
            'cliente': Select2Widget(attrs={'class': 'form-control'}),
            'pedido': Select2Widget(attrs={'class': 'form-control'}),
            'forma_pagamento': forms.Select(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'observacoes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'anexo': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }

    def clean_anexo(self):
        anexo = self.cleaned_data.get('anexo')
        if anexo:
            if anexo.size > 2 * 1024 * 1024:
                raise forms.ValidationError("O anexo deve ter no máximo 2MB.")
            if not anexo.name.lower().endswith(('.png', '.jpg', '.jpeg', '.pdf')):
                raise forms.ValidationError("Formato de anexo inválido.")
        return anexo

class DespesaForm(forms.ModelForm):
    class Meta:
        model = Despesa
        fields = [
            'descricao', 'data', 'data_vencimento', 'valor', 'categoria',
            'centro_custo', 'forma_pagamento', 'status', 'observacoes', 'anexo'
        ]
        widgets = {
            'descricao': forms.TextInput(attrs={'class': 'form-control'}),
            'data': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'data_vencimento': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'valor': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'categoria': forms.Select(attrs={'class': 'form-control'}),
            'centro_custo': Select2Widget(attrs={'class': 'form-control'}),
            'forma_pagamento': forms.Select(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'observacoes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'anexo': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }

    def clean_anexo(self):
        anexo = self.cleaned_data.get('anexo')
        if anexo:
            if anexo.size > 2 * 1024 * 1024:
                raise forms.ValidationError("O anexo deve ter no máximo 2MB.")
            if not anexo.name.lower().endswith(('.png', '.jpg', '.jpeg', '.pdf')):
                raise forms.ValidationError("Formato de anexo inválido.")
        return anexo

class CentroCustoForm(forms.ModelForm):
    class Meta:
        model = CentroCusto
        fields = ['nome', 'descricao', 'ativo']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'ativo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class RelatorioForm(forms.Form):
    """Formulário para geração de relatórios"""
    data_inicio = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        label='Data Início'
    )
    data_fim = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        label='Data Fim'
    )
    categoria = forms.ChoiceField(
        choices=[('todas', 'Todas as categorias')] + 
                list(Receita._meta.get_field('categoria').choices) + 
                list(Despesa._meta.get_field('categoria').choices),
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=False
    )
    status = forms.ChoiceField(
        choices=[('todos', 'Todos os status'), ('P', 'Pendente'), ('R', 'Realizado'), ('C', 'Cancelado')],
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=False
    )
