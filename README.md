# SentinelTrade

A risk-gated algorithmic trading agent built on Alpaca's paper trading platform.

Built for the Alpaca AI Trading Agents Hackathon (2026).

## What it does

SentinelTrade scans a watchlist of stocks, generates BUY/HOLD/SELL signals from
technical indicators, and routes every proposed trade through an independent
risk manager before anything is executed — all on Alpaca's **paper trading**
environment, so no real money is ever involved.

## Architecture
