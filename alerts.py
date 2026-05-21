from market import get_current_price, get_intraday_prices

# Desaceleração detectada quando o último ganho de período é menor que
# este percentual da média dos ganhos anteriores
DECELERATION_THRESHOLD = 0.3


def calc_profit_pct(current_price: float, avg_price: float) -> float:
    return ((current_price - avg_price) / avg_price) * 100


def detect_deceleration(prices: list[float]) -> bool:
    """
    True quando momentum ainda é positivo mas está desacelerando significativamente.
    Requer ao menos 4 pontos de preço (1 hora de dados a 15min).
    """
    if len(prices) < 4:
        return False

    changes = [prices[i] - prices[i - 1] for i in range(1, len(prices))]

    # Tendência prévia precisa ter sido positiva para falar em desaceleração
    prev_changes = changes[:-1]
    prev_avg = sum(prev_changes) / len(prev_changes)
    if prev_avg <= 0:
        return False

    last_change = changes[-1]
    return last_change < (prev_avg * DECELERATION_THRESHOLD)


def check_alerts(stock: dict) -> list[str]:
    """
    Verifica os alertas de um ativo e retorna lista de mensagens a enviar.
    Modifica stock['alerts_sent'] e stock['last_price'] in-place.
    """
    ticker = stock["ticker"]
    avg_price = stock["avg_price"]
    min_pct = stock["min_profit_pct"]
    max_pct = stock["max_profit_pct"]
    sent = stock.setdefault("alerts_sent", {})

    current_price = get_current_price(ticker)
    if current_price is None:
        return []

    profit_pct = calc_profit_pct(current_price, avg_price)
    stock["last_price"] = current_price
    stock["last_profit_pct"] = round(profit_pct, 2)

    messages = []

    # Lucro máximo atingido
    if profit_pct >= max_pct and not sent.get("max_profit"):
        messages.append(
            f"*ALERTA MAXIMO* {ticker}\n"
            f"Lucro: {profit_pct:.1f}% (meta maxima: {max_pct}%)\n"
            f"Preco atual: R${current_price:.2f} | Medio: R${avg_price:.2f}\n"
            f"Considere realizar o lucro!"
        )
        sent["max_profit"] = True

    # Lucro mínimo atingido (só envia se máximo ainda não foi)
    elif profit_pct >= min_pct and not sent.get("min_profit"):
        messages.append(
            f"*Zona de lucro* {ticker}\n"
            f"Lucro: {profit_pct:.1f}% (minimo: {min_pct}%)\n"
            f"Preco atual: R${current_price:.2f} | Medio: R${avg_price:.2f}"
        )
        sent["min_profit"] = True

    # Desaceleração enquanto na zona de lucro
    if profit_pct >= min_pct and not sent.get("deceleration"):
        prices = get_intraday_prices(ticker)
        if detect_deceleration(prices):
            messages.append(
                f"*DESACELERACAO* {ticker}\n"
                f"Momentum caindo — lucro atual: {profit_pct:.1f}%\n"
                f"Preco: R${current_price:.2f}\n"
                f"Hora de realizar o lucro!"
            )
            sent["deceleration"] = True

    # Reseta alertas ao iniciar novo dia de pregão (preço abaixo da zona mínima)
    if profit_pct < min_pct * 0.5:
        stock["alerts_sent"] = {}

    return messages
