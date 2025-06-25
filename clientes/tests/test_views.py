import pytest
from django.urls import reverse
from clientes.models import Cliente, TipoCliente, Endereco

pytestmark = pytest.mark.django_db

class TestClienteViews:
    def test_listar_clientes(self, client, clientes_list):
        """Testa listagem de clientes"""
        url = reverse('clientes:listar')
        response = client.get(url)
        assert response.status_code == 200
        assert len(response.context['clientes']) == len(clientes_list)

    def test_criar_cliente(self, client, tipo_cliente):
        """Testa criação de cliente"""
        url = reverse('clientes:novo')
        data = {
            'nome': 'Novo Cliente',
            'email': 'novo@teste.com',
            'telefone': '(11) 98765-4321',
            'cpf_cnpj': '12345678901',
            'tipo_cliente': tipo_cliente.id,
            'observacoes': 'Observações do novo cliente'
        }
        response = client.post(url, data)
        assert response.status_code == 302  # Redirecionamento após sucesso
        
        cliente = Cliente.objects.get(nome='Novo Cliente')
        assert cliente.email == 'novo@teste.com'
        assert cliente.telefone == '(11) 98765-4321'
        assert cliente.tipo_cliente == tipo_cliente

    def test_editar_cliente(self, client, cliente):
        """Testa edição de cliente"""
        url = reverse('clientes:editar', args=[cliente.id])
        data = {
            'nome': 'Cliente Editado',
            'email': 'editado@teste.com',
            'telefone': '(11) 98765-4321',
            'cpf_cnpj': cliente.cpf_cnpj,
            'tipo_cliente': cliente.tipo_cliente.id,
            'observacoes': 'Observações editadas'
        }
        response = client.post(url, data)
        assert response.status_code == 302
        
        cliente.refresh_from_db()
        assert cliente.nome == 'Cliente Editado'
        assert cliente.email == 'editado@teste.com'
        assert cliente.telefone == '(11) 98765-4321'

    def test_excluir_cliente(self, client, cliente):
        """Testa exclusão de cliente"""
        url = reverse('clientes:excluir', args=[cliente.id])
        response = client.post(url)
        assert response.status_code == 302
        
        with pytest.raises(Cliente.DoesNotExist):
            Cliente.objects.get(id=cliente.id)

    def test_detalhe_cliente(self, client, cliente):
        """Testa visualização de detalhes do cliente"""
        url = reverse('clientes:detalhe', args=[cliente.id])
        response = client.get(url)
        assert response.status_code == 200
        assert response.context['cliente'].id == cliente.id

    def test_buscar_cep(self, client):
        """Testa busca de CEP"""
        url = reverse('clientes:buscar_cep')
        response = client.get(url, {'cep': '01001000'})  # CEP do Correios
        assert response.status_code == 200
        data = response.json()
        assert 'logradouro' in data
        assert 'bairro' in data
        assert 'cidade' in data
        assert 'uf' in data

    def test_buscar_cep_invalido(self, client):
        """Testa busca de CEP inválido"""
        url = reverse('clientes:buscar_cep')
        response = client.get(url, {'cep': '123'})
        assert response.status_code == 400
        data = response.json()
        assert 'error' in data

