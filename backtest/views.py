import json
from django.shortcuts import render
from stocks.models import Stock
from .engine import run_backtest


def backtest_index(request):
    stocks = Stock.objects.filter(active=True)
    result = None
    selected_stock = None
    selected_period = "1y"
    selected_quantity = None
    selected_buyback_pct = 5.0
    selected_trailing_pct = 3.0
    selected_min_hold_pct = 60.0

    if request.method == "POST":
        stock_id = request.POST.get("stock_id")
        selected_period = request.POST.get("period", "1y")
        try:
            stock = Stock.objects.get(pk=stock_id)
            selected_stock = stock

            qty_raw = request.POST.get("quantity", "").strip()
            selected_quantity = int(qty_raw) if qty_raw else stock.quantity

            buyback_raw = request.POST.get("buyback_pct", "5").strip()
            selected_buyback_pct = float(buyback_raw) if buyback_raw else 5.0

            trailing_raw = request.POST.get("trailing_stop_pct", "3").strip()
            selected_trailing_pct = float(trailing_raw) if trailing_raw else 3.0

            hold_raw = request.POST.get("min_hold_pct", "60").strip()
            selected_min_hold_pct = float(hold_raw) if hold_raw else 60.0

            result = run_backtest(
                ticker=stock.ticker,
                quantity=selected_quantity,
                min_pct=float(stock.min_profit_pct),
                trailing_stop_pct=selected_trailing_pct,
                buyback_pct=selected_buyback_pct,
                period=selected_period,
                min_hold_pct=selected_min_hold_pct,
            )
        except (Stock.DoesNotExist, ValueError):
            pass

    return render(request, "backtest/index.html", {
        "stocks": stocks,
        "result": result,
        "selected_stock": selected_stock,
        "selected_period": selected_period,
        "selected_quantity": selected_quantity,
        "selected_buyback_pct": selected_buyback_pct,
        "selected_trailing_pct": selected_trailing_pct,
        "selected_min_hold_pct": selected_min_hold_pct,
        "chart_data_json": json.dumps(result["chart"]) if result and "chart" in result else "null",
    })
