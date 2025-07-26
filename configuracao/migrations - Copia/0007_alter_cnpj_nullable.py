from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("configuracao", "0006_configuracaosistema_cnpj"),
    ]
    operations = [
        migrations.RunSQL(
            sql="ALTER TABLE configuracao_configuracaosistema ALTER COLUMN cnpj DROP NOT NULL;",
            reverse_sql="ALTER TABLE configuracao_configuracaosistema ALTER COLUMN cnpj SET NOT NULL;",
        ),
    ]
