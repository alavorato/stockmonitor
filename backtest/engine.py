import math
import yfinance as yf


def run_backtest(ticker: str, quantity: int, min_pct: float,
                 trailing_stop_pct: float, buyback_pct: float, period: str,
                 min_hold_pct: float = 60.0, fee_pct: float = 0.0305) -> dict:
    sym = ticker.upper()
    if not sym.endswith(".SA"):
        sym += ".SA"

    stock_data = yf.Ticker(sym)
    hist = stock_data.history(period=period)

    if hist.empty:
        return {"error": f"Sem dados históricos para {ticker}. Verifique o ticker e tente novamente."}

    prices = hist["Close"].dropna()
    purchase_price = round(float(prices.iloc[0]), 2)
    initial_shares = int(quantity)
    initial_investment = purchase_price * initial_shares

    shares = initial_shares
    avg_price = purchase_price
    cash = 0.0

    # Rastreia pico enquanto lucro >= max_pct; reseta após cada venda
    peak_price = None

    # Cada venda gera uma ordem de recompra independente:
    # {"trigger_price", "shares_to_buy", "allocated_cash", "sell_date"}
    pending_buybacks = []

    events = []
    chart_labels = [dt.strftime("%Y-%m-%d") for dt in prices.index]
    chart_prices = [round(float(p), 2) for p in prices.values]
    sell_points = [None] * len(chart_labels)
    buy_points = [None] * len(chart_labels)

    for i, (dt, price) in enumerate(zip(prices.index, prices.values)):
        price = float(price)
        profit_pct = ((price - avg_price) / avg_price) * 100 if avg_price > 0 else 0

        # Rastreia pico a partir do momento em que lucro atinge a meta mínima
        if profit_pct >= min_pct:
            if peak_price is None or price > peak_price:
                peak_price = price

        sold_today = False

        # VENDA PARCIAL: trailing stop ativado (queda X% do pico)
        if peak_price is not None and price <= peak_price * (1 - trailing_stop_pct / 100) and shares > 0:
            target_position_value = initial_investment * (1 + min_pct / 100)
            kept_by_profit = min(shares, math.ceil(target_position_value / price))
            kept_by_limit  = math.ceil(shares * min_hold_pct / 100)
            kept_shares    = max(kept_by_profit, kept_by_limit)
            sold_shares    = shares - kept_shares

            if sold_shares > 0:
                sale_value = sold_shares * price
                fee = round(sale_value * fee_pct / 100, 2)
                profit_captured = sold_shares * (price - avg_price) - fee
                cash += sale_value - fee
                shares = kept_shares
                sell_points[i] = round(price, 2)
                sold_today = True

                trigger = round(price * (1 - buyback_pct / 100), 2)
                pending_buybacks.append({
                    "trigger_price": trigger,
                    "shares_to_buy": sold_shares,
                    "allocated_cash": round(sale_value, 2),
                    "sell_date": dt.strftime("%Y-%m-%d"),
                })

                events.append({
                    "date": dt.strftime("%Y-%m-%d"),
                    "type": "SELL",
                    "price": round(price, 2),
                    "peak_price": round(peak_price, 2),
                    "profit_pct_at_sell": round(profit_pct, 2),
                    "shares_sold": sold_shares,
                    "sale_value": round(sale_value, 2),
                    "fee": round(fee, 2),
                    "profit_captured": round(profit_captured, 2),
                    "shares_remaining": kept_shares,
                    "shares_after": kept_shares,
                    "avg_price_used": round(avg_price, 2),
                    "cash": round(cash, 2),
                    "buyback_trigger": trigger,
                })

            # Reseta pico após venda
            peak_price = None

        # RECOMPRAS INDEPENDENTES: cada venda tem seu próprio gatilho
        # Todas as ordens cujo gatilho foi atingido hoje são executadas
        if not sold_today and pending_buybacks:
            triggered = [pb for pb in pending_buybacks if price <= pb["trigger_price"]]
            for pb in triggered:
                shares_to_buy = pb["shares_to_buy"]
                buy_cost = shares_to_buy * price
                # Lucro do ciclo: vendeu mais caro, comprou mais barato
                saved = pb["allocated_cash"] - buy_cost

                total_new = shares + shares_to_buy
                avg_price = ((shares * avg_price) + (shares_to_buy * price)) / total_new
                shares = total_new
                cash -= buy_cost  # desconta só o custo; o saved fica no caixa
                buy_points[i] = round(price, 2)

                events.append({
                    "date": dt.strftime("%Y-%m-%d"),
                    "type": "BUY",
                    "price": round(price, 2),
                    "shares_bought": shares_to_buy,
                    "buy_value": round(buy_cost, 2),
                    "saved": round(saved, 2),
                    "shares_total": shares,
                    "shares_after": shares,
                    "new_avg_price": round(avg_price, 2),
                    "sell_ref": pb["sell_date"],
                })

            for pb in triggered:
                pending_buybacks.remove(pb)

        # Descarta pico obsoleto se preço cair muito abaixo da meta mínima
        if peak_price is not None and profit_pct < min_pct * 0.5:
            peak_price = None

    last_price = round(float(prices.iloc[-1]), 2)
    position_value = shares * last_price
    total_value = position_value + cash
    total_profit = total_value - initial_investment
    total_profit_captured = sum(e["profit_captured"] for e in events if e["type"] == "SELL")
    total_fees = sum(e["fee"] for e in events if e["type"] == "SELL")
    total_saved = sum(e["saved"] for e in events if e["type"] == "BUY")

    pending_cash = sum(pb["allocated_cash"] for pb in pending_buybacks)
    free_cash = round(cash - pending_cash, 2)

    return {
        "purchase_price": purchase_price,
        "initial_shares": initial_shares,
        "initial_investment": round(initial_investment, 2),
        "events": events,
        "chart": {
            "labels": chart_labels,
            "prices": chart_prices,
            "sell_points": sell_points,
            "buy_points": buy_points,
            "avg_price": purchase_price,
            "min_price": round(purchase_price * (1 + min_pct / 100), 2),
        },
        "summary": {
            "sell_count": len([e for e in events if e["type"] == "SELL"]),
            "buy_count": len([e for e in events if e["type"] == "BUY"]),
            "total_profit_captured": round(total_profit_captured, 2),
            "total_fees": round(total_fees, 2),
            "total_saved": round(total_saved, 2),
            "shares_held": shares,
            "pending_buybacks_count": len(pending_buybacks),
            "cash_remaining": round(cash, 2),
            "pending_cash": round(pending_cash, 2),
            "free_cash": free_cash,
            "position_value": round(position_value, 2),
            "total_value": round(total_value, 2),
            "total_profit": round(total_profit, 2),
            "total_profit_pct": round((total_profit / initial_investment) * 100, 2),
            "last_price": last_price,
            "last_avg_price": round(avg_price, 2),
        },
    }
