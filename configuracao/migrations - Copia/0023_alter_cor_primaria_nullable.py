from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("configuracao", "0022_configuracaosistema_cor_primaria"),
    ]
    operations = [
        migrations.RunSQL(
            sql="ALTER TABLE configuracao_configuracaosistema ALTER COLUMN cor_primaria DROP NOT NULL;",
            reverse_sql="ALTER TABLE configuracao_configuracaosistema ALTER COLUMN cor_primaria SET NOT NULL;",
        ),
    ]
