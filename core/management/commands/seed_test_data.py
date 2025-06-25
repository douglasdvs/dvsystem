from django.core.management.base import BaseCommand
from clientes.models import Cliente
from produtos.models import Produto, CategoriaProduto
from pedidos.models import Pedido, ItemPedido
from financeiro.models import Receita, Despesa
from django.contrib.auth import get_user_model
from django.utils import timezone
import random
from decimal import Decimal

CATEGORIAS_RECEITA = ['pedido', 'servico', 'outros']
CATEGORIAS_DESPESA = ['devolucao', 'fornecedor', 'marketing', 'operacional', 'administrativo', 'impostos', 'outros']

class Command(BaseCommand):
    help = 'Popula o banco de dados com dados de teste (clientes, produtos, pedidos, financeiro)'

    def handle(self, *args, **kwargs):
        User = get_user_model()
        usuario = User.objects.first()
        if not usuario:
            self.stdout.write(self.style.ERROR('Nenhum usuário encontrado. Crie um superusuário antes.'))
            return

        # Criar categorias de produto
        cat_prod, _ = CategoriaProduto.objects.get_or_create(nome='Categoria Teste')

        # Criar clientes
        clientes = []
        for i in range(10):
            cliente = Cliente.objects.create(
                nome=f'Cliente Teste {i+1}',
                cpf_cnpj=f'0000000000{i+1}',
                telefone=f'(11) 90000-000{i+1}',
                email=f'cliente{i+1}@teste.com',
                ativo=True
            )
            clientes.append(cliente)
        self.stdout.write(self.style.SUCCESS('10 clientes criados.'))

        # Criar produtos
        produtos = []
        for i in range(10):
            produto = Produto.objects.create(
                descricao=f'Produto Teste {i+1}',
                categoria=cat_prod,
                preco_custo=Decimal('10.00') + i,
                margem_lucro=Decimal('20.00'),
                preco_venda=Decimal('12.00') + i,
                estoque=100,
                estoque_minimo=10,
                unidade_medida='UN',
                peso=Decimal('1.0')
            )
            produtos.append(produto)
        self.stdout.write(self.style.SUCCESS('10 produtos criados.'))

        # Criar pedidos
        for i in range(10):
            pedido = Pedido.objects.create(
                cliente=random.choice(clientes),
                data_pedido=timezone.now(),
                status='aberto',
                valor_sinal=Decimal('0.00')
            )
            # Adiciona 1 a 3 itens por pedido
            for _ in range(random.randint(1, 3)):
                ItemPedido.objects.create(
                    pedido=pedido,
                    produto=random.choice(produtos),
                    quantidade=random.randint(1, 5),
                    preco_unitario=Decimal('12.00')
                )
        self.stdout.write(self.style.SUCCESS('10 pedidos criados.'))

        # Criar receitas e despesas
        for i in range(10):
            Receita.objects.create(
                descricao=f'Receita Teste {i+1}',
                data=timezone.now(),
                valor=Decimal('100.00') + i,
                categoria=random.choice(CATEGORIAS_RECEITA),
                usuario=usuario
            )
            Despesa.objects.create(
                descricao=f'Despesa Teste {i+1}',
                data=timezone.now(),
                valor=Decimal('50.00') + i,
                categoria=random.choice(CATEGORIAS_DESPESA),
                usuario=usuario
            )
        self.stdout.write(self.style.SUCCESS('10 receitas e 10 despesas criadas.'))

        self.stdout.write(self.style.SUCCESS('População de dados de teste concluída!')) 