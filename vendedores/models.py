from django.db import models


class Vendedor(models.Model):
    nome = models.CharField(max_length=100)
    telefone = models.CharField(max_length=20, blank=True)
    comissao_percentual = models.DecimalField(
        max_digits=5, decimal_places=2, help_text="Comissão (%) sobre o valor dos produtos vendidos"
    )

    def __str__(self):
        return self.nome
