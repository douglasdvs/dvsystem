
from django.shortcuts import render, redirect, get_object_or_404
from .models import Receita, Despesa
from .forms import ReceitaForm, DespesaForm

def lista_receitas(request):
    receitas = Receita.objects.all()
    return render(request, 'financeiro/receita_list.html', {'receitas': receitas})

def nova_receita(request):
    form = ReceitaForm(request.POST or None, request.FILES or None)
    if form.is_valid():
        form.save()
        return redirect('lista_receitas')
    return render(request, 'financeiro/receita_form.html', {'form': form})

def editar_receita(request, pk):
    receita = get_object_or_404(Receita, pk=pk)
    form = ReceitaForm(request.POST or None, request.FILES or None, instance=receita)
    if form.is_valid():
        form.save()
        return redirect('lista_receitas')
    return render(request, 'financeiro/receita_form.html', {'form': form})

def deletar_receita(request, pk):
    receita = get_object_or_404(Receita, pk=pk)
    receita.delete()
    return redirect('lista_receitas')

def lista_despesas(request):
    despesas = Despesa.objects.all()
    return render(request, 'financeiro/despesa_list.html', {'despesas': despesas})

def nova_despesa(request):
    form = DespesaForm(request.POST or None, request.FILES or None)
    if form.is_valid():
        form.save()
        return redirect('lista_despesas')
    return render(request, 'financeiro/despesa_form.html', {'form': form})

def editar_despesa(request, pk):
    despesa = get_object_or_404(Despesa, pk=pk)
    form = DespesaForm(request.POST or None, request.FILES or None, instance=despesa)
    if form.is_valid():
        form.save()
        return redirect('lista_despesas')
    return render(request, 'financeiro/despesa_form.html', {'form': form})

def deletar_despesa(request, pk):
    despesa = get_object_or_404(Despesa, pk=pk)
    despesa.delete()
    return redirect('lista_despesas')
