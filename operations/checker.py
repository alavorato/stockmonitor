"""
Lógica de verificação de condições para operações em tempo real.
Usa a mesma estratégia do backtest engine, mas de forma incremental e stateful.
"""
import math
import uuid
from datetime import timedelta

import yfinance as yf
from django.utils import timezone

from stocks.models import Stock
from .models import StockPosition, TradeSignal


def _get_price(ticker: str) -> float | None:
    sym = ticker.upper()
    if not sym.endswith(".SA"):
        sym += ".SA"
    try:
        data = yf.Ticker(sym).history(period="1d", interval="5m")
        if data.empty:
            return None
        return round(float(data["Close"].iloc[-1]), 4)
    except Exception:
        return None


def check_all() -> int:
    """Verifica todos os ativos ativos. Retorna número de novos sinais gerados."""
    total = 0
    for stock in Stock.objects.filter(active=True):
        total += check_stock(stock)
    return total


def check_stock(stock: Stock) -> int:
    price = _get_price(stock.ticker)
    if price is None:
        return 0

    pos, _ = StockPosition.objects.get_or_create(
        stock=stock,
        defaults={
            "shares":            stock.quantity,
            "avg_price":         stock.avg_price,
            "initial_shares":    stock.quantity,
            "initial_avg_price": stock.avg_price,
        },
    )

    shares        = pos.shares
    avg_price     = float(pos.avg_price)
    peak_price    = float(pos.peak_price) if pos.peak_price else None
    min_pct       = float(stock.min_profit_pct)
    trailing_stop = float(pos.trailing_stop_pct)
    buyback_pct   = float(pos.buyback_pct)
    min_hold_pct  = float(pos.min_hold_pct)
    fee_pct       = float(pos.fee_pct)
    new_signals   = 0
    now           = timezone.now()

    if shares <= 0:
        pos.last_price   = price
        pos.last_checked = now
        pos.save(update_fields=["last_price", "last_checked"])
        return 0

    profit_pct = ((price - avg_price) / avg_price) * 100

    # Atualiza pico
    if profit_pct >= min_pct:
        if peak_price is None or price > peak_price:
            peak_price = price

    # --- VENDA ---
    if peak_price is not None and price <= peak_price * (1 - trailing_stop / 100):
        # Evita duplicar: não gera novo sinal se já existe um pendente
        # ou se houve cancelamento recente (< 1h)
        recent_sell = TradeSignal.objects.filter(
            stock=stock,
            signal_type="SELL",
            created_at__gte=now - timedelta(hours=1),
        ).exists()

        if not recent_sell:
            initial_investment = float(pos.initial_avg_price) * pos.initial_shares
            kept_by_profit = min(shares, math.ceil(initial_investment * (1 + min_pct / 100) / price))
            kept_by_limit  = math.ceil(shares * min_hold_pct / 100)
            kept_shares    = max(kept_by_profit, kept_by_limit)
            sold_shares    = shares - kept_shares

            if sold_shares > 0:
                sale_value      = round(sold_shares * price, 2)
                fee             = round(sale_value * fee_pct / 100, 2)
                profit_captured = round(sold_shares * (price - avg_price) - fee, 2)
                buyback_trigger = round(price * (1 - buyback_pct / 100), 4)

                TradeSignal.objects.create(
                    stock           = stock,
                    signal_type     = "SELL",
                    suggested_price = price,
                    shares          = sold_shares,
                    peak_price      = peak_price,
                    profit_pct      = round(profit_pct, 2),
                    avg_price_ref   = avg_price,
                    buyback_trigger = buyback_trigger,
                    sale_value      = sale_value,
                    profit_captured = profit_captured,
                    fee             = fee,
                    shares_after    = kept_shares,
                )
                new_signals += 1

    # --- RECOMPRAS ---
    for pb in pos.pending_buybacks:
        if price > pb["trigger_price"]:
            continue
        pb_id = pb.get("id", "")
        # Evita duplicar: sem sinal pendente/recente (< 24h) para esta recompra
        recent_buy = TradeSignal.objects.filter(
            stock=stock,
            signal_type="BUY",
            pending_buyback_id=pb_id,
            created_at__gte=now - timedelta(hours=24),
        ).exists()
        if recent_buy:
            continue

        shares_to_buy = pb["shares_to_buy"]
        buy_cost      = round(shares_to_buy * price, 2)
        saved         = round(pb["allocated_cash"] - buy_cost, 2)
        total_new     = shares + shares_to_buy
        new_avg       = round(((shares * avg_price) + (shares_to_buy * price)) / total_new, 4)

        TradeSignal.objects.create(
            stock              = stock,
            signal_type        = "BUY",
            suggested_price    = price,
            shares             = shares_to_buy,
            pending_buyback_id = pb_id,
            sell_ref_date      = pb.get("sell_date", ""),
            buy_value          = buy_cost,
            saved              = saved,
            new_avg_price      = new_avg,
            shares_after       = total_new,
        )
        new_signals += 1

    pos.peak_price   = peak_price
    pos.last_price   = price
    pos.last_checked = now
    pos.save(update_fields=["peak_price", "last_price", "last_checked"])
    return new_signals
