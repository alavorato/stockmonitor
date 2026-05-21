import json
from django.shortcuts import render
from stocks.models import Stock
from .engine import run_backtest


def backtest_index(request):
    stocks = Stock.objects.filter(active=True)
    result = None
    selected_stock = None
    selected_period = "1y"

    if request.method == "POST":
        stock_id = request.POST.get("stock_id")
        selected_period = request.POST.get("period", "1y")
        try:
            stock = Stock.objects.get(pk=stock_id)
            selected_stock = stock
            result = run_backtest(
                ticker=stock.ticker,
                avg_price=float(stock.avg_price),
                quantity=float(stock.quantity),
                min_pct=float(stock.min_profit_pct),
                max_pct=float(stock.max_profit_pct),
                period=selected_period,
            )
        except Stock.DoesNotExist:
            pass

    return render(request, "backtest/index.html", {
        "stocks": stocks,
        "result": result,
        "selected_stock": selected_stock,
        "selected_period": selected_period,
        "chart_data_json": json.dumps(result["chart"]) if result and "chart" in result else "null",
    })
