from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("configuracao", "0016_configuracaosistema_instagram"),
    ]
    operations = [
        migrations.RunSQL(
            sql="ALTER TABLE configuracao_configuracaosistema ALTER COLUMN instagram DROP NOT NULL;",
            reverse_sql="ALTER TABLE configuracao_configuracaosistema ALTER COLUMN instagram SET NOT NULL;",
        ),
    ]
