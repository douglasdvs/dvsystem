from django import forms
from django_select2.forms import Select2Widget
from .models import Pedido, ItemPedido, HistoricoPedido, AnexoPedido
from produtos.models import Produto
from clientes.models import Cliente
from django.forms import inlineformset_factory
from django.urls import reverse_lazy

class PedidoForm(forms.ModelForm):
    valor_sinal_pago = forms.DecimalField(
        label='Valor do Sinal Pago',
        required=False,
        min_value=0,
        decimal_places=2,
        max_digits=10,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'})
    )
    valor_restante_pago = forms.DecimalField(
        label='Valor do Restante Pago',
        required=False,
        min_value=0,
        decimal_places=2,
        max_digits=10,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'})
    )

    class Meta:
        model = Pedido
        fields = [
            'cliente', 'vendedor', 'status', 'prioridade', 'forma_pagamento',
            'data_entrega_prevista', 'desconto', 'taxa_entrega',
            'observacoes', 'observacoes_internas', 'arquivo_arte',
            'arte_aprovada', 'data_arte_aprovada', 'arquivo_arte_aprovada', 'observacoes_arte',
            'sinal_pago', 'data_sinal_pago', 'restante_pago', 'data_restante_pago',
            'valor_sinal_pago', 'valor_restante_pago',
            'valor_recebido',
            'forma_envio', 'codigo_rastreio', 'data_envio', 'data_entrega',
        ]
        widgets = {
            'cliente': Select2Widget(
                attrs={
                    'class': 'form-control',
                    'data-placeholder': 'Digite nome, CPF/CNPJ, email ou telefone...',
                    'data-ajax--url': '/clientes/api/buscar/',
                    'data-ajax--cache': 'true',
                    'data-ajax--delay': '250',
                    'data-ajax--data-type': 'json',
                    'data-minimum-input-length': '2',
                }
            ),
            'vendedor': forms.Select(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'prioridade': forms.Select(attrs={'class': 'form-control'}),
            'forma_pagamento': forms.Select(attrs={'class': 'form-select'}),
            'data_entrega_prevista': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'desconto': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
            'taxa_entrega': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
            'observacoes': forms.Textarea(attrs={'rows': 3}),
            'observacoes_internas': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'arquivo_arte': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'arte_aprovada': forms.CheckboxInput(),
            'data_arte_aprovada': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'arquivo_arte_aprovada': forms.ClearableFileInput(),
            'observacoes_arte': forms.Textarea(attrs={'rows': 2}),
            'sinal_pago': forms.CheckboxInput(),
            'data_sinal_pago': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'restante_pago': forms.CheckboxInput(),
            'data_restante_pago': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'valor_sinal_pago': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'valor_restante_pago': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'valor_recebido': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'forma_envio': forms.Select(),
            'codigo_rastreio': forms.TextInput(),
            'data_envio': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'data_entrega': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        status = cleaned_data.get('status')
        sinal_pago = cleaned_data.get('sinal_pago')
        restante_pago = cleaned_data.get('restante_pago')
        valor_recebido = cleaned_data.get('valor_recebido')
        instance = getattr(self, 'instance', None)
        total = instance.total if instance and instance.pk else None
        if status in ['A', 'E', 'T'] and not sinal_pago:
            self.add_error('sinal_pago', 'O sinal deve estar pago para avançar para este status.')
        if status in ['E', 'T'] and not restante_pago:
            self.add_error('restante_pago', 'O restante deve estar pago para avançar para este status.')
        # Só valida valor_recebido < total se o pedido já existir (edição)
        if status and valor_recebido is not None and total is not None and valor_recebido < total:
            self.add_error('valor_recebido', 'O valor recebido não pode ser menor que o total do pedido para alterar o status.')
        return cleaned_data

class ItemPedidoForm(forms.ModelForm):
    class Meta:
        model = ItemPedido
        fields = ['produto', 'quantidade', 'preco_unitario', 'desconto_item', 'observacoes']
        widgets = {
            'produto': Select2Widget(
                attrs={
                    'class': 'form-control produto-select',
                    'data-placeholder': 'Digite descrição ou categoria do produto...',
                    'data-ajax--url': reverse_lazy('pedidos:buscar_produtos_ajax'),
                    'data-ajax--cache': 'true',
                    'data-ajax--delay': '250',
                    'data-ajax--data-type': 'json',
                    'data-minimum-input-length': '2',
                }
            ),
            'quantidade': forms.NumberInput(attrs={'class': 'form-control quantidade'}),
            'preco_unitario': forms.NumberInput(attrs={'class': 'form-control preco-unitario', 'step': '0.01'}),
            'desconto_item': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'observacoes': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.pk:
            self.fields['quantidade'].initial = 1
            self.fields['desconto_item'].initial = 0

class HistoricoPedidoForm(forms.ModelForm):
    class Meta:
        model = HistoricoPedido
        fields = ['tipo', 'descricao']
        widgets = {
            'tipo': forms.Select(attrs={'class': 'form-control'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class AnexoPedidoForm(forms.ModelForm):
    class Meta:
        model = AnexoPedido
        fields = ['arquivo', 'descricao']
        widgets = {
            'arquivo': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'descricao': forms.TextInput(attrs={'class': 'form-control'}),
        }

class FiltrosPedidoForm(forms.Form):
    """Formulário para filtros avançados de pedidos"""
    status = forms.ChoiceField(
        choices=[('', 'Todos os Status')] + Pedido.STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    prioridade = forms.ChoiceField(
        choices=[('', 'Todas as Prioridades')] + Pedido.PRIORIDADE_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    vendedor = forms.ChoiceField(
        choices=[('', 'Todos os Vendedores')] + Pedido.VENDEDORES_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    data_inicio = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    data_fim = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    busca = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control', 
            'placeholder': 'Buscar por cliente, número do pedido...'
        })
    )

ItemPedidoFormSet = inlineformset_factory(
    Pedido,
    ItemPedido,
    form=ItemPedidoForm,
    extra=0,
    can_delete=True,
    min_num=1,
    validate_min=True
)
