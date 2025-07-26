from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("configuracao", "0008_configuracaosistema_endereco"),
    ]
    operations = [
        migrations.RunSQL(
            sql="ALTER TABLE configuracao_configuracaosistema ALTER COLUMN endereco DROP NOT NULL;",
            reverse_sql="ALTER TABLE configuracao_configuracaosistema ALTER COLUMN endereco SET NOT NULL;",
        ),
    ]
