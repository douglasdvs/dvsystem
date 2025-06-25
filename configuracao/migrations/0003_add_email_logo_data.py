from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ("configuracao", "0002_add_temas"),
    ]

    operations = [
        migrations.AddField(
            model_name="configuracaosistema",
            name="data_atualizacao",
            field=models.DateTimeField(auto_now=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
    ]
