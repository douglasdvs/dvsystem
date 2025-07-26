from django import forms
from django.db.models import Max
from django.forms import inlineformset_factory
from django.utils.crypto import get_random_string
from django_select2.forms import Select2Widget

from .models import CATEGORIAS_PRODUTO, CategoriaProduto, HistoricoPreco, MovimentoEstoque, Produto


class ProdutoForm(forms.ModelForm):
    class Meta:
        model = Produto
        fields = [
            "descricao",
            "categoria",
            "preco_custo",
            "margem_lucro",
            "preco_venda",
            "estoque",
            "estoque_minimo",
            "unidade_medida",
            "ativo",
        ]
        widgets = {
            "descricao": forms.TextInput(attrs={"class": "form-control", "placeholder": "Nome do produto"}),
            "categoria": forms.Select(
                attrs={"class": "form-control select2", "data-placeholder": "Selecione uma categoria"}
            ),
            "preco_custo": forms.NumberInput(attrs={"class": "form-control", "step": "0.01", "min": "0"}),
            "margem_lucro": forms.NumberInput(attrs={"class": "form-control", "step": "0.01", "min": "0"}),
            "preco_venda": forms.NumberInput(attrs={"class": "form-control", "step": "0.01", "min": "0"}),
            "estoque": forms.NumberInput(attrs={"class": "form-control", "min": "0"}),
            "estoque_minimo": forms.NumberInput(attrs={"class": "form-control", "min": "0"}),
            "unidade_medida": forms.TextInput(attrs={"class": "form-control", "placeholder": "Ex: UN, KG, CX"}),
            "ativo": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["categoria"].queryset = CategoriaProduto.objects.filter(ativo=True)
        self.fields["categoria"].empty_label = "Selecione uma categoria"
        self.fields["categoria"].required = True

        # Campos obrigatórios
        campos_obrigatorios = ["descricao", "categoria", "preco_custo", "margem_lucro", "preco_venda"]
        for campo in campos_obrigatorios:
            self.fields[campo].required = True

        # Campos opcionais com valores padrão
        self.fields["estoque"].initial = 0
        self.fields["estoque_minimo"].initial = 5
        self.fields["unidade_medida"].initial = "UN"

    def clean(self):
        cleaned_data = super().clean()
        preco_custo = cleaned_data.get("preco_custo")
        margem_lucro = cleaned_data.get("margem_lucro")
        preco_venda = cleaned_data.get("preco_venda")
        estoque = cleaned_data.get("estoque")

        # Calcula preço de venda se não foi informado
        if preco_custo and margem_lucro and not preco_venda:
            cleaned_data["preco_venda"] = preco_custo * (1 + margem_lucro / 100)

        # Validações
        if preco_venda is not None and preco_custo is not None and preco_venda < preco_custo:
            self.add_error("preco_venda", "O preço de venda não pode ser menor que o preço de custo.")

        if estoque is not None and estoque < 0:
            self.add_error("estoque", "O estoque não pode ser negativo.")

        return cleaned_data

    def save(self, commit=True):
        try:
            is_new = self.instance.pk is None
            produto = super().save(commit=False)

            # Define valores padrão para campos não incluídos no formulário
            produto.peso = 0
            produto.despesas = 0
            produto.impostos = 0

            # Gera código se for novo produto
            if is_new and not produto.codigo:
                ultimo = Produto.objects.order_by("-codigo").first()
                if ultimo and ultimo.codigo:
                    try:
                        ultimo_numero = int(ultimo.codigo)
                        proximo_codigo = str(ultimo_numero + 1).zfill(5)
                    except ValueError:
                        proximo_codigo = str((ultimo.id + 1) if ultimo else 1).zfill(5)
                else:
                    proximo_codigo = "00001"
                produto.codigo = proximo_codigo

            if commit:
                produto.save()
            return produto
        except Exception as e:
            print(f"Erro ao salvar produto: {str(e)}")
            raise


class CategoriaProdutoForm(forms.ModelForm):
    class Meta:
        model = CategoriaProduto
        fields = ["nome", "descricao", "cor", "ativo"]
        widgets = {
            "nome": forms.TextInput(attrs={"class": "form-control"}),
            "descricao": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "cor": forms.TextInput(attrs={"class": "form-control", "type": "color"}),
            "ativo": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }
        labels = {
            "nome": "Nome da Categoria",
            "descricao": "Descrição",
            "cor": "Cor",
            "ativo": "Ativo",
        }


class FiltroAvancadoForm(forms.Form):
    categoria = forms.ChoiceField(
        required=False,
        choices=[("", "Todas as Categorias")] + list(CATEGORIAS_PRODUTO),
        widget=forms.Select(attrs={"class": "form-control"}),
    )
    categoria_nova = forms.ModelChoiceField(
        required=False,
        queryset=CategoriaProduto.objects.filter(ativo=True),
        empty_label="Todas as Categorias Novas",
        widget=forms.Select(attrs={"class": "form-control"}),
    )
    status = forms.ChoiceField(
        required=False,
        choices=[
            ("", "Todos"),
            ("ativos", "Ativos"),
            ("inativos", "Inativos"),
            ("promocao", "Em Promoção"),
            ("destaque", "Em Destaque"),
        ],
        widget=forms.Select(attrs={"class": "form-control"}),
    )
    estoque = forms.ChoiceField(
        required=False,
        choices=[("", "Todos"), ("baixo", "Estoque Baixo"), ("zerado", "Sem Estoque"), ("disponivel", "Com Estoque")],
        widget=forms.Select(attrs={"class": "form-control"}),
    )
    preco_min = forms.DecimalField(
        required=False, widget=forms.NumberInput(attrs={"class": "form-control", "placeholder": "Preço Mínimo"})
    )
    preco_max = forms.DecimalField(
        required=False, widget=forms.NumberInput(attrs={"class": "form-control", "placeholder": "Preço Máximo"})
    )
    busca = forms.CharField(
        required=False, widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Buscar..."})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        categorias = [("", "Todas as Categorias")] + list(CATEGORIAS_PRODUTO)
        self.fields["categoria"].choices = categorias


class ImportarProdutosForm(forms.Form):
    arquivo = forms.FileField(
        widget=forms.FileInput(attrs={"class": "form-control"}),
        help_text="Arquivo Excel ou CSV com produtos para importar",
    )
    atualizar_existentes = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
        help_text="Atualizar produtos existentes (por código)",
    )


class MovimentoEstoqueForm(forms.ModelForm):
    class Meta:
        model = MovimentoEstoque
        fields = "__all__"
        widgets = {
            "produto": forms.Select(attrs={"class": "form-control"}),
            "tipo": forms.Select(attrs={"class": "form-control"}),
            "quantidade": forms.NumberInput(attrs={"class": "form-control", "min": "1"}),
            "data": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "observacoes": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }

    def clean_quantidade(self):
        quantidade = self.cleaned_data.get("quantidade")
        if quantidade is not None and quantidade <= 0:
            raise forms.ValidationError("A quantidade deve ser maior que zero.")
        return quantidade
