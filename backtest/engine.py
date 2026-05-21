import yfinance as yf


def run_backtest(ticker: str, avg_price: float, quantity: float,
                 min_pct: float, max_pct: float, period: str) -> dict:
    sym = ticker.upper()
    if not sym.endswith(".SA"):
        sym += ".SA"

    stock = yf.Ticker(sym)
    hist = stock.history(period=period)

    if hist.empty:
        return {"error": f"Sem dados históricos para {ticker}. Verifique o ticker e tente novamente."}

    prices = hist["Close"].dropna()
    trades = []
    alerts_sent = {}

    for dt, price in zip(prices.index, prices.values):
        price = float(price)
        profit_pct = ((price - avg_price) / avg_price) * 100

        if profit_pct >= max_pct and not alerts_sent.get("max"):
            trades.append({
                "date": dt.strftime("%Y-%m-%d"),
                "type": "MAX",
                "label": "Alerta Máximo",
                "price": round(price, 2),
                "profit_pct": round(profit_pct, 2),
                "profit_value": round((price - avg_price) * quantity, 2),
            })
            alerts_sent["max"] = True
        elif profit_pct >= min_pct and not alerts_sent.get("min"):
            trades.append({
                "date": dt.strftime("%Y-%m-%d"),
                "type": "MIN",
                "label": "Zona de Lucro",
                "price": round(price, 2),
                "profit_pct": round(profit_pct, 2),
                "profit_value": round((price - avg_price) * quantity, 2),
            })
            alerts_sent["min"] = True

        if profit_pct < min_pct * 0.5:
            alerts_sent = {}

    chart_labels = [dt.strftime("%Y-%m-%d") for dt in prices.index]
    chart_prices = [round(float(p), 2) for p in prices.values]

    trade_dates = {t["date"]: t for t in trades}
    min_points = [trade_dates[d]["price"] if d in trade_dates and trade_dates[d]["type"] == "MIN" else None for d in chart_labels]
    max_points = [trade_dates[d]["price"] if d in trade_dates and trade_dates[d]["type"] == "MAX" else None for d in chart_labels]

    total_max = sum(t["profit_value"] for t in trades if t["type"] == "MAX")
    total_min = sum(t["profit_value"] for t in trades if t["type"] == "MIN")

    return {
        "trades": trades,
        "chart": {
            "labels": chart_labels,
            "prices": chart_prices,
            "min_points": min_points,
            "max_points": max_points,
            "avg_price": avg_price,
            "min_price": round(avg_price * (1 + min_pct / 100), 2),
            "max_price": round(avg_price * (1 + max_pct / 100), 2),
        },
        "summary": {
            "total_max_alerts": len([t for t in trades if t["type"] == "MAX"]),
            "total_min_alerts": len([t for t in trades if t["type"] == "MIN"]),
            "profit_if_sold_at_max": round(total_max, 2),
            "profit_if_sold_at_min": round(total_min, 2),
            "profit_total": round(total_max + total_min, 2),
        },
    }
