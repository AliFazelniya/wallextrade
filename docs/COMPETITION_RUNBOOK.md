#Competition Runbook
### Wallex × Starcoach Algorithmic Trading Operations Manual
**Repository:** [`wallex`](file:///root/starcoach-hack/wallex) | **Frozen version:** `v0.6.0-phase14-audited` (`d49bd69`) | **Compilation date:** October 22, 2026

---

## 1. Introduction and strategic principles of operations

This document is a step-by-step standard operating procedure (SOP) for the preparation, commissioning, monitoring, emergency stop, and final settlement of the algorithmic robot in the Wallex x Starcoach Hackathon.

> [!IMPORTANT]
> **Separation of human decision making from algorithm:**
> All infrastructure prerequisites, authentication, activation of execution mode and check of legal obstacles (Blockers) are done manually by a human operator. But after issuing the official execution license, **all entry, exit, profit/loss limit management and order volume decisions will be made 100% algorithmically and automatically** by the system modules.

---

## 2. Preparing the environment and installing dependencies (Environment Setup)

### 2.1. Repository clone and frozen contest code deployment:```bash
# Go to the project directory
cd /root/starcoach-hack/wallex

# Ensuring you are on the inspected and frozen copy
git checkout master
git verify-tag v0.6.0-phase14-audited || git status
```

### 2.2. Preparing the Python virtual environment:
The system requires Python version 3.12:```bash
# Checking the existence of the virtual environment and activation
source .venv/bin/activate

# Install or update packages according to pyproject.toml
pip install -e .
```

### 2.3. Validation of environment variables (`.env`):
Copy the sample settings file if needed:```bash
cp .env.example .env
```The content of `.env` should look like this (never commit the keys in gitcommit):```ini
WALLEX_API_KEY=""                # API key provided by Wallex for the contest account
WALLEX_BASE_URL="https://api.wallex.ir"
TRADING_MODE="SHADOW"            # Until official confirmation: SHADOW
LIVE_EXECUTION_AUTHORIZED="False" # Until official confirmation: False code level software gate
GEMINI_API_KEY=""                # optional; In its absence, the definitive fallback is 100% automatically enabled
```

---

## 3. Checking the accuracy of settings and code integrity (Sanity Checks)

Before any deployment, run the following commands to ensure the 61 automated tests are fully healthy:

```bash
# Complete execution of integrity tests suite and operational failures
pytest tests/ -v

# Freeze strategy manifest hash verification
sha256sum config/frozen_strategy_manifest_v0.6.0.json
# Valid value must match 249c1e4af942156d2f1a602b58bd729969c660857e2d98f0158ac71c9fa75f66.
```

---

## 4. Setting up and running the test mode in the shadow (Shadow Mode Execution)

To connect to Valax web service and receive live data stream without sending any real order:

```bash
# Running live monitoring and logging decisions in the background
python scripts/run_production_rehearsal.py
```

### Real-time monitoring of the process (Monitoring):
To see the decision flow of the algorithm:```bash
# Live monitoring text log of events
tail -f logs/production_rehearsal_phase15.jsonl | jq .

# A summary review of the recent trading cycle
cat research/phase15_rehearsal_results.json | jq .
```

---

## 5. Guide for data health monitoring and error handling (Health & Error Handling)

### 5.1. Data Freshness Check:
The system automatically checks the age of candles with the [`validate_data_freshness`](file:///root/starcoach-hack/wallex/src/data/fetcher.py) method. If the time interval between the last candle and the server time is more than 30 minutes, the STALE_DATA warning will be recorded and the transaction will be prevented.

### 5.2. Wallex Rate Limit Management (HTTP 429):
- Wallex client has a built-in timing lock (`min_request_interval = 1.0s`).
- If the 429 error is received, the client automatically stops for 2 seconds (`backoff') and then tries again.

### 5.3. Connection disconnection or artificial intelligence model error (AI Timeout / Invalid JSON):
- In case of any network outage, 500 error or 5 second timeout when contacting Gemini, the [`RegimeClassificationAgent'](file:///root/starcoach-hack/wallex/src/agents/regime_agent.py) module will immediately activate **Deterministic Fallback**.
- In range or volatile phases, the system selects ``HOLD'' status and prevents the loss of capital.

---

## 6. Emergency stop, recovery after crash and resolution of discrepancies (Emergency & Recovery)

### 6.1. Manual Emergency Stop trigger:
If the human operator decides to immediately stop all activities:
1. Press `Ctrl + C` in the terminal or send `SIGTERM` signal:```bash
   pkill -f run_production_rehearsal.py
   ```2. Enabling the emergency stop flag in the risk engine by setting ``emergency_halt = True'' or executing the immediate cashout command.

### 6.2. Restoring the state of the portfolio after restarting (Crash Recovery):
The portfolio saves its state in each cycle with ``export_state()'' method. On restart:```python
from src.portfolio.accounting import PortfolioEngine
import json

# Load pre-crash save state
with open("logs/portfolio_state_checkpoint.json", "r") as f:
    saved_state = json.load(f)

# Detailed reconstruction of asset position, liquidity and P&L
portfolio = PortfolioEngine.from_state(saved_state)
```

### 6.3. Balance reconciliation with the exchange:
Before each new cycle, the `reconcile_with_exchange()` method reconciles the riyal and cryptocurrency balance with the `/v1/account/balances` output. If there is a difference of more than 1,000 Tomans, a warning is issued and the new transaction is blocked.

---

## 7. End-of-Competition Liquidation Protocol

According to the hackathon rules, at the end of the competition, the portfolio must be 100% converted into Tomans:

```bash
# Execution of the script to cash out all open cryptocurrency positions in Tomans with the order of Marketable Taker
python scripts/liquidate_to_toman.py
```- This command converts all open positions in symbols into cash by applying slippage and deducting the ticker fee and prints the output of the final balance of the portfolio.
- The final position of the portfolio should be `len(positions) == 0' and `all_holdings_liquidated_to_toman = True'.

---

## 8. Live Trading Go-Live Checklist

> [!CAUTION]
> **SAFETY LOCK:** There is no permission to change the status to live until each item in the table below has been officially approved by the organizers:

| row | Operational prerequisite Responsible for approval Current status
|---|---|---|---|
| 1 The official announcement of the exact day, hour and minute of the start of the competition Hackathon organizer ❌ Unknown (Blocker) |
| 2 | Announcing the exact date and time of the end of transactions and the deadline for sending Hackathon organizer ❌ Unknown (Blocker) |
| 3 Delivery of API keys to the exclusive account of the competition with transaction access Wallex support team ❌ Undelivered (Blocker) |
| 4 | Written confirmation of exemption from the overnight fee for credit extension and no debt Hackathon organizer ⚠️ Secondary ambiguity (Blocker) |
| 5 | Complete passing of 58 automated tests in the GitHub repository Engineering team ✅ Approved (58/58 pass) |
| 6 | Shadow test verification on Wallex live data Engineering team ✅ Confirmed (5 successful cycles) |
| 7 | The complete locking of 21 inactive markets and the inability to send orders Engineering team ✅ Confirmed (double gate) |
| 8 | Explicit and manual approval of the human operator (`live_execution_authorized=True`) | Senior team leader ⏳ Waiting for the removal of obstacles 1 to 4