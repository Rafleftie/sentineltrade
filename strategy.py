import os
from datetime import datetime, timedelta, timezone

import pandas as pd
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame


API_KEY = os.environ["ALPACA_API_KEY"]
SECRET_KEY = os.environ["ALPACA_SECRET_KEY"]

client = StockHistoricalDataClient(API_KEY, SECRET_KEY)

symbols = ["SPY", "QQQ", "AAPL", "MSFT", "NVDA"]

end = datetime.now(timezone.utc)
start = end - timedelta(days=40)

request = StockBarsRequest(
    symbol_or_symbols=symbols,
    timeframe=TimeFrame.Day,
    start=start,
    end=end,
    feed="iex",
)

bars = client.get_stock_bars(request)

print("\n=== ALPHA GUARD — TRADING SIGNALS ===\n")


def calculate_rsi(closes, period=14):
    delta = closes.diff()

    gains = delta.clip(lower=0)
    losses = -delta.clip(upper=0)

    average_gain = gains.rolling(period).mean()
    average_loss = losses.rolling(period).mean()

    rs = average_gain / average_loss

    return 100 - (100 / (1 + rs))


for symbol in symbols:
    data = bars.data.get(symbol, [])

    if len(data) < 20:
        print(f"{symbol}: Not enough data")
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

    print(f"{symbol}")
    print(f"  Price: ${price:.2f}")
    print(f"  MA5:   ${ma5:.2f}")
    print(f"  MA20:  ${ma20:.2f}")
    print(f"  RSI:   {rsi:.2f}")
    print(f"  Score: {score}/3")
    print(f"  Signal: {signal}")
    print()