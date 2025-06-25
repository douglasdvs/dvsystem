from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ("configuracao", "0001_initial"),   # deixe como está
    ]

    operations = [
        migrations.AddField(
            model_name="configuracaosistema",
            name="tema_primario",
            field=models.CharField(max_length=7, default="#2193b0"),
        ),
        migrations.AddField(
            model_name="configuracaosistema",
            name="tema_secundario",
            field=models.CharField(max_length=7, default="#6dd5ed"),
        ),
    ]