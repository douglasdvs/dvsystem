from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("configuracao", "0010_configuracaosistema_telefone"),
    ]
    operations = [
        migrations.RunSQL(
            sql="ALTER TABLE configuracao_configuracaosistema ALTER COLUMN telefone DROP NOT NULL;",
            reverse_sql="ALTER TABLE configuracao_configuracaosistema ALTER COLUMN telefone SET NOT NULL;",
        ),
    ]
