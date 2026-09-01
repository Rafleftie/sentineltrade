from dataclasses import dataclass


@dataclass
class RiskDecision:
    approved: bool
    reason: str
    quantity: int
    position_value: float


class RiskManager:
    """
    AlphaGuard risk-control engine.

    The strategy proposes trades.
    This class decides whether those trades are allowed.
    """

    def __init__(
        self,
        account_equity: float = 100_000,
        max_position_pct: float = 0.10,
        max_portfolio_exposure_pct: float = 0.60,
        max_daily_loss_pct: float = 0.02,
        min_trade_value: float = 500,
    ):
        self.account_equity = account_equity

        # Maximum amount allowed in one position.
        self.max_position_pct = max_position_pct

        # Maximum total portfolio exposure.
        self.max_portfolio_exposure_pct = max_portfolio_exposure_pct

        # Maximum daily loss before trading is stopped.
        self.max_daily_loss_pct = max_daily_loss_pct

        self.min_trade_value = min_trade_value

    def check_trade(
        self,
        symbol: str,
        price: float,
        signal: str,
        current_exposure: float = 0,
        daily_pnl: float = 0,
    ) -> RiskDecision:

        # ---------------------------------------------------------
        # Rule 1: Only BUY signals can currently enter positions.
        # ---------------------------------------------------------
        if signal != "BUY":
            return RiskDecision(
                approved=False,
                reason=f"Signal is {signal}; no new position allowed.",
                quantity=0,
                position_value=0,
            )

        # ---------------------------------------------------------
        # Rule 2: Stop trading if daily loss reaches 2%.
        # ---------------------------------------------------------
        max_daily_loss = self.account_equity * self.max_daily_loss_pct

        if daily_pnl <= -max_daily_loss:
            return RiskDecision(
                approved=False,
                reason=(
                    f"Daily loss limit reached: "
                    f"${daily_pnl:,.2f}"
                ),
                quantity=0,
                position_value=0,
            )

        # ---------------------------------------------------------
        # Rule 3: Limit each individual position to 10%.
        # ---------------------------------------------------------
        max_position_value = (
            self.account_equity * self.max_position_pct
        )

        # ---------------------------------------------------------
        # Rule 4: Limit total portfolio exposure to 60%.
        # ---------------------------------------------------------
        max_portfolio_value = (
            self.account_equity * self.max_portfolio_exposure_pct
        )

        remaining_exposure = max_portfolio_value - current_exposure

        if remaining_exposure <= 0:
            return RiskDecision(
                approved=False,
                reason="Maximum portfolio exposure reached.",
                quantity=0,
                position_value=0,
            )

        # Use whichever limit is smaller.
        allowed_value = min(
            max_position_value,
            remaining_exposure,
        )

        # ---------------------------------------------------------
        # Calculate number of shares.
        # ---------------------------------------------------------
        quantity = int(allowed_value // price)

        if quantity <= 0:
            return RiskDecision(
                approved=False,
                reason="Price is too high for the allowed position size.",
                quantity=0,
                position_value=0,
            )

        position_value = quantity * price

        # ---------------------------------------------------------
        # Rule 5: Ignore trades that are too small.
        # ---------------------------------------------------------
        if position_value < self.min_trade_value:
            return RiskDecision(
                approved=False,
                reason=(
                    f"Trade value ${position_value:,.2f} "
                    f"is below minimum ${self.min_trade_value:,.2f}."
                ),
                quantity=0,
                position_value=0,
            )

        # ---------------------------------------------------------
        # All risk checks passed.
        # ---------------------------------------------------------
        return RiskDecision(
            approved=True,
            reason="All risk checks passed.",
            quantity=quantity,
            position_value=position_value,
        )


# ==============================================================
# TEST THE RISK MANAGER
# ==============================================================

if __name__ == "__main__":

    risk_manager = RiskManager(
        account_equity=100_000
    )

    print("\n=== ALPHAGUARD RISK MANAGER ===\n")

    test_trades = [
        ("NVDA", 220.86, "BUY"),
        ("AAPL", 317.14, "HOLD"),
        ("MSFT", 506.95, "SELL"),
    ]

    for symbol, price, signal in test_trades:

        decision = risk_manager.check_trade(
            symbol=symbol,
            price=price,
            signal=signal,
            current_exposure=0,
            daily_pnl=0,
        )

        print(f"{symbol}")
        print(f"  Signal: {signal}")
        print(f"  Approved: {decision.approved}")
        print(f"  Quantity: {decision.quantity}")
        print(f"  Value: ${decision.position_value:,.2f}")
        print(f"  Reason: {decision.reason}")
        print()