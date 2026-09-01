# SentinelTrade

A risk-gated algorithmic trading agent built on Alpaca's paper trading platform.

Built for the Alpaca AI Trading Agents Hackathon (2026).

## What it does

SentinelTrade scans a watchlist of stocks, generates BUY/HOLD/SELL signals from
technical indicators, and routes every proposed trade through an independent
risk manager before anything is executed — all on Alpaca's **paper trading**
environment, so no real money is ever involved.

## Architecture

- **`market_data.py`** — pulls live daily price bars from Alpaca
- **`strategy.py`** — calculates 5-day / 20-day moving averages, RSI, and a
  composite score to generate a BUY / HOLD / SELL signal per symbol
- **`risk_manager.py`** — a hard, independent safety layer. Enforces:
  - Max 10% of account equity per position
  - Max 60% total portfolio exposure
  - 2% daily loss circuit breaker
  - $500 minimum trade size
- **`trader.py`** — submits orders to Alpaca's paper trading account, and
  checks existing positions so the agent never re-buys a stock it already holds
- **`agent.py`** — orchestrates the full pipeline end to end

## Usage

Install dependencies:

```bash
uv sync
```

Set your Alpaca paper trading API keys as environment variables:

```bash
$env:ALPACA_API_KEY="your_key_here"
$env:ALPACA_SECRET_KEY="your_secret_here"
```

Run in dry-run mode (default — prints what it would do, sends no orders):

```bash
uv run python agent.py
```

Run live against your Alpaca **paper** account:

```bash
uv run python agent.py --live
```

## Watchlist

SPY, QQQ, AAPL, MSFT, NVDA

## Disclaimer

This project only ever trades against Alpaca's paper trading environment.
No real capital is placed at risk at any point. This is not financial advice
and is not intended for use with a live brokerage account.

## Roadmap

- Backtesting harness for historical signal performance
- Multi-day P&L tracking feeding the daily loss circuit breaker
- Optional AI/LLM review layer for additional trade judgment above the risk manager
