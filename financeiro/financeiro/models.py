
from django.db import models

CATEGORIAS_DESPESA = [
    ('devolucao', 'Devolução'),
    ('fornecedor', 'Fornecedor'),
    ('outros', 'Outros'),
]

CATEGORIAS_RECEITA = [
    ('pedido', 'Venda de Pedido'),
    ('outros', 'Outros'),
]

class Despesa(models.Model):
    descricao = models.CharField(max_length=255)
    data = models.DateField()
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    categoria = models.CharField(max_length=20, choices=CATEGORIAS_DESPESA)
    anexo = models.FileField(upload_to='financeiro/anexos/', null=True, blank=True)

    def __str__(self):
        return f"Despesa: {self.descricao} - R$ {self.valor}"

class Receita(models.Model):
    descricao = models.CharField(max_length=255)
    data = models.DateField()
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    categoria = models.CharField(max_length=20, choices=CATEGORIAS_RECEITA)
    anexo = models.FileField(upload_to='financeiro/anexos/', null=True, blank=True)

    def __str__(self):
        return f"Receita: {self.descricao} - R$ {self.valor}"
