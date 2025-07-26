from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError

from produtos.models import CategoriaProduto, Produto

pytestmark = pytest.mark.django_db


class TestCategoriaProduto:
    def test_criar_categoria(self, categoria_produto):
        """Testa a criação de uma categoria de produto"""
        assert categoria_produto.id is not None
        assert categoria_produto.nome
        assert categoria_produto.descricao

    def test_str_categoria(self, categoria_produto):
        """Testa o método __str__ da categoria"""
        assert str(categoria_produto) == categoria_produto.nome


class TestProduto:
    def test_criar_produto(self, produto):
        """Testa a criação de um produto"""
        assert produto.id is not None
        assert produto.descricao
        assert produto.preco_custo > 0
        assert produto.margem_lucro > 0
        assert produto.estoque >= 0
        assert produto.estoque_minimo > 0

    def test_str_produto(self, produto):
        """Testa o método __str__ do produto"""
        assert str(produto) == produto.descricao

    def test_calculo_preco_venda(self, produto):
        """Testa o cálculo do preço de venda"""
        preco_venda_esperado = produto.preco_custo * (1 + produto.margem_lucro / 100)
        assert produto.preco_venda == preco_venda_esperado

    def test_estoque_negativo(self):
        """Testa validação de estoque negativo"""
        with pytest.raises(ValidationError):
            produto = Produto(
                descricao="Produto Teste", preco_custo=Decimal("10.00"), margem_lucro=Decimal("20.00"), estoque=-1
            )
            produto.full_clean()

    def test_preco_venda_menor_custo(self):
        """Testa validação de preço de venda menor que custo"""
        with pytest.raises(ValidationError):
            produto = Produto(
                descricao="Produto Teste",
                preco_custo=Decimal("10.00"),
                margem_lucro=Decimal("-50.00"),  # Isso fará o preço de venda ser menor que o custo
            )
            produto.full_clean()

    def test_atualizar_estoque(self, produto):
        """Testa a atualização de estoque"""
        estoque_inicial = produto.estoque
        quantidade = 5

        produto.atualizar_estoque(quantidade, "E")  # Entrada
        assert produto.estoque == estoque_inicial + quantidade

        produto.atualizar_estoque(quantidade, "S")  # Saída
        assert produto.estoque == estoque_inicial

    def test_atualizar_estoque_insuficiente(self, produto):
        """Testa tentativa de saída com estoque insuficiente"""
        with pytest.raises(ValueError):
            produto.atualizar_estoque(produto.estoque + 1, "S")  # Tenta sair mais que tem

    def test_produto_em_baixo_estoque(self, produto):
        """Testa verificação de produto em baixo estoque"""
        produto.estoque = produto.estoque_minimo - 1
        assert produto.em_baixo_estoque is True

        produto.estoque = produto.estoque_minimo
        assert produto.em_baixo_estoque is False
