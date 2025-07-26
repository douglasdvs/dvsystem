from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("configuracao", "0014_configuracaosistema_site"),
    ]
    operations = [
        migrations.RunSQL(
            sql="ALTER TABLE configuracao_configuracaosistema ALTER COLUMN site DROP NOT NULL;",
            reverse_sql="ALTER TABLE configuracao_configuracaosistema ALTER COLUMN site SET NOT NULL;",
        ),
    ]
