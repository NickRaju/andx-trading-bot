# ANDX Trading Bot

A crypto trading bot for **ANDX Global** with a local dashboard. It trades long
and short on ANDX derivatives, runs four research-backed strategies, and starts
in a safe practice mode so you can learn before risking anything.

---

## ⬇️ Download & run (students start here)

**[➡️ Click here to download the bot (.zip)](https://github.com/NickRaju/andx-trading-bot/archive/refs/heads/main.zip)**

Then:

1. **Unzip it** — double-click the downloaded file to get the `andx-trading-bot-main` folder.
2. **Start it (one-time security step — every computer does this):**
   - **Mac:** **right-click** `Start Bot.command` → **Open** → **Open**. If you instead see *"Apple could not verify…"* with only **Done** / **Move to Trash**, click **Done**, then go to ** menu → System Settings → Privacy & Security**, scroll down, and click **"Open Anyway."** One time only.
   - **Windows:** double-click `Start Bot (Windows).bat`. If a blue "Windows protected your PC" box appears, click **More info → Run anyway**. If it says Python is missing, install it from [python.org](https://www.python.org/downloads/) (tick **"Add Python to PATH"**) and run it again.
   - First launch sets itself up automatically — give it about a minute.
3. **Your browser opens the dashboard** at `http://127.0.0.1:8300`. **That page is the bot.** Press **Start bot**.

It opens in **paper mode** — simulated money, real market prices, no account or keys needed. Trade, learn, and edit the code with zero risk.

---

## Going live with your own account

When you're ready to trade real money:

1. Create API keys in **your own ANDX account** with **trade permission only — never withdrawals**. Use *your* keys, never someone else's.
2. On the dashboard, open **Settings → Exchange & API keys**, paste your key + secret, and hit **Save & test keys** (it checks them against your account).
3. Switch **Trading mode** to **Live** and press Start. You'll be asked to confirm.

Your keys are stored **only on your own computer** (`secrets.json`, which is git-ignored and never uploaded) and are sent nowhere except ANDX.

---

## The dashboard

- **⚡ Derivatives** — trade long *and* short with leverage (stops enforced by the exchange). Off = spot only (buy / sell to USDT).
- **🛡️ Conservative** — patient, profit-focused mode: fewer high-conviction trades, smaller risk, wider stops, daily-loss circuit breaker.
- **Start / Stop / Stop & close all** — run control; "close all" flattens every position at market.
- **🌓** — light / dark theme.
- Tabs: **Overview** (equity, signals, positions), **Activity** (trade history, log), **Settings** (keys, config, risk).

## Strategies

- **Auto (Regime Switch)** — default; trend-follows in trends, mean-reverts in ranges (ADX decides).
- **EMA Trend-Following**, **RSI Mean-Reversion**, **Donchian Breakout** — force one style.

Risk controls: volatility-based position sizing, ATR stops, leverage/position caps, and a daily-loss kill switch. **ATR stop** = the auto exit price, set a few normal price-wiggles away from entry.

## Editing the code (competition)

This is a template — click **"Use this template"** to get your own copy you can edit and commit to. The bot's brains live in `strategies.py` (signals) and `risk.py` (sizing/stops). Change them, restart the bot, and watch the difference in paper mode.

## Disclaimer

Crypto trading — especially leveraged and short — can lose money quickly. Past
performance doesn't predict future results; no strategy wins in all markets.
This software is provided as-is, with no warranty. You are responsible for any
trades made with your keys. Start in paper mode. Start small.
