from django.shortcuts import render
from django.http import JsonResponse
from stocks.models import Stock
from market import get_current_price, is_market_open


def _stock_status(s):
    avg = float(s.avg_price)
    qty = float(s.quantity)
    min_pct = float(s.min_profit_pct)
    max_pct = float(s.max_profit_pct)

    price = get_current_price(s.ticker)
    if price is None:
        return {
            "ticker": s.ticker,
            "name": s.name,
            "status": "unavailable",
            "current_price": None,
            "avg_price": avg,
            "profit_pct": None,
            "profit_value": None,
            "invested": round(avg * qty, 2),
            "current_value": None,
            "min_pct": min_pct,
            "max_pct": max_pct,
        }

    profit_pct = ((price - avg) / avg) * 100

    if profit_pct >= max_pct:
        status = "max"
    elif profit_pct >= min_pct:
        status = "min"
    elif profit_pct >= 0:
        status = "positive"
    else:
        status = "negative"

    return {
        "ticker": s.ticker,
        "name": s.name,
        "status": status,
        "current_price": round(price, 2),
        "avg_price": avg,
        "profit_pct": round(profit_pct, 2),
        "profit_value": round((price - avg) * qty, 2),
        "invested": round(avg * qty, 2),
        "current_value": round(price * qty, 2),
        "min_pct": min_pct,
        "max_pct": max_pct,
    }


def dashboard(request):
    stocks = Stock.objects.filter(active=True)
    return render(request, "monitor/dashboard.html", {
        "stocks": stocks,
        "market_open": is_market_open(),
    })


def status_data(request):
    stocks = Stock.objects.filter(active=True)
    data = [_stock_status(s) for s in stocks]
    return JsonResponse({"stocks": data, "market_open": is_market_open()})