class TestTipoClienteViews:
    def test_listar_tipos(self, client, tipo_cliente):
        """Testa listagem de tipos de cliente"""
        url = reverse('clientes:tipos_cliente')
        response = client.get(url)
        assert response.status_code == 200
        assert tipo_cliente in response.context['tipos']

    def test_criar_tipo(self, client):
        """Testa criação de tipo de cliente"""
        url = reverse('clientes:novo_tipo')
        data = {
            'nome': 'Novo Tipo',
            'descricao': 'Descrição do novo tipo',
            'desconto_padrao': '15.00'
        }
        response = client.post(url, data)
        assert response.status_code == 302
        
        tipo = TipoCliente.objects.get(nome='Novo Tipo')
        assert tipo.descricao == 'Descrição do novo tipo'
        assert float(tipo.desconto_padrao) == 15.00

    def test_editar_tipo(self, client, tipo_cliente):
        """Testa edição de tipo de cliente"""
        url = reverse('clientes:editar_tipo', args=[tipo_cliente.id])
        data = {
            'nome': 'Tipo Editado',
            'descricao': 'Nova descrição',
            'desconto_padrao': '20.00'
        }
        response = client.post(url, data)
        assert response.status_code == 302
        
        tipo_cliente.refresh_from_db()
        assert tipo_cliente.nome == 'Tipo Editado'
        assert tipo_cliente.descricao == 'Nova descrição'
        assert float(tipo_cliente.desconto_padrao) == 20.00

    def test_excluir_tipo(self, client, tipo_cliente):
        """Testa exclusão de tipo de cliente"""
        url = reverse('clientes:excluir_tipo', args=[tipo_cliente.id])
        response = client.post(url)
        assert response.status_code == 302
        
        with pytest.raises(TipoCliente.DoesNotExist):
            TipoCliente.objects.get(id=tipo_cliente.id)

    def test_excluir_tipo_em_uso(self, client, cliente):
        """Testa tentativa de excluir tipo de cliente em uso"""
        url = reverse('clientes:excluir_tipo', args=[cliente.tipo_cliente.id])
        response = client.post(url)
        assert response.status_code == 302  # Redirecionamento
        assert TipoCliente.objects.filter(id=cliente.tipo_cliente.id).exists()  # Tipo não foi excluído

class TestEnderecoViews:
    def test_adicionar_endereco(self, client, cliente):
        """Testa adição de endereço a um cliente"""
        url = reverse('clientes:adicionar_endereco', args=[cliente.id])
        data = {
            'cep': '12345678',
            'logradouro': 'Rua Teste',
            'numero': '123',
            'complemento': 'Apto 45',
            'bairro': 'Centro',
            'cidade': 'São Paulo',
            'uf': 'SP'
        }
        response = client.post(url, data)
        assert response.status_code == 302, "A view deve redirecionar após salvar o endereço."
        assert cliente.enderecos.count() == 2, "O cliente deve ter dois endereços (um do fixture e um novo)."
        novo_endereco = cliente.enderecos.latest('id')
        assert novo_endereco.cep == '12345678', "O CEP do novo endereço deve ser 12345678."
        assert novo_endereco.logradouro == 'Rua Teste', "O logradouro do novo endereço deve ser 'Rua Teste'."

    def test_editar_endereco(self, client, cliente, endereco):
        """Testa edição de endereço"""
        url = reverse('clientes:editar_endereco', args=[endereco.id])
        data = {
            'cep': '87654321',
            'logradouro': 'Avenida Editada',
            'numero': '456',
            'complemento': 'Sala 789',
            'bairro': 'Jardim',
            'cidade': 'Rio de Janeiro',
            'uf': 'RJ'
        }
        response = client.post(url, data)
        assert response.status_code == 302, "A view deve redirecionar após atualizar o endereço."
        endereco.refresh_from_db()
        assert endereco.cep == '87654321', "O CEP do endereço deve ser atualizado para 87654321."
        assert endereco.logradouro == 'Avenida Editada', "O logradouro do endereço deve ser atualizado para 'Avenida Editada'."
        assert endereco.cidade == 'Rio de Janeiro', "A cidade do endereço deve ser atualizada para 'Rio de Janeiro'."

    def test_excluir_endereco(self, client, cliente, endereco):
        """Testa exclusão de endereço"""
        url = reverse('clientes:excluir_endereco', args=[endereco.id])
        response = client.post(url)
        assert response.status_code == 302, "A view deve redirecionar após excluir o endereço."
        assert not cliente.enderecos.filter(id=endereco.id).exists(), "O endereço não deve mais existir no banco de dados." 