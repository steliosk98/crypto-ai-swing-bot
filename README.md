
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

## ▶️ Run Live Decision Cycle (no trading)

A single decision cycle using live candles:

```bash
python3 src/main.py
```

This **does not place real orders**.

---

## 🧪 Historical Testing (Local BTC/USD)

Using Bitstamp BTC/USD 1h data (local CSV) for 2018-05-15 → 2025-12-01:
- Mean Reversion strategy
- Return: 106025.24%
- Max Drawdown: -15.35%
- Trades: 4472

Per-year breakdown:
- 2018 (from 2018-05-15): Return 16.09%, Trades 345, Win Rate 53.62%, Max DD -14.93%
- 2019: Return 71.67%, Trades 554, Win Rate 55.05%, Max DD -15.35%
- 2020: Return 118.82%, Trades 588, Win Rate 59.86%, Max DD -14.39%
- 2021: Return 378.81%, Trades 546, Win Rate 62.64%, Max DD -10.45%
- 2022: Return 181.02%, Trades 553, Win Rate 62.03%, Max DD -9.83%
- 2023: Return 56.40%, Trades 561, Win Rate 57.93%, Max DD -5.70%
- 2024: Return 149.92%, Trades 628, Win Rate 60.99%, Max DD -6.59%
- 2025 (through 2025-12-01): Return 283.66%, Trades 562, Win Rate 70.46%, Max DD -4.40%

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
