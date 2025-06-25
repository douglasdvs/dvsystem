import pytest
from decimal import Decimal
from produtos.forms import ProdutoForm, ImportarProdutosForm
from produtos.models import Produto

pytestmark = pytest.mark.django_db

class TestProdutoForm:
    def test_form_valido(self, categoria_produto):
        """Testa formulário com dados válidos"""
        form_data = {
            'descricao': 'Produto Teste',
            'categoria': categoria_produto.id,
            'preco_custo': '10.00',
            'margem_lucro': '20.00',
            'estoque': '10',
            'estoque_minimo': '5',
            'unidade_medida': 'UN',
            'peso': '1.000'
        }
        form = ProdutoForm(data=form_data)
        assert form.is_valid()
        
        produto = form.save()
        assert produto.descricao == 'Produto Teste'
        assert produto.preco_custo == Decimal('10.00')
        assert produto.margem_lucro == Decimal('20.00')
        assert produto.estoque == 10
        assert produto.estoque_minimo == 5

    def test_form_invalido_preco_negativo(self):
        """Testa formulário com preço negativo"""
        form_data = {
            'descricao': 'Produto Teste',
            'preco_custo': '-10.00',
            'margem_lucro': '20.00',
            'estoque': '10',
            'estoque_minimo': '5'
        }
        form = ProdutoForm(data=form_data)
        assert not form.is_valid()
        assert 'preco_custo' in form.errors

    def test_form_invalido_estoque_negativo(self):
        """Testa formulário com estoque negativo"""
        form_data = {
            'descricao': 'Produto Teste',
            'preco_custo': '10.00',
            'margem_lucro': '20.00',
            'estoque': '-1',
            'estoque_minimo': '5'
        }
        form = ProdutoForm(data=form_data)
        assert not form.is_valid()
        assert 'estoque' in form.errors

    def test_form_calculo_preco_venda(self):
        """Testa cálculo automático do preço de venda"""
        form_data = {
            'descricao': 'Produto Teste',
            'preco_custo': '10.00',
            'margem_lucro': '20.00',
            'estoque': '10',
            'estoque_minimo': '5'
        }
        form = ProdutoForm(data=form_data)
        assert form.is_valid()
        
        produto = form.save()
        preco_venda_esperado = Decimal('10.00') * (1 + Decimal('20.00')/100)
        assert produto.preco_venda == preco_venda_esperado

class TestImportarProdutosForm:
    def test_form_valido(self):
        """Testa formulário de importação com dados válidos"""
        form_data = {
            'atualizar_existentes': True
        }
        form = ImportarProdutosForm(data=form_data)
        assert form.is_valid()

    def test_form_sem_arquivo(self):
        """Testa formulário de importação sem arquivo"""
        form_data = {
            'atualizar_existentes': True
        }
        form = ImportarProdutosForm(data=form_data, files={})
        assert not form.is_valid()
        assert 'arquivo' in form.errors 