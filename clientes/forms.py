import re

from django import forms

from .models import UF_CHOICES, Cliente, Endereco, Segmento, Tag, TipoCliente
from .utils import validar_cep, validar_cpf_cnpj, validar_telefone


class TagForm(forms.ModelForm):
    """Formulário para criação e edição de tags."""

    class Meta:
        model = Tag
        fields = ["nome", "cor", "descricao"]
        widgets = {
            "nome": forms.TextInput(attrs={"class": "form-control"}),
            "cor": forms.TextInput(attrs={"class": "form-control", "type": "color"}),
            "descricao": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }

    def clean_cor(self):
        cor = self.cleaned_data["cor"]
        if not cor.startswith("#"):
            cor = f"#{cor}"
        return cor


class ClienteForm(forms.ModelForm):
    """Formulário para criação e edição de clientes."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["segmento"].queryset = Segmento.objects.all().order_by("nome")
        self.fields["segmento"].empty_label = "Selecione o segmento..."

    class Meta:
        model = Cliente
        fields = [
            "nome",
            "nome_loja",
            "cpf_cnpj",
            "email",
            "telefone",
            "tipo_cliente",
            "segmento",
            "ativo",
            "observacao",
        ]
        widgets = {
            "nome": forms.TextInput(attrs={"class": "form-control", "placeholder": "Nome completo"}),
            "cpf_cnpj": forms.TextInput(attrs={"class": "form-control", "placeholder": "CPF ou CNPJ"}),
            "email": forms.EmailInput(attrs={"class": "form-control", "placeholder": "E-mail"}),
            "telefone": forms.TextInput(attrs={"class": "form-control", "placeholder": "Telefone"}),
            "tipo_cliente": forms.Select(attrs={"class": "form-control"}),
            "segmento": forms.Select(attrs={"class": "form-control"}),
            "observacao": forms.Textarea(attrs={"class": "form-control", "rows": 3, "placeholder": "Observações"}),
            "ativo": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def clean_cpf_cnpj(self):
        cpf_cnpj = self.cleaned_data.get("cpf_cnpj")
        if not cpf_cnpj or cpf_cnpj.strip() == "":
            return None
        valido, tipo = validar_cpf_cnpj(cpf_cnpj)
        if not valido:
            raise forms.ValidationError(f"{tipo} inválido")
        return cpf_cnpj

    def clean_telefone(self):
        telefone = self.cleaned_data["telefone"]
        if not validar_telefone(telefone):
            raise forms.ValidationError("Telefone inválido")
        return telefone


class TipoClienteForm(forms.ModelForm):
    class Meta:
        model = TipoCliente
        fields = ["nome", "descricao"]
        widgets = {
            "nome": forms.TextInput(attrs={"class": "form-control"}),
            "descricao": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }


class EnderecoForm(forms.ModelForm):
    class Meta:
        model = Endereco
        fields = ["cep", "logradouro", "numero", "complemento", "bairro", "cidade", "uf"]
        widgets = {
            "cep": forms.TextInput(attrs={"class": "form-control cep", "placeholder": "00000-000"}),
            "logradouro": forms.TextInput(attrs={"class": "form-control", "placeholder": "Rua, Avenida, etc."}),
            "numero": forms.TextInput(attrs={"class": "form-control", "placeholder": "Número"}),
            "complemento": forms.TextInput(attrs={"class": "form-control", "placeholder": "Complemento (opcional)"}),
            "bairro": forms.TextInput(attrs={"class": "form-control", "placeholder": "Bairro"}),
            "cidade": forms.TextInput(attrs={"class": "form-control", "placeholder": "Cidade"}),
            "uf": forms.Select(attrs={"class": "form-select"}, choices=UF_CHOICES),
        }

    def clean_cep(self):
        cep = self.cleaned_data["cep"]
        digits = "".join(filter(str.isdigit, cep))
        if not digits or len(digits) != 8:
            raise forms.ValidationError("CEP inválido")
        return f"{digits[:5]}-{digits[5:]}"

    def clean_uf(self):
        uf = self.cleaned_data["uf"]
        if uf not in dict(UF_CHOICES).keys():
            raise forms.ValidationError("UF inválida")
        return uf
