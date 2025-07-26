from django.db import transaction

from clientes.models import Cliente


def atualizar_codigos_vazios():
    with transaction.atomic():
        clientes = Cliente.objects.filter(codigo__isnull=True) | Cliente.objects.filter(codigo="")
        seq = 1
        for cliente in clientes.order_by("id"):
            novo_codigo = str(seq).zfill(5)
            # Garante que não vai gerar código duplicado
            while Cliente.objects.filter(codigo=novo_codigo).exists():
                seq += 1
                novo_codigo = str(seq).zfill(5)
            cliente.codigo = novo_codigo
            cliente.save(update_fields=["codigo"])
            seq += 1
    print(f"Corrigidos {clientes.count()} clientes com código vazio ou nulo.")


if __name__ == "__main__":
    atualizar_codigos_vazios()
