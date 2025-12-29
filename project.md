
# Crypto AI Swing Bot — MVP Scope & Current Status

This document summarizes the current MVP scope, completed work, and the development position of the **Crypto AI Swing Bot**, so you can continue development seamlessly (including using Codex or another assistant).

---

## 🎯 MVP Goal

Build a **risk-managed automated crypto trading bot** that:
- focuses on **BTC/USDC**
- performs **2–4 high‑conviction trades per day**
- supports **both long & short trades**
- emphasizes **capital preservation**
- includes **realistic backtesting**
- **does not yet place real orders**

The MVP does **not** require:
- AI integration in live execution (only planned)
- live trading (to be added after validation)
- multiple asset support
- hyperparameter tuning

---

## 📌 Core Architecture (MVP)

```
[Historical Futures Data Loader]
            ↓
[Indicator Engine]  ← independent
            ↓
[Regime Detector: trending / range]
            ↓
[Strategy: pullback + breakout logic]
            ↓
[Trade Limiter: daily caps + reset]
            ↓
[Paper Brokerage Execution]
            ↓
[Session State Tracking]
            ↓
[Visualization: equity + drawdown]
```

---

## 📍 Current Project State (as of latest update)

| Component | Status | Notes |
|----------|--------|-------|
| **Symbol standardization (`BTC/USDC`)** | ✔ DONE | Entire system aligned |
| **Historical loader (USDC‑margined futures)** | ✔ DONE | Uses Binance COIN‑M |
| **Indicator engine** | ✔ DONE | SMA/EMA/RSI/MACD |
| **Regime detection** | ✔ DONE | Trending vs sideways |
| **Pullback strategy (long/short)** | ✔ DONE | Supports all regimes |
| **Trade limiter** | ✔ DONE | Max trades/day |
| **Paper broker** | ✔ DONE | SL/TP behavior |
| **Backtesting engine** | ✔ DONE | Iterates candles |
| **Session tracking** | ✔ DONE | PnL, equity curve |
| **Visualization** | ✔ DONE | equity + drawdowns |
| **Tests** | ✳ Partial | imports, signals, indicators |
| **Fees/slippage modeling** | ⏳ TODO | next |
| **AI filter** | ⏳ scaffolded | optional enhancement |
| **Trade markers visualization** | ⏳ TODO | nice-to-have |
| **Paper live mode** | ⏳ TODO | before real trading |
| **Real Binance execution** | 🚧 NOT STARTED | post‑MVP stage |

---

## 🛠 What You Can Do Right Now

| Task | Outcome |
|------|---------|
| run backtest | see equity + drawdowns |
| modify strategy rules | observe performance shifts |
| adjust limits | tune risk |
| add indicators | strategy experimentation |
| integrate AI as filter | risk-quality improvement |
| visualize trades on price | debugging |
| integrate futures execution | go live (post testing) |

---

## 🧪 How to Run Backtest (MVP)

From project root:

```bash
python -m backtesting.run_backtest
```

This runs:
- BTC/USDC futures
- 1h timeframe
- 2021 → 2022 by default
- shows equity curve + drawdowns

---

## 🚧 Next Logical Steps

> These extend MVP toward **production-grade automation**

### Phase 1 — Core improvements
- [ ] **Add fees & slippage**
- [ ] **Add funding cost modeling** (for futures realism)
- [ ] **Position sizing & risk % per trade**
- [ ] **Trade markers on charts**

### Phase 2 — Strategy refinement
- [ ] parameterize entry/exit rules
- [ ] validate multiple timeframes
- [ ] walk‑forward stability testing

### Phase 3 — AI layer integration
- [ ] apply **LLM filter only to actionable signals**
- [ ] compare raw strategy vs AI‑filtered
- [ ] measure improvement in expectancy/drawdown

### Phase 4 — Live deployment
- [ ] add futures execution client
- [ ] dry‑run mode w/ Discord or Telegram
- [ ] daily reports
- [ ] enable live ordering w/ guard rails

---

## 🔧 Files Most Important for Development

| Path | Purpose |
|------|---------|
| `src/backtesting/run_backtest.py` | entry point for backtests |
| `src/data/historical_data.py` | futures OHLCV loader |
| `src/strategy/btc_trend_pullback.py` | strategy logic |
| `src/backtesting/session_state.py` | equity & PnL tracking |
| `src/backtesting/visualizer.py` | charts |
| `src/execution/paper_broker.py` | TP/SL + execution |


---

## 🧭 Summary for Codex

> The system currently supports:  
> **BTC/USDC USDC‑margined futures backtesting** with  
> **pullback strategy, regime detection, trade limiting, paper execution, equity/drawdown visualization**.  
> Next steps are **fees/slippage**, **position sizing**, **trade markers**, and **AI filtering** before **live trading support**.

---

## 🤝 Contribution Principles (MVP)

- Keep **symbol = BTC/USDC**
- Do **not** break backtesting compatibility
- Strategy changes should **not** require execution rewrite
- Risk comes before returns

---

### Ready for Codex development.
