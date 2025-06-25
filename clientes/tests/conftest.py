import pytest
from django.contrib.auth.models import User
from clientes.models import Cliente, TipoCliente, Endereco
from factory import Faker, SubFactory
from factory.django import DjangoModelFactory

class UserFactory(DjangoModelFactory):
    class Meta:
        model = User
    
    username = Faker('user_name')
    email = Faker('email')
    password = Faker('password')

class TipoClienteFactory(DjangoModelFactory):
    class Meta:
        model = TipoCliente
    
    nome = Faker('word')
    descricao = Faker('sentence')
    desconto_padrao = Faker('pydecimal', left_digits=2, right_digits=2, positive=True, max_value=100)

class EnderecoFactory(DjangoModelFactory):
    class Meta:
        model = Endereco
    
    cep = Faker('numerify', text='########')
    logradouro = Faker('street_name')
    numero = Faker('building_number')
    complemento = Faker('secondary_address')
    bairro = Faker('neighborhood')
    cidade = Faker('city')
    uf = Faker('state_abbr')

class ClienteFactory(DjangoModelFactory):
    class Meta:
        model = Cliente
    
    nome = Faker('name')
    email = Faker('email')
    telefone = Faker('phone_number')
    cpf_cnpj = Faker('numerify', text='###########')
    tipo_cliente = SubFactory(TipoClienteFactory)
    observacoes = Faker('paragraph')
    ativo = True

@pytest.fixture
def user():
    return UserFactory()

@pytest.fixture
def tipo_cliente():
    return TipoClienteFactory()

@pytest.fixture
def endereco():
    return EnderecoFactory()

@pytest.fixture
def cliente(tipo_cliente, endereco):
    cliente = ClienteFactory(tipo_cliente=tipo_cliente)
    cliente.enderecos.add(endereco)
    return cliente

@pytest.fixture
def clientes_list(tipo_cliente):
    return ClienteFactory.create_batch(5, tipo_cliente=tipo_cliente) 