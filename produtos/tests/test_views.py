import pytest
from decimal import Decimal
from django.urls import reverse
from produtos.models import Produto, CategoriaProduto

pytestmark = pytest.mark.django_db

class TestProdutoViews:
    def test_listar_produtos(self, client, produtos_list):
        """Testa listagem de produtos"""
        url = reverse('produtos:listar')
        response = client.get(url)
        assert response.status_code == 200
        assert len(response.context['produtos']) == len(produtos_list)

    def test_criar_produto(self, client, categoria_produto):
        """Testa criação de produto"""
        url = reverse('produtos:novo')
        data = {
            'descricao': 'Novo Produto',
            'categoria': categoria_produto.id,
            'preco_custo': '10.00',
            'margem_lucro': '20.00',
            'estoque': '10',
            'estoque_minimo': '5',
            'unidade_medida': 'UN',
            'peso': '1.000'
        }
        response = client.post(url, data)
        assert response.status_code == 302  # Redirecionamento após sucesso
        
        produto = Produto.objects.get(descricao='Novo Produto')
        assert produto.preco_custo == Decimal('10.00')
        assert produto.margem_lucro == Decimal('20.00')

    def test_editar_produto(self, client, produto):
        """Testa edição de produto"""
        url = reverse('produtos:editar', args=[produto.id])
        data = {
            'descricao': 'Produto Editado',
            'categoria': produto.categoria.id,
            'preco_custo': '15.00',
            'margem_lucro': '25.00',
            'estoque': '20',
            'estoque_minimo': '10',
            'unidade_medida': 'UN',
            'peso': '1.000'
        }
        response = client.post(url, data)
        assert response.status_code == 302  # Redirecionamento após sucesso
        
        produto.refresh_from_db()
        assert produto.descricao == 'Produto Editado'
        assert produto.preco_custo == Decimal('15.00')
        assert produto.margem_lucro == Decimal('25.00')

    def test_excluir_produto(self, client, produto):
        """Testa exclusão de produto"""
        url = reverse('produtos:excluir', args=[produto.id])
        response = client.post(url)
        assert response.status_code == 302  # Redirecionamento após sucesso
        
        with pytest.raises(Produto.DoesNotExist):
            Produto.objects.get(id=produto.id)

    def test_detalhe_produto(self, client, produto):
        """Testa visualização de detalhes do produto"""
        url = reverse('produtos:detalhe', args=[produto.id])
        response = client.get(url)
        assert response.status_code == 200
        assert response.context['produto'].id == produto.id

    def test_atualizar_estoque(self, client, produto):
        """Testa atualização de estoque"""
        url = reverse('produtos:atualizar_estoque', args=[produto.id])
        estoque_inicial = produto.estoque
        
        # Teste entrada de estoque
        data = {
            'tipo': 'E',
            'quantidade': 5,
            'observacao': 'Entrada de teste'
        }
        response = client.post(url, data)
        assert response.status_code == 302
        
        produto.refresh_from_db()
        assert produto.estoque == estoque_inicial + 5
        
        # Teste saída de estoque
        data = {
            'tipo': 'S',
            'quantidade': 3,
            'observacao': 'Saída de teste'
        }
        response = client.post(url, data)
        assert response.status_code == 302
        
        produto.refresh_from_db()
        assert produto.estoque == estoque_inicial + 2

    def test_atualizar_estoque_insuficiente(self, client, produto):
        """Testa tentativa de saída com estoque insuficiente"""
        url = reverse('produtos:atualizar_estoque', args=[produto.id])
        data = {
            'tipo': 'S',
            'quantidade': produto.estoque + 1,
            'observacao': 'Saída inválida'
        }
        response = client.post(url, data)
        assert response.status_code == 200  # Retorna para o formulário
        assert 'error' in response.context

class TestCategoriaViews:
    def test_listar_categorias(self, client, categoria_produto):
        """Testa listagem de categorias"""
        url = reverse('produtos:listar_categorias')
        response = client.get(url)
        assert response.status_code == 200
        assert categoria_produto in response.context['categorias']

    def test_criar_categoria(self, client):
        """Testa criação de categoria"""
        url = reverse('produtos:nova_categoria')
        data = {
            'nome': 'Nova Categoria',
            'descricao': 'Descrição da nova categoria'
        }
        response = client.post(url, data)
        assert response.status_code == 302
        
        categoria = CategoriaProduto.objects.get(nome='Nova Categoria')
        assert categoria.descricao == 'Descrição da nova categoria'

    def test_editar_categoria(self, client, categoria_produto):
        """Testa edição de categoria"""
        url = reverse('produtos:editar_categoria', args=[categoria_produto.id])
        data = {
            'nome': 'Categoria Editada',
            'descricao': 'Nova descrição'
        }
        response = client.post(url, data)
        assert response.status_code == 302
        
        categoria_produto.refresh_from_db()
        assert categoria_produto.nome == 'Categoria Editada'
        assert categoria_produto.descricao == 'Nova descrição'

    def test_excluir_categoria(self, client, categoria_produto):
        """Testa exclusão de categoria"""
        url = reverse('produtos:excluir_categoria', args=[categoria_produto.id])
        response = client.post(url)
        assert response.status_code == 302
        
        with pytest.raises(CategoriaProduto.DoesNotExist):
            CategoriaProduto.objects.get(id=categoria_produto.id) 