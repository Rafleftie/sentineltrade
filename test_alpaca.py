import os
from alpaca.trading.client import TradingClient

api_key = os.environ["ALPACA_API_KEY"]
secret_key = os.environ["ALPACA_SECRET_KEY"]

client = TradingClient(
    api_key=api_key,
    secret_key=secret_key,
    paper=True,
)

account = client.get_account()

print("=== ALPACA PAPER ACCOUNT ===")
print(f"Status:        {account.status}")
print(f"Equity:        ${account.equity}")
print(f"Cash:          ${account.cash}")
print(f"Buying Power:  ${account.buying_power}")
print(f"Currency:      {account.currency}")