import time
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


def get_current_price(ticker: str) -> float | None:
    try:
        stock = yf.Ticker(_b3_symbol(ticker))
        hist = stock.history(period="1d", interval="1m")
        if hist.empty:
            return None
        return float(hist["Close"].iloc[-1])
    except Exception:
        return None


def get_intraday_prices(ticker: str, periods: int = 8) -> list[float]:
    """Returns up to `periods` most recent 15-min closing prices for today."""
    try:
        stock = yf.Ticker(_b3_symbol(ticker))
        hist = stock.history(period="1d", interval="15m")
        if hist.empty:
            return []
        prices = hist["Close"].tolist()
        return prices[-periods:]
    except Exception:
        return []
