import os

from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce


API_KEY = os.environ["ALPACA_API_KEY"]
SECRET_KEY = os.environ["ALPACA_SECRET_KEY"]

# paper=True is critical — this must always point at the paper account.
trading_client = TradingClient(API_KEY, SECRET_KEY, paper=True)


def place_order(symbol: str, quantity: int, side: str = "buy"):
    """
    Submits a market order to the Alpaca PAPER trading account.

    side: "buy" or "sell"
    """

    order_side = OrderSide.BUY if side == "buy" else OrderSide.SELL

    order_request = MarketOrderRequest(
        symbol=symbol,
        qty=quantity,
        side=order_side,
        time_in_force=TimeInForce.DAY,
    )

    order = trading_client.submit_order(order_data=order_request)

    print(f"  → Order submitted: {order.id}")
    print(f"    Status: {order.status}")

    return order


def get_account():
    account = trading_client.get_account()
    return account


def get_positions():
    """
    Returns a dict of {symbol: quantity} for all current paper account holdings.
    """
    positions = trading_client.get_all_positions()
    return {p.symbol: int(float(p.qty)) for p in positions}


if __name__ == "__main__":
    account = get_account()

    print("\n=== ALPACA PAPER ACCOUNT ===\n")
    print(f"  Equity:        ${float(account.equity):,.2f}")
    print(f"  Cash:          ${float(account.cash):,.2f}")
    print(f"  Buying Power:  ${float(account.buying_power):,.2f}")
    print(f"  Status:        {account.status}")
    print()