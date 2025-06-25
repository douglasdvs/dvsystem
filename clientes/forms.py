from django import forms
from .models import Cliente, TipoCliente, UF_CHOICES, Endereco, Tag
from .utils import validar_cpf_cnpj, validar_telefone, validar_cep
import re

class TagForm(forms.ModelForm):
    """Formulário para criação e edição de tags."""
    
    class Meta:
        model = Tag
        fields = ['nome', 'cor', 'descricao']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'cor': forms.TextInput(attrs={
                'class': 'form-control',
                'type': 'color'
            }),
            'descricao': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3
            })
        }
    
    def clean_cor(self):
        cor = self.cleaned_data['cor']
        if not cor.startswith('#'):
            cor = f'#{cor}'
        return cor

class ClienteForm(forms.ModelForm):
    """Formulário para criação e edição de clientes."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from .models import Segmento
        self.fields['segmento'].queryset = Segmento.objects.all().order_by('nome')
        self.fields['segmento'].empty_label = 'Selecione o segmento...'

    class Meta:
        model = Cliente
        fields = [
            'nome', 'cpf_cnpj', 'email', 'telefone', 'cep', 'endereco', 'numero', 'complemento', 'bairro', 'cidade', 'uf', 'tipo_cliente', 'segmento', 'ativo', 'observacao'
        ]
        widgets = {
            'nome': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nome completo'
            }),
            'cpf_cnpj': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'CPF ou CNPJ'}),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'E-mail'
            }),
            'telefone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Telefone'
            }),
            'cep': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'CEP',
                'id': 'id_cep'
            }),
            'endereco': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Endereço',
                'id': 'id_endereco'
            }),
            'numero': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Número',
                'id': 'id_numero'
            }),
            'complemento': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Complemento'
            }),
            'bairro': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Bairro',
                'id': 'id_bairro'
            }),
            'cidade': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Cidade',
                'id': 'id_cidade'
            }),
            'uf': forms.Select(attrs={
                'class': 'form-control',
                'id': 'id_uf'
            }, choices=UF_CHOICES),
            'tipo_cliente': forms.Select(attrs={'class': 'form-control'}),
            'segmento': forms.Select(attrs={'class': 'form-control'}),
            'observacao': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Observações'
            }),
            'ativo': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }

    def validar_cpf(self, cpf):
        # Remove caracteres não numéricos
        cpf = ''.join(filter(str.isdigit, cpf))
        
        # Verifica se tem 11 dígitos
        if len(cpf) != 11:
            return False
            
        # Verifica se todos os dígitos são iguais
        if cpf == cpf[0] * 11:
            return False
            
        # Validação do primeiro dígito verificador
        soma = sum(int(cpf[i]) * (10 - i) for i in range(9))
        digito1 = (soma * 10 % 11) % 10
        if int(cpf[9]) != digito1:
            return False
            
        # Validação do segundo dígito verificador
        soma = sum(int(cpf[i]) * (11 - i) for i in range(10))
        digito2 = (soma * 10 % 11) % 10
        if int(cpf[10]) != digito2:
            return False
            
        return True

    def validar_cnpj(self, cnpj):
        # Remove caracteres não numéricos
        cnpj = ''.join(filter(str.isdigit, cnpj))
        
        # Verifica se tem 14 dígitos
        if len(cnpj) != 14:
            return False
            
        # Verifica se todos os dígitos são iguais
        if cnpj == cnpj[0] * 14:
            return False
            
        # Validação do primeiro dígito verificador
        peso = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        soma = sum(int(cnpj[i]) * peso[i] for i in range(12))
        digito1 = (11 - (soma % 11)) % 10
        if int(cnpj[12]) != digito1:
            return False
            
        # Validação do segundo dígito verificador
        peso = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        soma = sum(int(cnpj[i]) * peso[i] for i in range(13))
        digito2 = (11 - (soma % 11)) % 10
        if int(cnpj[13]) != digito2:
            return False
            
        return True

    def clean_cpf_cnpj(self):
        cpf_cnpj = self.cleaned_data.get('cpf_cnpj')
        if not cpf_cnpj or cpf_cnpj.strip() == '':
            return None
        valido, tipo = validar_cpf_cnpj(cpf_cnpj)
        if not valido:
            raise forms.ValidationError(f'{tipo} inválido')
        return cpf_cnpj

    def clean_telefone(self):
        telefone = self.cleaned_data['telefone']
        if not validar_telefone(telefone):
            raise forms.ValidationError('Telefone inválido')
        return telefone

    def clean_cep(self):
        cep = self.cleaned_data['cep']
        if not validar_cep(cep):
            raise forms.ValidationError('CEP inválido')
        return cep

class TipoClienteForm(forms.ModelForm):
    class Meta:
        model = TipoCliente
        fields = ['nome', 'descricao']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class EnderecoForm(forms.ModelForm):
    class Meta:
        model = Endereco
        fields = [
            'cep', 'logradouro', 'numero', 'complemento', 'bairro', 'cidade', 'uf'
        ]
        widgets = {
            'cep': forms.TextInput(attrs={
                'class': 'form-control cep',
                'placeholder': '00000-000'
            }),
            'logradouro': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Rua, Avenida, etc.'
            }),
            'numero': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Número'
            }),
            'complemento': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Complemento (opcional)'
            }),
            'bairro': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Bairro'
            }),
            'cidade': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Cidade'
            }),
            'uf': forms.Select(attrs={
                'class': 'form-select'
            }, choices=UF_CHOICES),
        }

    def clean_cep(self):
        cep = self.cleaned_data['cep']
        digits = ''.join(filter(str.isdigit, cep))
        if not digits or len(digits) != 8:
            raise forms.ValidationError('CEP inválido')
        return f"{digits[:5]}-{digits[5:]}"

    def clean_uf(self):
        uf = self.cleaned_data['uf']
        if uf not in dict(UF_CHOICES).keys():
            raise forms.ValidationError('UF inválida')
        return uf