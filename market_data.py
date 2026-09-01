import os
from datetime import datetime, timedelta, timezone

from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame


API_KEY = os.environ["ALPACA_API_KEY"]
SECRET_KEY = os.environ["ALPACA_SECRET_KEY"]

client = StockHistoricalDataClient(API_KEY, SECRET_KEY)

symbols = ["SPY", "QQQ", "AAPL", "MSFT", "NVDA"]

end = datetime.now(timezone.utc)
start = end - timedelta(days=5)

request = StockBarsRequest(
    symbol_or_symbols=symbols,
    timeframe=TimeFrame.Day,
    start=start,
    end=end,
    feed="iex",
)

bars = client.get_stock_bars(request)

print("\n=== ALPACA MARKET DATA ===\n")

for symbol in symbols:
    data = bars.data.get(symbol, [])

    if not data:
        print(f"{symbol}: No data available")
        continue

    latest = data[-1]

    print(
        f"{symbol}: "
        f"Open=${latest.open:.2f} | "
        f"High=${latest.high:.2f} | "
        f"Low=${latest.low:.2f} | "
        f"Close=${latest.close:.2f} | "
        f"Volume={latest.volume:,}"
    )