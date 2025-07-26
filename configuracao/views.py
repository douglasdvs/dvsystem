import datetime
import os
import subprocess

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.views.decorators.csrf import csrf_exempt

from pedidos.models import Pedido

from .forms import ConfiguracaoSistemaForm
from .forms_integracao import IntegracaoForm
from .models import ConfiguracaoSistema, Integracao


@login_required
def index(request):
    return render(request, "configuracao/index.html")


@login_required
def parametros_gerais(request):
    config = ConfiguracaoSistema.objects.first()
    if request.method == "POST":
        form = ConfiguracaoSistemaForm(request.POST, request.FILES, instance=config)
        if form.is_valid():
            form.save()
            messages.success(request, "Parâmetros gerais atualizados com sucesso!")
            return redirect("configuracao:parametros_gerais")
    else:
        form = ConfiguracaoSistemaForm(instance=config)
    return render(request, "configuracao/parametros_gerais.html", {"form": form})


@login_required
def editar_modelo_impressao(request):
    template_path = os.path.join("pedidos", "templates", "pedidos", "modelo_pedido.html")
    conteudo = ""
    if os.path.exists(template_path):
        with open(template_path, "r", encoding="utf-8") as f:
            conteudo = f.read()
    pedidos_recentes = Pedido.objects.order_by("-id")[:10]
    if request.method == "POST":
        novo_conteudo = request.POST.get("conteudo", "")
        # Substitui /static/logo.png por tag Django para uso real
        novo_conteudo = novo_conteudo.replace("/static/logo.png", "{% static 'logo.png' %}")
        with open(template_path, "w", encoding="utf-8") as f:
            f.write(novo_conteudo)
        messages.success(request, "Modelo de impressão atualizado com sucesso!")
        return redirect("configuracao:modelos_impressao")
    # Passa logo_url para visualização no editor
    return render(
        request,
        "configuracao/modelos_impressao.html",
        {
            "conteudo": conteudo,
            "pedidos_recentes": pedidos_recentes,
            "logo_url": "/static/logo.png",
        },
    )


@login_required
def lista_integracoes(request):
    integracoes = Integracao.objects.all().order_by("nome")
    return render(request, "configuracao/integracoes.html", {"integracoes": integracoes})


@login_required
def nova_integracao(request):
    if request.method == "POST":
        form = IntegracaoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Integração criada com sucesso!")
            return redirect("configuracao:lista_integracoes")
    else:
        form = IntegracaoForm()
    return render(request, "configuracao/integracao_form.html", {"form": form, "titulo": "Nova Integração"})


@login_required
def backup(request):
    # Apenas exibe a tela de backup/restore (funcionalidade manual)
    return render(request, "configuracao/backup.html")


from io import StringIO

from django.core.management import call_command


@login_required
def fazer_backup(request):
    """
    Realiza o backup dos dados do sistema usando dumpdata,
    que é independente de banco de dados.
    """
    try:
        # Usa um buffer em memória para armazenar o backup
        backup_io = StringIO()
        call_command("dumpdata", stdout=backup_io, indent=2)

        # Prepara a resposta para download
        backup_io.seek(0)
        data_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        response = HttpResponse(backup_io.read(), content_type="application/json")
        response["Content-Disposition"] = f'attachment; filename="backup_{data_str}.json"'

        messages.success(request, "Backup gerado com sucesso!")
        return response

    except Exception as e:
        messages.error(request, f"Ocorreu um erro ao gerar o backup: {e}")
        return redirect("configuracao:backup")


@login_required
def restaurar_backup(request):
    """
    Restaura os dados a partir de um arquivo de backup .json.
    Este método apaga os dados existentes antes de restaurar.
    """
    if request.method == "POST":
        backup_file = request.FILES.get("backup_file")
        if not backup_file:
            messages.error(request, "Nenhum arquivo de backup enviado.")
            return redirect("configuracao:backup")

        if not backup_file.name.endswith(".json"):
            messages.error(request, "Arquivo inválido. Por favor, envie um arquivo .json.")
            return redirect("configuracao:backup")

        try:
            # Salva o arquivo temporariamente para o loaddata ler
            temp_dir = r"D:\dvsystem\BPK"
            os.makedirs(temp_dir, exist_ok=True)
            temp_path = os.path.join(temp_dir, "temp_backup.json")

            with open(temp_path, "wb+") as dest:
                for chunk in backup_file.chunks():
                    dest.write(chunk)

            # Limpa o banco de dados antes de carregar os novos dados
            call_command("flush", "--no-input")

            # Carrega os dados do backup
            call_command("loaddata", temp_path)

            # Remove o arquivo temporário
            os.remove(temp_path)

            messages.success(request, "Backup restaurado com sucesso! O sistema foi reiniciado com os novos dados.")

        except Exception as e:
            messages.error(request, f"Ocorreu um erro ao restaurar o backup: {e}")

        return redirect("configuracao:backup")

    return redirect("configuracao:backup")


@login_required
def listar_backups(request):
    """
    Lista os arquivos de backup .json no diretório de backup.
    """
    if request.method == "POST":
        backup_dir = r"D:\dvsystem\BPK"
        try:
            if os.path.exists(backup_dir):
                files = [
                    f
                    for f in os.listdir(backup_dir)
                    if f.endswith(".json") and os.path.isfile(os.path.join(backup_dir, f))
                ]
                return HttpResponse(",".join(files))
            else:
                return HttpResponse("")
        except Exception as e:
            return HttpResponse(f"Erro ao listar backups: {e}", status=500)
    return HttpResponse("Método não permitido", status=405)


@csrf_exempt
@login_required
def excluir_backup(request):
    if request.method == "POST":
        filename = request.POST.get("filename")
        if not filename:
            return HttpResponse("Nome do arquivo não fornecido.", status=400)

        backup_dir = r"D:\dvsystem\BPK"
        file_path = os.path.join(backup_dir, filename)

        # Verificação de segurança para evitar travessia de diretório
        if not os.path.abspath(file_path).startswith(os.path.abspath(backup_dir)):
            return HttpResponse("Tentativa de acesso a diretório inválido.", status=403)

        try:
            if os.path.exists(file_path) and os.path.isfile(file_path):
                os.remove(file_path)
                return HttpResponse(f"Backup {filename} excluído com sucesso.")
            else:
                return HttpResponse("Arquivo não encontrado.", status=404)
        except Exception as e:
            return HttpResponse(f"Erro ao excluir o backup: {e}", status=500)

    return HttpResponse("Método não permitido", status=405)
