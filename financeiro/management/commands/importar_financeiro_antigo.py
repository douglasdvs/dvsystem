import csv
from datetime import datetime

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from clientes.models import Cliente
from financeiro.models import CentroCusto, Despesa, Receita
from pedidos.models import Pedido

RECEITAS_CSV = "temp/receitas_antigas_utf8.csv"
DESPESAS_CSV = "temp/despesas_antigas_utf8.csv"


class Command(BaseCommand):
    help = "Importa receitas e despesas do financeiro do banco antigo (CSV) para o novo banco."

    def handle(self, *args, **options):
        self.importar_receitas()
        self.importar_despesas()

    def importar_receitas(self):
        with open(RECEITAS_CSV, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            count = 0
            for row in reader:
                cliente = Cliente.objects.filter(pk=row.get("cliente_id")).first() if row.get("cliente_id") else None
                pedido = Pedido.objects.filter(pk=row.get("pedido_id")).first() if row.get("pedido_id") else None
                usuario = User.objects.filter(pk=row.get("usuario_id")).first() if row.get("usuario_id") else None
                receita, created = Receita.objects.get_or_create(
                    descricao=row.get("descricao", "")[:255],
                    data=row.get("data") or datetime.now().date(),
                    valor=row.get("valor") or 0,
                    categoria=row.get("categoria") or "pedido",
                    cliente=cliente,
                    pedido=pedido,
                    forma_pagamento=row.get("forma_pagamento") or "dinheiro",
                    status=row.get("status") or "P",
                    usuario=usuario or User.objects.first(),
                )
                count += 1
            self.stdout.write(self.style.SUCCESS(f"Importadas {count} receitas."))

    def importar_despesas(self):
        with open(DESPESAS_CSV, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            count = 0
            for row in reader:
                centro_custo = (
                    CentroCusto.objects.filter(pk=row.get("centro_custo_id")).first()
                    if row.get("centro_custo_id")
                    else None
                )
                usuario = User.objects.filter(pk=row.get("usuario_id")).first() if row.get("usuario_id") else None
                despesa, created = Despesa.objects.get_or_create(
                    descricao=row.get("descricao", "")[:255],
                    data=row.get("data") or datetime.now().date(),
                    valor=row.get("valor") or 0,
                    categoria=row.get("categoria") or "outros",
                    centro_custo=centro_custo,
                    forma_pagamento=row.get("forma_pagamento") or "dinheiro",
                    status=row.get("status") or "P",
                    usuario=usuario or User.objects.first(),
                )
                count += 1
            self.stdout.write(self.style.SUCCESS(f"Importadas {count} despesas."))
