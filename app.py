import streamlit as st
import pandas as pd

from dashboard_core import run_dry_scan
from trader import get_account
from risk_manager import RiskManager


st.set_page_config(page_title="SentinelTrade", page_icon="📈", layout="wide")

st.title("📈 SentinelTrade")
st.caption("Risk-gated algorithmic trading agent — dry-run dashboard")

# --- Account summary ---
try:
    account = get_account()
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Equity", f"${float(account.equity):,.2f}")
    col2.metric("Cash", f"${float(account.cash):,.2f}")
    col3.metric("Buying Power", f"${float(account.buying_power):,.2f}")
    col4.metric("Status", str(account.status).replace("AccountStatus.", ""))
except Exception as e:
    st.error(f"Could not load account info: {e}")

st.divider()

# --- Risk rules reference ---
with st.expander("Risk Manager rules"):
    rm = RiskManager()
    st.markdown(
        f"""
        - **Max position size:** {rm.max_position_pct * 100:.0f}% of account equity per symbol
        - **Max portfolio exposure:** {rm.max_portfolio_exposure_pct * 100:.0f}% across all positions
        - **Daily loss circuit breaker:** {rm.max_daily_loss_pct * 100:.0f}%
        - **Minimum trade size:** ${rm.min_trade_value:,.2f}
        """
    )

st.divider()

# --- Run scan ---
if "scan_results" not in st.session_state:
    st.session_state.scan_results = None
    st.session_state.positions = None

if st.button("🔍 Run Dry-Run Scan", type="primary"):
    with st.spinner("Fetching market data and running signals..."):
        rows, positions = run_dry_scan()
        st.session_state.scan_results = rows
        st.session_state.positions = positions

if st.session_state.scan_results is not None:
    if st.session_state.positions:
        st.subheader("Existing Positions")
        pos_df = pd.DataFrame(
            [{"Symbol": s, "Shares": q} for s, q in st.session_state.positions.items()]
        )
        st.dataframe(pos_df, hide_index=True, use_container_width=True)

    st.subheader("Signals & Risk Decisions")

    df = pd.DataFrame(st.session_state.scan_results)

    def highlight_signal(val):
        if val == "BUY":
            return "color: #2FBF71; font-weight: bold"
        if val == "SELL":
            return "color: #D64545; font-weight: bold"
        if val == "SKIPPED":
            return "color: #6B7280; font-style: italic"
        return ""

    def highlight_approved(val):
        if val is True:
            return "color: #2FBF71; font-weight: bold"
        if val is False:
            return "color: #D64545"
        return ""

    styled = df.style.applymap(highlight_signal, subset=["Signal"]).applymap(
        highlight_approved, subset=["Approved"]
    )

    st.dataframe(styled, hide_index=True, use_container_width=True)

    st.info(
        "This dashboard is dry-run only. To submit real paper trades, run "
        "`uv run python agent.py --live` in your terminal."
    )
else:
    st.info("Click **Run Dry-Run Scan** to fetch live signals.")