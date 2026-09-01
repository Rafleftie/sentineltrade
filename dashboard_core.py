import os
from datetime import datetime, timedelta, timezone

import pandas as pd
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame

from risk_manager import RiskManager
from trader import get_positions, get_account


API_KEY = os.environ["ALPACA_API_KEY"]
SECRET_KEY = os.environ["ALPACA_SECRET_KEY"]

SYMBOLS = ["SPY", "QQQ", "AAPL", "MSFT", "NVDA"]


def calculate_rsi(closes, period=14):
    delta = closes.diff()

    gains = delta.clip(lower=0)
    losses = -delta.clip(upper=0)

    average_gain = gains.rolling(period).mean()
    average_loss = losses.rolling(period).mean()

    rs = average_gain / average_loss

    return 100 - (100 / (1 + rs))


def get_signal(df):
    df["MA5"] = df["close"].rolling(5).mean()
    df["MA20"] = df["close"].rolling(20).mean()
    df["RSI"] = calculate_rsi(df["close"])

    latest = df.iloc[-1]

    price = latest["close"]
    ma5 = latest["MA5"]
    ma20 = latest["MA20"]
    rsi = latest["RSI"]

    score = 0

    if ma5 > ma20:
        score += 1

    if price > ma20:
        score += 1

    if 50 < rsi < 70:
        score += 1

    if rsi < 30:
        signal = "BUY"
    elif rsi > 70:
        signal = "SELL"
    elif score >= 2:
        signal = "BUY"
    else:
        signal = "HOLD"

    return price, ma5, ma20, rsi, score, signal


def run_dry_scan():
    """
    Fetches fresh market data, computes signals, and runs each through the
    risk manager. Always dry-run — never places an order. Returns a list of
    dicts, one per symbol, ready to display in a table.
    """

    client = StockHistoricalDataClient(API_KEY, SECRET_KEY)

    end = datetime.now(timezone.utc)
    start = end - timedelta(days=40)

    request = StockBarsRequest(
        symbol_or_symbols=SYMBOLS,
        timeframe=TimeFrame.Day,
        start=start,
        end=end,
        feed="iex",
    )

    bars = client.get_stock_bars(request)

    risk_manager = RiskManager(account_equity=100_000)
    daily_pnl = 0

    existing_positions = get_positions()
    current_exposure = sum(
        qty * bars.data[symbol][-1].close
        for symbol, qty in existing_positions.items()
        if symbol in bars.data and len(bars.data[symbol]) > 0
    )

    rows = []

    for symbol in SYMBOLS:
        data = bars.data.get(symbol, [])

        if len(data) < 20:
            rows.append({
                "Symbol": symbol,
                "Price": None,
                "MA5": None,
                "MA20": None,
                "RSI": None,
                "Score": None,
                "Signal": "N/A",
                "Approved": False,
                "Quantity": 0,
                "Value": 0,
                "Reason": "Not enough data",
            })
            continue

        df = pd.DataFrame(
            [
                {
                    "timestamp": bar.timestamp,
                    "close": float(bar.close),
                    "volume": float(bar.volume),
                }
                for bar in data
            ]
        )
        df = df.sort_values("timestamp")

        if symbol in existing_positions:
            rows.append({
                "Symbol": symbol,
                "Price": float(data[-1].close),
                "MA5": None,
                "MA20": None,
                "RSI": None,
                "Score": None,
                "Signal": "SKIPPED",
                "Approved": False,
                "Quantity": existing_positions[symbol],
                "Value": None,
                "Reason": f"Already holding {existing_positions[symbol]} shares",
            })
            continue

        price, ma5, ma20, rsi, score, signal = get_signal(df)

        decision = risk_manager.check_trade(
            symbol=symbol,
            price=price,
            signal=signal,
            current_exposure=current_exposure,
            daily_pnl=daily_pnl,
        )

        if decision.approved:
            current_exposure += decision.position_value

        rows.append({
            "Symbol": symbol,
            "Price": round(price, 2),
            "MA5": round(ma5, 2),
            "MA20": round(ma20, 2),
            "RSI": round(rsi, 2),
            "Score": f"{score}/3",
            "Signal": signal,
            "Approved": decision.approved,
            "Quantity": decision.quantity,
            "Value": round(decision.position_value, 2) if decision.approved else 0,
            "Reason": decision.reason,
        })

    return rows, existing_positions