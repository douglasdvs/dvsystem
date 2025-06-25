import os
from celery import Celery
from django.conf import settings

# Configurar o módulo de configurações do Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dvsystem.settings')

# Criar a aplicação Celery
app = Celery('dvsystem')

# Configurar o Celery usando as configurações do Django
app.config_from_object('django.conf:settings', namespace='CELERY')

# Carregar tarefas de todos os apps registrados
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}') 