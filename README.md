
# Crypto AI Swing Bot

Adaptive, risk-aware cryptocurrency trading bot for **BTC/USDC futures**, built for
consistent performance and disciplined execution.

This project focuses on:
- operating across **uptrend, downtrend, and sideways markets**
- using **pullback & breakout signals** to capture directional moves
- **minimizing trading frequency** while maximizing trade quality
- **protecting capital** with strict daily risk limits
- **backtesting strategies realistically** before live deployment

---

## 🚀 Features

| Component | Status | Description |
|----------|--------|-------------|
| Market Data | ✔ | Live & historical USDⓈ-M futures OHLCV via CCXT |
| Indicators | ✔ | EMA, SMA, RSI, MACD via built-in indicator engine |
| Market Regime Detection | ✔ | Uptrend / Downtrend / Sideways classification |
| Strategy Engine | ✔ | Pullback longs, pullback shorts, sideways breakout |
| Trade Limiter | ✔ | Max trades/day + daily PnL caps |
| Daily Reset | ✔ | Reset at US Market Open (9:30 AM ET) |
| Paper Broker | ✔ | Simulated execution for backtesting |
| Backtesting | ✔ | Full walk-forward simulation |
| AI Filter | ⏳ optional | Placeholder for trade-quality evaluation |
| Live Trading | ⏳ future | Binance execution to be added safely |

---

## 🧠 Philosophy

The bot is designed to:
- take **fewer, higher-probability trades**
- avoid **low-quality sideways chop**
- **enter during liquidity-rich periods**
- use **clear, explainable rules**

This improves survivability and reduces churn.

---

## 📦 Installation

```bash
pip install -r requirements.txt
```

Recommended Python version: `>= 3.9`

Visualization requires `matplotlib` (included in `requirements.txt`).

---

## 🧪 Run a Backtest

```bash
python3 src/backtesting/run_backtest.py
```

The default configuration tests:
- BTC/USDC futures
- 1 hour timeframe
- 2023-01-01 → 2025-01-01

Modify the dates in `run_backtest.py` to test other periods.

---

## ▶️ Live Loop (Disabled by Default)

`src/main.py` runs the live trading loop. It will **not** place orders unless
`ENABLE_LIVE_TRADING=true` is set in `.env`.

---

## ⚡ Live Trading (Auto Execution)

Live trading uses Binance USDⓈ-M futures on BTC/USDC and **will place real orders**.
Set the following in `.env` before running:

```
ENABLE_LIVE_TRADING=true
BINANCE_API_KEY=...
BINANCE_API_SECRET=...
```

Optional risk configuration (defaults shown in `.env.example`):
- `RISK_PER_TRADE` (default 0.01 = 1% of equity at risk per trade)
- `MAX_DAILY_LOSS_PCT` (default 0.02)
- `MAX_TRADES_PER_DAY` (default 5)
- `LIVE_LEVERAGE` (default 1)

Start the live loop:

```bash
python3 src/main.py
```

---

## 🧠 Strategy (Mean Reversion Variant)

The current backtests use a mean-reversion rule set designed to capture
stretched moves back toward a short-term mean:
- RSI extremes as a trigger (oversold/overbought)
- minimum price stretch requirement before entry
- ATR-based sizing for stop-loss and take-profit
- trade limiter applied with daily reset at NYSE open

This variant aims to take high-conviction pullbacks and exit on reversion
rather than trend continuation.

## 🧪 Historical Testing (Local BTC/USD)

Using Bitstamp BTC/USD 1h data (local CSV) for 2018-05-15 → 2025-12-01.
Fees modeled as Binance USDC taker 0.05% per side:
- Mean Reversion strategy
- Return: 998.47%
- Max Drawdown: -41.11%
- Trades: 4523
- Win Rate: 60.51%

Per-year breakdown:
- 2018 (from 2018-05-15): Return -19.40%, Trades 346, Win Rate 53.47%, Max DD -22.97%
- 2019: Return -6.15%, Trades 563, Win Rate 54.71%, Max DD -29.31%
- 2020: Return 21.57%, Trades 597, Win Rate 59.80%, Max DD -19.45%
- 2021: Return 183.41%, Trades 554, Win Rate 62.64%, Max DD -11.51%
- 2022: Return 58.28%, Trades 557, Win Rate 61.94%, Max DD -13.88%
- 2023: Return -10.42%, Trades 564, Win Rate 57.98%, Max DD -21.31%
- 2024: Return 31.67%, Trades 631, Win Rate 60.86%, Max DD -14.41%
- 2025 (through 2025-12-01): Return 110.76%, Trades 574, Win Rate 70.03%, Max DD -6.81%

Equity curve (full window):
![Equity Curve](/equity_curve_full.png)

Run multi-window backtests (full + per-year):

```bash
python3 src/backtesting/run_window_backtests.py
```

## 🗂 Directory Structure

```
crypto-ai-swing-bot/
├─ src/
│  ├─ backtesting/
│  │  ├─ run_backtest.py
│  │  ├─ run_window_backtests.py
│  │  ├─ session_state.py
│  │  ├─ visualizer.py
│  ├─ data/
│  │  ├─ historical_data.py
│  │  ├─ market_data.py
│  ├─ execution/
│  │  ├─ paper_broker.py
│  ├─ filters/
│  │  ├─ trade_limiter.py
│  ├─ indicators/
│  │  ├─ indicator_engine.py
│  ├─ strategy/
│  │  ├─ btc_trend_pullback.py
│  │  ├─ regime.py
│  │  ├─ sideways.py
│  │  ├─ signal.py
│  │  ├─ base_strategy.py
│  ├─ utils/
│  │  ├─ logger.py
│  │  ├─ config.py
│  ├─ ai/
│  │  ├─ ai_filter.py
│  ├─ main.py
├─ requirements.txt
├─ README.md
```

---

## 📊 Daily Risk Reset Logic

Trading limits reset **once per day at 9:30 AM Eastern Time**, coinciding with
U.S. equities market open — a key liquidity event.

This helps avoid:
- overtrading in quiet hours
- unnecessary exposure during chop

---

## ⚠️ Disclaimer

This software is provided for **educational and research purposes**.
Cryptocurrency trading involves risk. Past performance does not guarantee
future results.

---

## 📄 License

MIT
