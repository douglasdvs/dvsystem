from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("configuracao", "0018_configuracaosistema_facebook"),
    ]
    operations = [
        migrations.RunSQL(
            sql="ALTER TABLE configuracao_configuracaosistema ALTER COLUMN facebook DROP NOT NULL;",
            reverse_sql="ALTER TABLE configuracao_configuracaosistema ALTER COLUMN facebook SET NOT NULL;",
        ),
    ]
