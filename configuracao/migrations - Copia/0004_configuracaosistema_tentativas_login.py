# Generated by Django 5.2.2 on 2025-06-26 22:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("configuracao", "0003_configuracaosistema_tempo_sessao"),
    ]

    operations = [
        migrations.AddField(
            model_name="configuracaosistema",
            name="tentativas_login",
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
