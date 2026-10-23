# Comprehensive guide for reproducing results and implementing the system (Reproducibility Guide)

This guide describes unambiguous step-by-step instructions for contest judges and engineers to run the system, reproduce backtest results, and run Shadow Mode testing in a raw Linux environment.

---

## 1. Prerequisites and environment
- **Operating system:** Linux (tested on Ubuntu 22.04 / 24.04 LTS)
- **Python version:** Python 3.11 or 3.12 (used version: `Python 3.12.3`)
- **Package manager:** `pip` and virtual environment tool `venv`
- **Internet connection:** Direct or proxy access to connect to ``https://api.wallex.ir'' servers

---

## 2. Quick setup steps from the raw environment (Setup from Scratch)

```bash
# 1. Go to the repository directory
cd wallex

# 2. Creation and activation of Python virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 3. Install required packages and project dependencies
pip install -e .
pip install pytest pytest-asyncio

# 4. Creating an environment settings file from a safe sample
cp .env.example .env
```

---

## 3. Implementation of automatic tests and governance validation (Unit Testing)

To ensure the health of the computing layers, the risk engine and not accidentally sending live orders:

```bash
pytest tests/ -v
```

**Expected output:** 100% passing tests (12 out of 12 tests in less than 1 second) without any errors or sending real orders.

---

## 4. Reproduce historical backtest results on real Wallex data

To get live 30 days of 15 minute UDF candle data from Wallex and run the simulation:

```bash
python scripts/run_backtest.py BTCTMN ETHTMN
```

**Expected output:**
- Automatic report generation and update in [`docs/BACKTEST_REPORT.md`](BACKTEST_REPORT.md).
- Detailed reporting of net P&L, win rate, number of transactions, fees and confirmation of 100% balance settlement in Tomans at the end of the simulation.

---

## 5. Running shadow tests on live data (Live Shadow Run)

To view the process of live order book monitoring, feature extraction, AI classification, and audit trail logging:

```bash
python scripts/run_shadow.py
```

**Expected output:**
- Record decisions, agent's technical justification and risk assessment in the file [`logs/trading_decisions.jsonl`] (../logs/trading_decisions.jsonl).
- Generate summary of results in [`docs/SHADOW_TEST_REPORT.md`](SHADOW_TEST_REPORT.md).

---

## 6. Implementation of the final settlement protocol in Tomans (Liquidation Protocol)

To independently implement the settlement process and convert all positions into Tomans:

```bash
python scripts/liquidate_to_toman.py
```
