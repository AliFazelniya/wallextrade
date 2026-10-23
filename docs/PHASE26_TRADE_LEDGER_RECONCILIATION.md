# Compilation and independent audit of trading record and portfolio balance (Phase 26 Trade Ledger Reconciliation)
## Independent Trade-Level Reconciliation, Capacity Evolution & Portfolio Accounting

> **Repository:** [`wallex`](file:///root/starcoach-hack/wallex)  
> **Research branch:** `research/phase26-forensic-validation`  
> **Frozen base commit:** [`b494d60e211497f47ef3b79d6ae79a0726471172`](file:///root/starcoach-hack/wallex)  
> **Ledger Discrepancy Level:** **0.000000 Tomans (perfect balance)**

---

## 1. Aggregate reconciliation table of trading profit against portfolio profit

| Trading model Total number of transactions Total net profit of individual transactions (TMN) | Reported Total Portfolio Profit (TMN) | The amount of discrepancy (Discrepancy). Total exchange friction (fee + slip) |
|---|:---:|:---:|:---:|:---:|:---:|
| **Model A: exclusive H1 (structural trend)** | **33** | **63,034.80** | **63,034.80** | **0.00 TMN** | 125,647.78 TMN
| **Model B: Exclusive H3 (Lead-Leg Acceleration Leakage)** | **6** **48,707.86** | **48,707.86** | **0.00 TMN** | 22,137.50 TMN
| **Model C: integrated combination of H1+H3** | **35** **63,954.66** | **63,954.66** | **0.00 TMN** | 134,611.73 TMN

> [!NOTE]
> The algebraic sum of the realized profit of each transaction contained in the executive log matches exactly to 6 decimal places with the changes in the liquidity balance and the equity value of the account ($5,000,000 \to $5,063,954.66). There is no invisible profit or loss in the system.

---

## 2. Rooting and empirical proof of the change in the number of trades (Evolution from 19 to 33 Trades)

One of the fundamental questions of the audit was why the number of H1 transactions increased from **19 transactions** in phase 24 to **33 transactions** in phase 25? Has a calculation error occurred?

### Controlled experiment of changing portfolio capacity:
To answer this question, the execution engine of phase 25 was re-executed with two position capacity constraints:

```python
# Position capacity limit test in src/experimental/ensemble_engine.py
# Test 1: Phase 24 Single-Position Constraint
# Test 2: Phase 25 Multi-Position Constraint
```

| The condition of the simultaneous capacity of the portfolio Number of transactions H1 | H1 net profit (TMN) | Total Friction (TMN) | Compliance with project phases
|---|:---:|:---:|:---:|---|
| **Maximum 1 open position (`max_pos = 1`)** | **19** | **32,138.03** | **72,575.87** | **exactly matches phase 24** (19 transactions and 72.5k friction) |
| **Maximum 2 open positions (`max_pos = 2`)** | **33** | **63,034.80** | **125,647.78** | **exactly matches phase 25** (33 transactions and 125.6k friction) |

### The result of the audit, the reason for the change:
1. In phase 24, the trading simulator [`simulation_harness.py`](file:///root/starcoach-hack/wallex/src/experimental/simulation_harness.py#L132) used the single-position structure (`open_pos: Optional[Dict]`). This means that if a position was open on Solana, any structural signal on Ethereum or Bitcoin would be blocked to close the Solana position.
2. In phase 25, the joint portfolio architecture allowed to open up to **2 open positions at the same time** (allocation ceiling of 1 million Tomans, equivalent to 20% of the total capital).
3. As a result, in strong bullish market waves (such as W09 and W20), the system was able to manage Solana and Ethereum winning positions simultaneously; Therefore, the number of transactions jumped from 19 to 33 and profit from 32.1 thousand tomans to 63.0 thousand tomans.
4. For the H3 model, the capacity of 2 positions allowed the system to catch the momentum leakage on both sluggish altcoins (SOL and ETH) at the same time when Bitcoin jumps and increase the transactions from 4-5 to 6 transactions with a profit of 48.7 thousand tomans.
5. **Result:** This change is 100% caused by the documented rules of the portfolio architecture and there is no arithmetic error involved in it.

---

## 3. An autopsy of the distribution of trading profits and losses based on assets and the reason for exit

### A) Breakdown of performance by trading symbol in model A (H1):
- **Solana (SOLTMN):** 12 transactions **20,789.98+ tomans profit** | Average 1,732+ Tomans per transaction
- **Ethereum (ETHTMN):** 10 transactions **44,175.99+ Tomans profit** | Average 4,417+ Tomans per transaction
- **Bitcoin (BTCTMN):** 11 transactions **Loss 1,931.17 Tomans** | Average - 175 tomans per transaction

### b) Separation according to the reason for leaving the position in model A (H1):
- **Exit in profit target (`H1_TP' with a profit limit of 4.5%+):** 8 transactions **157,550+ Tomans Profit** (Maker Liquidity Generator)
- **Emergency exit of loss limit (`H1_SL' with a loss limit of -2.2%):** 9 transactions **Loss of 132,284 Tomans** (Order Taker)
- **Break-even moving loss limit exit (`TRAILING_BE'):** 5 transactions **3,633-tomans marginal loss** (entry and exit fees)
- **Exit in the final 72-hour sail (`WIND_DOWN' at 66 hours with profit):** 10 trades | **47,478+ Tomans Profit** (Maker Liquidity Builder)
- **FORCED_BOUNDARY_LIQUIDATION final boundary of 72 hours:** 1 transaction | **Loss of 6,076 Tomans**

### Audit conclusion and approval: ``PASS''
The account balance, record of individual transactions, the order execution process and the calculation logic of the portfolio were confirmed without the slightest error.