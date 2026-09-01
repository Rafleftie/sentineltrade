import argparse
import os
from datetime import datetime, timedelta, timezone

import pandas as pd
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame

from risk_manager import RiskManager
from trader import place_order, get_positions


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


def main(dry_run=True):
    risk_manager = RiskManager(account_equity=100_000)

    daily_pnl = 0

    existing_positions = get_positions()
    current_exposure = sum(
        qty * bars.data[symbol][-1].close
        for symbol, qty in existing_positions.items()
        if symbol in bars.data and len(bars.data[symbol]) > 0
    )

    if existing_positions:
        print("Existing positions:")
        for symbol, qty in existing_positions.items():
            print(f"  {symbol}: {qty} shares")
        print()

    print("\n=== ALPHAGUARD — AGENT RUN ===")
    print(f"Mode: {'DRY RUN (no orders sent)' if dry_run else 'LIVE PAPER TRADING'}\n")

    for symbol in symbols:
        data = bars.data.get(symbol, [])

        if len(data) < 20:
            print(f"{symbol}: Not enough data\n")
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
            print(f"{symbol}")
            print(f"  Skipped: already holding {existing_positions[symbol]} shares.\n")
            continue

        price, ma5, ma20, rsi, score, signal = get_signal(df)

        decision = risk_manager.check_trade(
            symbol=symbol,
            price=price,
            signal=signal,
            current_exposure=current_exposure,
            daily_pnl=daily_pnl,
        )

        print(f"{symbol}")
        print(f"  Price:    ${price:.2f}")
        print(f"  MA5:      ${ma5:.2f}")
        print(f"  MA20:     ${ma20:.2f}")
        print(f"  RSI:      {rsi:.2f}")
        print(f"  Score:    {score}/3")
        print(f"  Signal:   {signal}")
        print(f"  Approved: {decision.approved}")

        if decision.approved:
            print(f"  Quantity: {decision.quantity}")
            print(f"  Value:    ${decision.position_value:,.2f}")

            current_exposure += decision.position_value

            if dry_run:
                print(f"  → [DRY RUN] Would submit BUY {decision.quantity} {symbol}")
            else:
                place_order(symbol, decision.quantity, side="buy")

        print(f"  Reason:   {decision.reason}")
        print()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--live",
        action="store_true",
        help="Actually submit orders to the Alpaca paper account instead of dry-run.",
    )
    args = parser.parse_args()

    main(dry_run=not args.live)