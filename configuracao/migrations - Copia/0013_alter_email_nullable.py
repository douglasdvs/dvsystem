from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("configuracao", "0012_configuracaosistema_email"),
    ]
    operations = [
        migrations.RunSQL(
            sql="ALTER TABLE configuracao_configuracaosistema ALTER COLUMN email DROP NOT NULL;",
            reverse_sql="ALTER TABLE configuracao_configuracaosistema ALTER COLUMN email SET NOT NULL;",
        ),
    ]
