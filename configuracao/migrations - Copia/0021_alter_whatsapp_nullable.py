from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("configuracao", "0020_configuracaosistema_whatsapp"),
    ]
    operations = [
        migrations.RunSQL(
            sql="ALTER TABLE configuracao_configuracaosistema ALTER COLUMN whatsapp DROP NOT NULL;",
            reverse_sql="ALTER TABLE configuracao_configuracaosistema ALTER COLUMN whatsapp SET NOT NULL;",
        ),
    ]
