import pytest
from django.contrib.auth.models import User
from produtos.models import Produto, CategoriaProduto
from factory import Faker
from factory.django import DjangoModelFactory

class UserFactory(DjangoModelFactory):
    class Meta:
        model = User
    
    username = Faker('user_name')
    email = Faker('email')
    password = Faker('password')

class CategoriaProdutoFactory(DjangoModelFactory):
    class Meta:
        model = CategoriaProduto
    
    nome = Faker('word')
    descricao = Faker('sentence')

class ProdutoFactory(DjangoModelFactory):
    class Meta:
        model = Produto
    
    descricao = Faker('word')
    preco_custo = Faker('pydecimal', left_digits=5, right_digits=2, positive=True)
    margem_lucro = Faker('pydecimal', left_digits=3, right_digits=2, positive=True)
    estoque = Faker('pyint', min_value=0, max_value=100)
    estoque_minimo = Faker('pyint', min_value=1, max_value=10)
    unidade_medida = 'UN'
    peso = Faker('pydecimal', left_digits=3, right_digits=3, positive=True)

@pytest.fixture
def user():
    return UserFactory()

@pytest.fixture
def categoria_produto():
    return CategoriaProdutoFactory()

@pytest.fixture
def produto(categoria_produto):
    return ProdutoFactory(categoria=categoria_produto)

@pytest.fixture
def produtos_list(categoria_produto):
    return ProdutoFactory.create_batch(5, categoria=categoria_produto) 