from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError

from clientes.models import Cliente, Endereco, TipoCliente

pytestmark = pytest.mark.django_db


class TestTipoCliente:
    def test_criar_tipo_cliente(self, tipo_cliente):
        """Testa a criação de um tipo de cliente"""
        assert tipo_cliente.id is not None
        assert tipo_cliente.nome
        assert tipo_cliente.descricao
        assert 0 <= tipo_cliente.desconto_padrao <= 100

    def test_str_tipo_cliente(self, tipo_cliente):
        """Testa o método __str__ do tipo de cliente"""
        assert str(tipo_cliente) == tipo_cliente.nome

    def test_desconto_negativo(self):
        """Testa validação de desconto negativo"""
        with pytest.raises(ValidationError):
            tipo = TipoCliente(nome="Tipo Teste", descricao="Descrição teste", desconto_padrao=Decimal("-10.00"))
            tipo.full_clean()

    def test_desconto_maior_100(self):
        """Testa validação de desconto maior que 100%"""
        with pytest.raises(ValidationError):
            tipo = TipoCliente(nome="Tipo Teste", descricao="Descrição teste", desconto_padrao=Decimal("150.00"))
            tipo.full_clean()


class TestEndereco:
    def test_criar_endereco(self, endereco):
        """Testa a criação de um endereço"""
        assert endereco.id is not None
        assert endereco.cep
        assert endereco.logradouro
        assert endereco.numero
        assert endereco.bairro
        assert endereco.cidade
        assert endereco.uf

    def test_str_endereco(self, endereco):
        """Testa o método __str__ do endereço"""
        endereco_str = f"{endereco.logradouro}, {endereco.numero}"
        if endereco.complemento:
            endereco_str += f" - {endereco.complemento}"
        assert str(endereco) == endereco_str

    def test_cep_invalido(self):
        """Testa validação de CEP inválido"""
        with pytest.raises(ValidationError):
            endereco = Endereco(
                cep="123", logradouro="Rua Teste", numero="123", bairro="Centro", cidade="São Paulo", uf="SP"
            )
            endereco.full_clean()


class TestCliente:
    def test_criar_cliente(self, cliente):
        """Testa a criação de um cliente"""
        assert cliente.id is not None
        assert cliente.nome
        assert cliente.email
        assert cliente.telefone
        assert cliente.cpf_cnpj
        assert cliente.tipo_cliente
        assert cliente.ativo is True
        assert cliente.enderecos.count() > 0

    def test_str_cliente(self, cliente):
        """Testa o método __str__ do cliente"""
        assert str(cliente) == cliente.nome

    def test_cpf_cnpj_invalido(self, tipo_cliente):
        """Testa validação de CPF/CNPJ inválido"""
        with pytest.raises(ValidationError):
            cliente = Cliente(
                nome="Cliente Teste",
                email="teste@teste.com",
                telefone="(11) 1234-5678",
                cpf_cnpj="123",  # CPF inválido
                tipo_cliente=tipo_cliente,
            )
            cliente.full_clean()

    def test_email_invalido(self, tipo_cliente):
        """Testa validação de email inválido"""
        with pytest.raises(ValidationError):
            cliente = Cliente(
                nome="Cliente Teste",
                email="email_invalido",
                telefone="(11) 1234-5678",
                cpf_cnpj="12345678901",
                tipo_cliente=tipo_cliente,
            )
            cliente.full_clean()

    def test_telefone_invalido(self, tipo_cliente):
        """Testa validação de telefone inválido"""
        with pytest.raises(ValidationError):
            cliente = Cliente(
                nome="Cliente Teste",
                email="teste@teste.com",
                telefone="123",  # Telefone inválido
                cpf_cnpj="12345678901",
                tipo_cliente=tipo_cliente,
            )
            cliente.full_clean()

    def test_cliente_sem_endereco(self, tipo_cliente):
        """Testa criação de cliente sem endereço"""
        cliente = Cliente.objects.create(
            nome="Cliente Teste",
            email="teste@teste.com",
            telefone="(11) 1234-5678",
            cpf_cnpj="12345678901",
            tipo_cliente=tipo_cliente,
        )
        assert cliente.enderecos.count() == 0

    def test_cliente_multiplos_enderecos(self, cliente, endereco):
        """Testa cliente com múltiplos endereços"""
        novo_endereco = EnderecoFactory()
        cliente.enderecos.add(novo_endereco)
        assert cliente.enderecos.count() == 2
