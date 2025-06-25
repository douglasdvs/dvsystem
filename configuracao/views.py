from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
import os

from pedidos.models import Pedido

@login_required
def editar_modelo_impressao(request):
    template_path = os.path.join('pedidos', 'templates', 'pedidos', 'modelo_pedido.html')
    conteudo = ''
    if os.path.exists(template_path):
        with open(template_path, 'r', encoding='utf-8') as f:
            conteudo = f.read()
    pedidos_recentes = Pedido.objects.order_by('-id')[:10]
    if request.method == 'POST':
        novo_conteudo = request.POST.get('conteudo', '')
        # Substitui /static/logo.png por tag Django para uso real
        novo_conteudo = novo_conteudo.replace('/static/logo.png', "{% static 'logo.png' %}")
        with open(template_path, 'w', encoding='utf-8') as f:
            f.write(novo_conteudo)
        messages.success(request, 'Modelo de impressão atualizado com sucesso!')
        return redirect('configuracao:modelos_impressao')
    # Passa logo_url para visualização no editor
    return render(request, 'configuracao/modelos_impressao.html', {
        'conteudo': conteudo,
        'pedidos_recentes': pedidos_recentes,
        'logo_url': '/static/logo.png',
    })
