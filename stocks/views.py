from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from .models import Stock
from .forms import StockForm


def stock_list(request):
    stocks = Stock.objects.all()
    return render(request, "stocks/list.html", {"stocks": stocks})


def stock_add(request):
    if request.method == "POST":
        form = StockForm(request.POST)
        if form.is_valid():
            stock = form.save()
            messages.success(request, f"Ativo {stock.ticker} adicionado com sucesso.")
            return redirect("stock_list")
    else:
        form = StockForm()
    return render(request, "stocks/form.html", {"form": form, "title": "Adicionar Ativo"})


def stock_edit(request, pk):
    stock = get_object_or_404(Stock, pk=pk)
    if request.method == "POST":
        form = StockForm(request.POST, instance=stock)
        if form.is_valid():
            form.save()
            messages.success(request, f"Ativo {stock.ticker} atualizado.")
            return redirect("stock_list")
    else:
        form = StockForm(instance=stock)
    return render(request, "stocks/form.html", {"form": form, "title": f"Editar {stock.ticker}", "stock": stock})


def stock_delete(request, pk):
    stock = get_object_or_404(Stock, pk=pk)
    if request.method == "POST":
        ticker = stock.ticker
        stock.delete()
        messages.success(request, f"Ativo {ticker} removido.")
        return redirect("stock_list")
    return render(request, "stocks/confirm_delete.html", {"stock": stock})
