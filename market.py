from datetime import datetime
from zoneinfo import ZoneInfo

import yfinance as yf

BRAZIL_TZ = ZoneInfo("America/Sao_Paulo")
MARKET_OPEN_HOUR = 10
MARKET_CLOSE_HOUR = 17
MARKET_CLOSE_MINUTE = 55


def is_market_open() -> bool:
    now = datetime.now(BRAZIL_TZ)
    if now.weekday() >= 5:
        return False
    after_open = now.hour > MARKET_OPEN_HOUR or (
        now.hour == MARKET_OPEN_HOUR and now.minute >= 0
    )
    before_close = now.hour < MARKET_CLOSE_HOUR or (
        now.hour == MARKET_CLOSE_HOUR and now.minute <= MARKET_CLOSE_MINUTE
    )
    return after_open and before_close


def _b3_symbol(ticker: str) -> str:
    t = ticker.upper().strip()
    return t if t.endswith(".SA") else f"{t}.SA"


def _extract_last_close(hist) -> float | None:
    if hist is None or hist.empty:
        return None
    close = hist["Close"]
    # yfinance pode retornar DataFrame em vez de Series em algumas versões
    if hasattr(close, "squeeze"):
        close = close.squeeze()
    val = close.iloc[-1]
    # pandas scalar pode ser Series de tamanho 1
    if hasattr(val, "item"):
        val = val.item()
    return float(val)


def get_current_price(ticker: str) -> float | None:
    sym = _b3_symbol(ticker)
    try:
        stock = yf.Ticker(sym)
        # Tenta dados do dia com granularidade de 1 minuto
        hist = stock.history(period="1d", interval="1m")
        price = _extract_last_close(hist)
        if price is not None:
            return price
        # Fallback: últimos 5 dias (útil fora do horário de pregão)
        hist = stock.history(period="5d", interval="1d")
        return _extract_last_close(hist)
    except Exception:
        return None


def get_intraday_prices(ticker: str, periods: int = 8) -> list[float]:
    """Retorna até `periods` fechamentos de 15min mais recentes do dia."""
    try:
        stock = yf.Ticker(_b3_symbol(ticker))
        hist = stock.history(period="1d", interval="15m")
        if hist is None or hist.empty:
            return []
        close = hist["Close"]
        if hasattr(close, "squeeze"):
            close = close.squeeze()
        return [float(v) for v in close.tolist()][-periods:]
    except Exception:
        return []
