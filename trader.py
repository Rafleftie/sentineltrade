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


def get_positions_detailed():
    """
    Returns a list of dicts with full position detail, including live
    unrealized P&L, for display purposes.
    """
    positions = trading_client.get_all_positions()

    result = []
    for p in positions:
        result.append({
            "Symbol": p.symbol,
            "Shares": int(float(p.qty)),
            "Avg Entry": round(float(p.avg_entry_price), 2),
            "Current Price": round(float(p.current_price), 2),
            "Market Value": round(float(p.market_value), 2),
            "Unrealized P&L": round(float(p.unrealized_pl), 2),
            "Unrealized P&L %": round(float(p.unrealized_plpc) * 100, 2),
        })

    return result


def get_daily_pnl():
    """
    Returns today's real profit/loss in dollars, calculated from the
    account's current equity vs. its equity at the start of the day
    (last_equity). This is what feeds the risk manager's daily loss
    circuit breaker.
    """
    account = trading_client.get_account()

    equity = float(account.equity)
    last_equity = float(account.last_equity)

    return equity - last_equity


if __name__ == "__main__":
    account = get_account()

    print("\n=== ALPACA PAPER ACCOUNT ===\n")
    print(f"  Equity:        ${float(account.equity):,.2f}")
    print(f"  Cash:          ${float(account.cash):,.2f}")
    print(f"  Buying Power:  ${float(account.buying_power):,.2f}")
    print(f"  Status:        {account.status}")
    print(f"  Daily P&L:     ${get_daily_pnl():,.2f}")
    print()
