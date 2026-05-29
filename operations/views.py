from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_POST

import uuid

from stocks.models import Stock
from .models import StockPosition, TradeSignal
from .checker import check_all, check_stock


def dashboard(request):
    pending = (
        TradeSignal.objects.filter(status="pending")
        .select_related("stock")
        .order_by("-created_at")
    )
    history = (
        TradeSignal.objects.exclude(status="pending")
        .select_related("stock")
        .order_by("-confirmed_at")[:200]
    )

    positions = StockPosition.objects.select_related("stock").order_by("stock__ticker")
    position_results = []
    for pos in positions:
        confirmed = TradeSignal.objects.filter(
            stock=pos.stock, status="confirmed"
        ).order_by("confirmed_at")

        confirmed_sells = [s for s in confirmed if s.signal_type == "SELL"]
        confirmed_buys  = [s for s in confirmed if s.signal_type == "BUY"]

        total_profit = sum(float(s.profit_captured or 0) for s in confirmed_sells)
        total_fees   = sum(float(s.fee or 0) for s in confirmed_sells)
        total_saved  = sum(float(s.saved or 0) for s in confirmed_buys)

        last_price       = float(pos.last_price) if pos.last_price else None
        position_value   = round(pos.shares * last_price, 2) if last_price else None
        initial_value    = float(pos.initial_avg_price) * pos.initial_shares
        current_avg      = float(pos.avg_price)
        profit_pct       = round(((last_price - current_avg) / current_avg) * 100, 2) if last_price else None

        position_results.append({
            "position":       pos,
            "confirmed":      list(confirmed),
            "total_profit":   round(total_profit, 2),
            "total_fees":     round(total_fees, 2),
            "total_saved":    round(total_saved, 2),
            "position_value": position_value,
            "initial_value":  round(initial_value, 2),
            "profit_pct":     profit_pct,
            "sell_count":     len(confirmed_sells),
            "buy_count":      len(confirmed_buys),
        })

    return render(request, "operations/dashboard.html", {
        "pending":          pending,
        "history":          history,
        "position_results": position_results,
    })


@require_POST
def check_now(request):
    try:
        n = check_all()
        if n:
            messages.success(request, f"{n} novo(s) sinal(is) gerado(s).")
        else:
            messages.info(request, "Verificação concluída — nenhum novo sinal.")
    except Exception as e:
        messages.error(request, f"Erro durante verificação: {e}")
    return redirect("operations_dashboard")


@require_POST
def confirm_signal(request, pk):
    signal = get_object_or_404(TradeSignal, pk=pk, status="pending")
    try:
        executed_price = float(request.POST.get("executed_price") or signal.suggested_price)
    except ValueError:
        messages.error(request, "Preço inválido.")
        return redirect("operations_dashboard")

    pos = signal.stock.position
    now = timezone.now()

    if signal.signal_type == "SELL":
        sold_shares     = signal.shares
        sale_value      = round(sold_shares * executed_price, 2)
        fee_pct         = float(pos.fee_pct)
        fee             = round(sale_value * fee_pct / 100, 2)
        profit_captured = round(sold_shares * (executed_price - float(pos.avg_price)) - fee, 2)
        buyback_trigger = round(executed_price * (1 - float(pos.buyback_pct) / 100), 4)
        pb_id           = str(uuid.uuid4())[:8]

        # Atualiza posição
        pos.pending_buybacks = list(pos.pending_buybacks) + [{
            "id":             pb_id,
            "trigger_price":  buyback_trigger,
            "shares_to_buy":  sold_shares,
            "allocated_cash": sale_value,
            "sell_date":      now.strftime("%Y-%m-%d"),
            "sell_signal_id": signal.pk,
        }]
        pos.shares     -= sold_shares
        pos.peak_price  = None
        pos.save()

        # Atualiza sinal com valores reais
        signal.executed_price  = executed_price
        signal.sale_value      = sale_value
        signal.fee             = fee
        signal.profit_captured = profit_captured
        signal.buyback_trigger = buyback_trigger
        signal.status          = "confirmed"
        signal.confirmed_at    = now
        signal.save()

        messages.success(
            request,
            f"Venda de {sold_shares} {signal.stock.ticker} confirmada @ {executed_price:.2f}. "
            f"Lucro: R$ {profit_captured:.2f}"
        )

    elif signal.signal_type == "BUY":
        shares_to_buy = signal.shares
        buy_cost      = round(shares_to_buy * executed_price, 2)
        pb_id         = signal.pending_buyback_id

        # Encontra o pending buyback correspondente
        allocated_cash = 0
        new_pending    = []
        for pb in pos.pending_buybacks:
            if pb.get("id") == pb_id:
                allocated_cash = pb["allocated_cash"]
            else:
                new_pending.append(pb)

        saved     = round(allocated_cash - buy_cost, 2)
        total_new = pos.shares + shares_to_buy
        new_avg   = round(
            (pos.shares * float(pos.avg_price) + shares_to_buy * executed_price) / total_new, 4
        )

        # Atualiza posição
        pos.shares           = total_new
        pos.avg_price        = new_avg
        pos.pending_buybacks = new_pending
        pos.save()

        signal.executed_price = executed_price
        signal.buy_value      = buy_cost
        signal.saved          = saved
        signal.new_avg_price  = new_avg
        signal.shares_after   = total_new
        signal.status         = "confirmed"
        signal.confirmed_at   = now
        signal.save()

        messages.success(
            request,
            f"Recompra de {shares_to_buy} {signal.stock.ticker} confirmada @ {executed_price:.2f}. "
            f"Economia: R$ {saved:.2f}"
        )

    return redirect("operations_dashboard")


@require_POST
def cancel_signal(request, pk):
    signal = get_object_or_404(TradeSignal, pk=pk, status="pending")
    signal.status       = "cancelled"
    signal.confirmed_at = timezone.now()
    signal.save()
    messages.info(request, f"Sinal {signal.signal_type} {signal.stock.ticker} cancelado.")
    return redirect("operations_dashboard")


