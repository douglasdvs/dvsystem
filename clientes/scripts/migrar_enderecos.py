import os
import sys

import django

# Garante que o diretório raiz do projeto está no sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


sys.path.insert(0, PROJECT_ROOT)
print("sys.path:", sys.path)
print("PROJECT_ROOT:", PROJECT_ROOT)
print("Conteúdo de PROJECT_ROOT:", os.listdir(PROJECT_ROOT))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dvsystem.settings")
django.setup()

from django.db import transaction

from clientes.models import Cliente, Endereco


def migrar_enderecos():
    with transaction.atomic():
        clientes = Cliente.objects.all()
        for cliente in clientes:
            # Se já tem endereço relacionado, pula
            if cliente.endereco_id:
                continue
            # Cria novo endereço com dados antigos
            endereco = Endereco.objects.create(
                cep=getattr(cliente, "cep", ""),
                logradouro=getattr(cliente, "endereco", ""),
                numero=getattr(cliente, "numero", ""),
                complemento=getattr(cliente, "complemento", ""),
                bairro=getattr(cliente, "bairro", ""),
                cidade=getattr(cliente, "cidade", ""),
                uf=getattr(cliente, "uf", ""),
            )
            cliente.endereco = endereco
            cliente.save(update_fields=["endereco"])
    print("Migração de endereços concluída.")


if __name__ == "__main__":
    migrar_enderecos()
