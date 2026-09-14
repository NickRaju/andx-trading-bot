# ANDX Trading Bot

A crypto trading bot with a local web dashboard for API keys, strategy
selection, risk controls, and live monitoring. The default venue is **ANDX
Global** (native connector, [docs.andx.one](https://docs.andx.one/)); Bybit /
Binance / OKX / KuCoin / Kraken futures are also supported via ccxt.

**ANDX specifics:** the connector speaks ANDX's GraphQL API v4
([docs.andxus.io](https://docs.andxus.io)) — candles, quotes, balances, and
orders are all native. Auth is just **API key + secret** (exchanged for a JWT
via `service_signin`, refreshed automatically). ANDX currently trades spot,
so the bot goes **long/flat** there — long signals buy the coin, short
signals sell back to USDT, leverage capped at 1×. The platform's margin API
(`margin_instruments`, `create_margin_order` with leverage/SL/TP) exists but
all margin instruments report `is_trading_on: false`; when ANDX enables
margin, real shorts can be added on top of `andx.py`'s margin hooks. On the
ccxt perp exchanges the bot goes **long and short** with leverage today.

## Quick start

```bash
cd trading_bot
../.venv/bin/python app.py
```

Open **http://127.0.0.1:8300**. The bot starts in **paper mode** — simulated
money against real market data, no API keys needed. Click **Start bot**.

## Strategies (chosen from published backtest research)

| Strategy | What it does | When it wins |
|---|---|---|
| **Auto (Regime Switch)** — default | Measures trend strength with ADX; routes to trend-following in trending markets, mean-reversion in ranges | All regimes — research shows the regime decides which family wins |
| **EMA Trend-Following** | EMA 21/55 crossover + ADX filter, ATR trailing stop, longs and shorts | Trending markets — the best-documented edge in crypto |
| **RSI Mean-Reversion** | Buys oversold at lower Bollinger band, shorts overbought at upper, exits at the mid-band; refuses to fade strong trends | Ranging markets (backtests: ~74% win rate, lower risk) |
| **Donchian Breakout** | Turtle-style: enter 20-bar breakouts, exit opposite 10-bar channel | Sustained momentum moves |

Risk management is volatility-adjusted (the approach academic backtests favor):
position size = (equity × risk-per-trade) / (ATR × stop multiple), with caps on
leverage, per-position notional, and open positions, plus a **daily-loss kill
switch** that flattens everything and pauses trading.

## Going live (please read)

1. **Paper-trade first** for at least a few weeks and check the stats.
2. Then try **Testnet** mode (exchange sandbox — real order flow, fake money).
   Create testnet keys on your exchange's testnet site.
3. Only then consider **Live**. Start with money you can afford to lose
   entirely, 1% risk per trade, and low leverage.

When creating API keys on your exchange, enable **trading permission only —
never withdrawals** — and IP-restrict the key to your machine if the exchange
supports it. Keys are stored in `trading_bot/secrets.json` with owner-only file
permissions, are shown only masked in the UI, and are sent nowhere except your
exchange. The dashboard binds to 127.0.0.1 only.

## Files

- `app.py` — Flask dashboard server (run this)
- `engine.py` — trading loop: signals → position reconciliation → stops
- `strategies.py` — indicators + the four strategies
- `risk.py` — sizing, ATR/trailing stops, kill switch
- `andx.py` — native ANDX GraphQL client (JWT auth, candles, orders, balances)
- `exchange.py` — market data (with fallback sources), paper + live + ANDX brokers
- `store.py` — settings, secrets, SQLite trade/equity history
- `bot.db` — created on first run

## Disclaimer

Trading cryptocurrency, especially with leverage and short positions, can lose
more than you expect, quickly. Past backtest performance does not guarantee
future results. No strategy wins in all regimes. This software is provided
as-is with no warranty; you are responsible for trades made with your keys.
