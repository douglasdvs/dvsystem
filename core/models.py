from django.db import models
from django.contrib.auth.models import User

class RegistroComUsuario(models.Model):
    criado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        abstract = True
from django.db import models
