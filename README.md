# Crypto AI Swing Bot 🧠📈

Automated crypto trading bot that combines rule-based technical strategies with 
OpenAI-powered decision filtering to execute a small number of high-confidence 
trades per day — designed for steady long-term growth and reduced noise.

---

## 🚀 Current Status
Repository scaffolding complete — beginning implementation of core modules.

---

## 🧠 Vision
1. Fetch market data
2. Generate technical candidate setups
3. Filter using AI sentiment + reasoning
4. Enforce risk controls + daily trade limits
5. Execute trades via Binance

Only take trades when **multiple independent filters align**.

---

## 🛠 Tech Stack
- Python 3.11+
- Binance API via ccxt / python-binance
- Pandas, NumPy, TA indicators
- OpenAI for trade-quality filtering
- APScheduler for interval execution
- Loguru for structured logs

---

## 🔧 Setup

Clone repository:
```
git clone <YOUR_REPO_URL>
cd crypto-ai-swing-bot
```

Install dependencies:
```
pip install -r requirements.txt
```

Setup environment variables:
```
cp .env.example .env
```

Fill your keys in `.env`.

---

## ▶️ Run (placeholder)
```
python src/main.py
```

---

## ☑️ Roadmap
- [x] Repo scaffold
- [ ] Indicator engine
- [ ] Strategy logic
- [ ] AI trade filtering
- [ ] News / sentiment integration
- [ ] Position sizing & risk rules
- [ ] Backtesting module
- [ ] Live trading mode
- [ ] Dashboard UI (optional)

---

## 📝 License
MIT
