import pytest
from clientes.forms import ClienteForm, EnderecoForm, TipoClienteForm
from clientes.models import Cliente, Endereco, TipoCliente

pytestmark = pytest.mark.django_db

class TestClienteForm:
    def test_form_valido(self, tipo_cliente):
        """Testa formulário com dados válidos"""
        form_data = {
            'nome': 'Cliente Teste',
            'email': 'teste@teste.com',
            'telefone': '(11) 1234-5678',
            'cpf_cnpj': '12345678901',
            'tipo_cliente': tipo_cliente.id,
            'observacoes': 'Observações do cliente'
        }
        form = ClienteForm(data=form_data)
        assert form.is_valid()
        
        cliente = form.save()
        assert cliente.nome == 'Cliente Teste'
        assert cliente.email == 'teste@teste.com'
        assert cliente.telefone == '(11) 1234-5678'
        assert cliente.cpf_cnpj == '12345678901'
        assert cliente.tipo_cliente == tipo_cliente

    def test_form_invalido_cpf(self, tipo_cliente):
        """Testa formulário com CPF inválido"""
        form_data = {
            'nome': 'Cliente Teste',
            'email': 'teste@teste.com',
            'telefone': '(11) 1234-5678',
            'cpf_cnpj': '123',  # CPF inválido
            'tipo_cliente': tipo_cliente.id
        }
        form = ClienteForm(data=form_data)
        assert not form.is_valid()
        assert 'cpf_cnpj' in form.errors

    def test_form_invalido_email(self, tipo_cliente):
        """Testa formulário com email inválido"""
        form_data = {
            'nome': 'Cliente Teste',
            'email': 'email_invalido',
            'telefone': '(11) 1234-5678',
            'cpf_cnpj': '12345678901',
            'tipo_cliente': tipo_cliente.id
        }
        form = ClienteForm(data=form_data)
        assert not form.is_valid()
        assert 'email' in form.errors

    def test_form_invalido_telefone(self, tipo_cliente):
        """Testa formulário com telefone inválido"""
        form_data = {
            'nome': 'Cliente Teste',
            'email': 'teste@teste.com',
            'telefone': '123',  # Telefone inválido
            'cpf_cnpj': '12345678901',
            'tipo_cliente': tipo_cliente.id
        }
        form = ClienteForm(data=form_data)
        assert not form.is_valid()
        assert 'telefone' in form.errors

class TestEnderecoForm:
    def test_form_valido(self):
        """Testa formulário com dados válidos"""
        form_data = {
            'cep': '12345678',
            'logradouro': 'Rua Teste',
            'numero': '123',
            'complemento': 'Apto 45',
            'bairro': 'Centro',
            'cidade': 'São Paulo',
            'uf': 'SP'
        }
        form = EnderecoForm(data=form_data)
        assert form.is_valid()
        
        endereco = form.save()
        assert endereco.cep == '12345678'
        assert endereco.logradouro == 'Rua Teste'
        assert endereco.numero == '123'
        assert endereco.complemento == 'Apto 45'
        assert endereco.bairro == 'Centro'
        assert endereco.cidade == 'São Paulo'
        assert endereco.uf == 'SP'

    def test_form_invalido_cep(self):
        """Testa formulário com CEP inválido"""
        form_data = {
            'cep': '123',  # CEP inválido
            'logradouro': 'Rua Teste',
            'numero': '123',
            'bairro': 'Centro',
            'cidade': 'São Paulo',
            'uf': 'SP'
        }
        form = EnderecoForm(data=form_data)
        assert not form.is_valid()
        assert 'cep' in form.errors

    def test_form_invalido_uf(self):
        """Testa formulário com UF inválida"""
        form_data = {
            'cep': '12345678',
            'logradouro': 'Rua Teste',
            'numero': '123',
            'bairro': 'Centro',
            'cidade': 'São Paulo',
            'uf': 'XX'  # UF inválida
        }
        form = EnderecoForm(data=form_data)
        assert not form.is_valid()
        assert 'uf' in form.errors

class TestTipoClienteForm:
    def test_form_valido(self):
        """Testa formulário com dados válidos"""
        form_data = {
            'nome': 'Tipo Teste',
            'descricao': 'Descrição do tipo',
            'desconto_padrao': '10.00'
        }
        form = TipoClienteForm(data=form_data)
        assert form.is_valid()
        
        tipo = form.save()
        assert tipo.nome == 'Tipo Teste'
        assert tipo.descricao == 'Descrição do tipo'
        assert float(tipo.desconto_padrao) == 10.00

    def test_form_invalido_desconto_negativo(self):
        """Testa formulário com desconto negativo"""
        form_data = {
            'nome': 'Tipo Teste',
            'descricao': 'Descrição do tipo',
            'desconto_padrao': '-10.00'
        }
        form = TipoClienteForm(data=form_data)
        assert not form.is_valid()
        assert 'desconto_padrao' in form.errors

    def test_form_invalido_desconto_maior_100(self):
        """Testa formulário com desconto maior que 100%"""
        form_data = {
            'nome': 'Tipo Teste',
            'descricao': 'Descrição do tipo',
            'desconto_padrao': '150.00'
        }
        form = TipoClienteForm(data=form_data)
        assert not form.is_valid()
        assert 'desconto_padrao' in form.errors 