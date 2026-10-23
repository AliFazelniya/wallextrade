# Final evidence audit report, signal-to-trade funnel analysis and 72-hour window evaluation (Phase 20.2)

> **Audit Status:** Final and Quantitatively Adapted (Independently Reconciled & Audited)  
> **Repository:** [`wallex`](..)  
> **release frozen commit:** [`b494d60e211497f47ef3b79d6ae79a0726471172`](..)  
> **valid tags:** `v1.0.0-phase20-frozen-release` and `v0.12.0-phase20-audited`  
> **Frozen Strategy Manifest Hash:** `249c1e4af942156d2f1a602b58bd729969c660857e2d98f0158ac71c9fa75f66`  
> **Live execution authorization:** `live_execution_authorized = False` (completely blocked and disabled)

---

## 1. Complete Signal-to-Trade Funnel Reconciliation

### 1.1. Detailed definitions of units and words (Unit Definitions)
To resolve any conceptual ambiguity, the statistical units in this audit are clearly separated:
1. **Trading candle (Candle / Bar):** A 15-minute OHLCV time frame in the data set.
2. **Candidate Signal:** A candle that meets the basic technical conditions ($\text{EMA}_{20} > \text{EMA}_{50}$ and $50 \le \text{RSI}_{14} \le 69$ and $\text{VolRatio} \ge 1.10$).
3. **Filter Veto:** Active obstruction by artificial intelligence regime or spread ceiling of 0.20% at the moment of candidate signal issuance.
4. **Rejection due to open position (In-Position Skip):** Rejection of the candidate signal simply because the strategy has an active open position at that moment and respects the single-position limit of the portfolio.
5. **Order Submitted:** Limit Taker purchase order sent to the portfolio engine.
6. **Completed Round-Trip Trade:** Complete entry and exit cycle of a position (buying and selling with profit limit, loss limit, or final liquidation).

---

### 1.2. Zero-Residual Funnel Balance

The equation of survival of signals in both strategies:
$$\text{Candidate Signals} \equiv \text{AI Vetoes} + \text{Spread Vetoes} + \text{In-Position Skips} + \text{Risk Vetoes} + \text{Orders Submitted}$$

| Funnel stage of decision and implementation (Funnel Stage). Artificial intelligence (AI) strategy Deter ministic strategy (Det) | Difference (Delta) | Matching status
|---|:---:|:---:|:---:|:---:|
| **1. Total net candles (after 60 warm-up candles)** | 8,576 candles 8,576 candles 0 | ✅ VERIFIED |
| **2. Technical candidate signals (Candidate Signals)** | **671 signals** | **671 signals** | **0** ✅ VERIFIED |
| **3. AI Regime Vetoes** | **553 vetoes** (82.4%) | **0 veto** (0.0%) | 553+ ✅ VERIFIED |
| **4. Veto gate spread (Spread > 0.20% on Free Bars)** | **9 veto** | **35 veto** | 26- ✅ VERIFIED |
| **5. Rejection due to having an open position (In-Position Skips)** | **87 signals** | **600 signals** | 513- | ✅ VERIFIED |
| **6. Risk Vetoes** | **0 veto** | **0 veto** | 0 | ✅ VERIFIED |
| **7. Orders Submitted** | **22 orders** | **36 orders** | 14- ✅ VERIFIED |
| **8. Unfilled Orders** | **0 order** | **0 order** | 0 | ✅ VERIFIED |
| **9. Filled orders (Filled Orders - 100%)** | **22 orders** | **36 orders** | 14- ✅ VERIFIED |
| **10. Opened positions (Positions Opened)** | **22 positions** | **36 position** | 14- ✅ VERIFIED |
| **11. Closed positions (Completed Trades)** | **22 deals** | **36 transactions** | **14-** | ✅ VERIFIED |
| **Mathematic balance of the funnel (Accounting Identity Sum)** | **$553 + 9 + 87 + 0 + 22 = $671** | **$0 + 35 + 600 + 0 + 36 = $671** | **Remaining: 0** | ✅ **PERFECT BALANCE** |

---

## 2. Rooting and dissection of the claim "14 transaction filter" (Matched Trade-Level Audit)

### 2.1. Is "14 filtered transactions" caused by static veto?
**No.** Trade-by-Trade Matched Analysis proves that the difference of 14 trades is a **Sequential Path-Dependent Emergence**, not a Static 1-to-1 Mask.

### 2.2. Breakdown of transaction entry points:
- **Trades with exactly the same entry point (Common Entries):** exactly **10 trades** were started in both strategies at the same candle and price.
- ** Deterministic-Only Entries: ** 26 transactions** were made by the Deterministic system, which artificial intelligence did not enter (due to range/bear regime veto or spread ceiling).
- ** AI-Only Entries: ** 12 transactions** were made by artificial intelligence, which Deterministic system could not enter!  
  *Reason:* At the time of occurrence of these 12 high-quality signals, the deterministic system was stuck and locked in a previous loss position (caused by the lack of veto of noise signals).

$$\text{Net Trade Difference} = \text{Deterministic-Only} - \text{AI-Only} = 26 - 12 = \mathbf{14\text{ trade}}$$

> [!IMPORTANT]
> Artificial intelligence actually vetoed 26 Deter Ministic positions and instead managed to hunt 12 new positions due to the release of capital capacity; As a result, the net difference of closing positions was equal to 14 transactions ($36 - 22 = $14).

---

## 3. Evaluation of 72-hour time windows based on UTC real time (Task 2 & Task 4)

### 3.1. Defining exact time boundaries (UTC Elapsed Time Boundaries)
- **The first data candle:** `2026-07-24 11:15:00+00:00`
- **Warm-up period:** The first 60 candles (15 hours) to stabilize EMA and ATR
- **Start of time evaluation ($T_0$):** `2026-07-25 02:15:00+00:00` (candle index 60)
- **End of time evaluation ($T_{\text{end}}$):** `2026-10-22 11:15:00+00:00`
- **Length of the elapsed time period:** 2,145 calendar hours (89 days and 9 hours)
- **Total number of 72-hour calendar windows:** $2,145 \div 72 = $29.79 Window:
  - **29 full 72-hour windows** (2,088 hours)
  - **1 incomplete window** (window 30 for 57 hours, 229 candles)

---

### 3.2. Full performance table for 30 72-hour UTC time windows

In the competition evaluation model, each window is started as an independent 3-day competition with an initial capital of 5,000,000 Tomans in cash, and in the last second of the window (72-hour limit), any open position is converted into cash at the market rate:

| Window ID Start Time (UTC) | End Time (UTC) | Window status Candles (missing) | Number of transactions Net efficiency Net Profit/Loss (TMN) | Profitability status
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **W01** | 2026-07-25 02:15 | 2026-07-28 02:15 | Full (72h) | 288 (0) | 1 | -0.28% -13,894 | LOSS |
| **W02** | 2026-07-28 02:15 | 2026-07-31 02:15 | Full (72h) | 288 (0) | 1 | +0.02% | +923 **Profit (WIN)** |
| **W03** | 2026-07-31 02:15 | 2026-08-03 02:15 | Full (72h) | 288 (0) | 0 | 0.00% | 0 | Neutral (NEUTRAL) |
| **W04** | 2026-08-03 02:15 | 2026-08-06 02:15 | Full (72h) | 288 (0) | 1 | -0.27% -13,718 | LOSS |
| **W05** | 2026-08-06 02:15 | 2026-08-09 02:15 | Full (72h) | 288 (0) | 0 | 0.00% | 0 | Neutral (NEUTRAL) |
| **W06** | 2026-08-09 02:15 | 2026-08-12 02:15 | Full (72h) | 288 (0) | 0 | 0.00% | 0 | Neutral (NEUTRAL) |
| **W07** | 2026-08-12 02:15 | 2026-08-15 02:15 | Full (72h) | 288 (0) | 0 | 0.00% | 0 | Neutral (NEUTRAL) |
| **W08** | 2026-08-15 02:15 | 2026-08-18 02:15 | Full (72h) | 288 (0) | 1 | -0.08% | -4,095 | LOSS |
| **W09** | 2026-08-18 02:15 | 2026-08-21 02:15 | Full (72h) | 288 (0) | 3 +1.20% +60,091 | **Profit (WIN)** |
| **W10** | 2026-08-21 02:15 | 2026-08-24 02:15 | Full (72h) | 288 (0) | 1 | -0.03% -1,438 | LOSS |
| **W11** | 2026-08-24 02:15 | 2026-08-27 02:15 | Full (72h) | 288 (0) | 2 | -0.00% | -23 | NEUTRAL |
| **W12** | 2026-08-27 02:15 | 2026-08-30 02:15 | Full (72h) | 288 (0) | 2 | -0.44% -22,161 | LOSS |
| **W13** | 2026-08-30 02:15 | 2026-09-02 02:15 | Full (72h) | 288 (0) | 1 | -0.11% -5,312 | LOSS |
| **W14** | 2026-09-02 02:15 | 2026-09-05 02:15 | Full (72h) | 288 (0) | 2 | +0.04% | +1,754 | **Profit (WIN)** |
| **W15** | 2026-09-05 02:15 | 2026-09-08 02:15 | Full (72h) | 288 (0) | 1 | -0.14% -6,754 | LOSS |
| **W16** | 2026-09-08 02:15 | 2026-09-11 02:15 | Full (72h) | 288 (0) | 1 | -0.12% -6,077 | LOSS |
| **W17** | 2026-09-11 02:15 | 2026-09-14 02:15 | Full (72h) | 288 (0) | 0 | 0.00% | 0 | Neutral (NEUTRAL) |
| **W18** | 2026-09-14 02:15 | 2026-09-17 02:15 | Full (72h) | 288 (0) | 1 | -0.29% -14,430 | LOSS |
| **W19** | 2026-09-17 02:15 | 2026-09-20 02:15 | Full (72h) | 288 (0) | 1 | +0.03% | +1,518 | **Profit (WIN)** |
| **W20** | 2026-09-20 02:15 | 2026-09-23 02:15 | Full (72h) | **283 (5)** | 1 | -0.04% -1,771 | LOSS |
| **W21** | 2026-09-23 02:15 | 2026-09-26 02:15 | Full (72h) | 288 (0) | 0 | 0.00% | 0 | Neutral (NEUTRAL) |
| **W22** | 2026-09-26 02:15 | 2026-09-29 02:15 | Full (72h) | 288 (0) | 1 | +0.12% +5,894 | **Profit (WIN)** |
| **W23** | 2026-09-29 02:15 | 2026-10-02 02:15 | Full (72h) | 288 (0) | 3 -0.16% -8,169 | LOSS |
| **W24** | 2026-10-02 02:15 | 2026-10-05 02:15 | Full (72h) | 288 (0) | 1 | +0.30% +15,139 | **Profit (WIN)** |
| **W25** | 2026-10-05 02:15 | 2026-10-08 02:15 | Full (72h) | 288 (0) | 0 | 0.00% | 0 | Neutral (NEUTRAL) |
| **W26** | 2026-10-08 02:15 | 2026-10-11 02:15 | Full (72h) | 288 (0) | 0 | 0.00% | 0 | Neutral (NEUTRAL) |
| **W27** | 2026-10-11 02:15 | 2026-10-14 02:15 | Full (72h) | 288 (0) | 0 | 0.00% | 0 | Neutral (NEUTRAL) |
| **W28** | 2026-10-14 02:15 | 2026-10-17 02:15 | Full (72h) | 288 (0) | 1 | -0.33% -16,348 | LOSS |
| **W29** | 2026-10-17 02:15 | 2026-10-20 02:15 | Full (72h) | 288 (0) | 0 | 0.00% | 0 | Neutral (NEUTRAL) |
| **W30** | 2026-10-20 02:15 | 2026-10-23 02:15 | Incomplete (57h) | 229 (0) | 1 | -0.06% | -3,243 | LOSS |

---

### 3.3. Corrected Historical Profitable-Window Fraction

| Categories of windows Number in 29 complete windows Percentage of all 29 windows A total of 30 windows Percentage of all 30 windows
|---|:---:|:---:|:---:|:---:|
| **Winning and profitable windows (Return > 0.0%)** | **6 windows** | **20.69% (20.7%)** | **6 windows** | **20.0%** |
| **Neutral and no-trade windows (Return = 0.0%)** | **11 windows** | **37.93% (37.9%)** | **11 windows** | **36.7%** |
| **Losing windows (Return < 0.0%)** | **12 windows** | **41.38% (41.4%)** | **13 windows** | **43.3%** |
| **total total** | **29 windows** | **100.0%** | **30 windows** | **100.0%** |

> [!CAUTION]
> **Statistical correction of phase 20.1 report:**  
> The previous claim of "10 winning windows equal to 34.5%" was not reproduced and is definitively rejected. The actual and reproduced value in the independent simulation with refinement at the 72-hour mark is **6 profitable windows out of 29 full windows (20.7%)**, which exactly matches the initial phase 13 baseline results in document [`research/phase13_validation_results.json#L281`](../research/phase13_validation_results.json#L281).
>
> **Critical distinction of descriptive statistics from predictive probability:**  
> This index is simply a "Historical Profitable-Window Fraction" in specific market conditions of the last 90 days. This number should in no way be interpreted as a "mathematical probability of winning an upcoming race" or "guaranteed profitability in a random 72-hour window".

---

## 4. Independent reconstruction of profit and loss attribution (Task 3 — P&L Attribution)

### 4.1. Comprehensive and definitive comparison of portfolio accounting components:

| Financial and accounting evaluation component Artificial intelligence (AI) strategy Deter ministic strategy (Det) | Difference / Superiority (Delta) | Audit analysis
|---|:---:|:---:|:---:|---|
| **Total number of closed transactions** | **22 deals** | **36 transactions** | **14- transaction** | Reducing noise and trading friction
| **ideal gross profit without slippage** | 119,545.94 Tomans 152,994.68 Tomans 33,448.74 Tomans Deter Ministik's lead in gross profit
| **Modeled slippage fee (0.15%)** | **24,562.28 Tomans** | **40,916.43 Tomans** | **Saving 16,354.15+ Tomans** | Artificial intelligence slippage savings
| **Gross operating profit (Modeled Gross P&L)** | **94,983.65 Tomans** | **112,078.25 Tomans** | **-17,094.60 Tomans (-15.25%)** | Deterministik made more gross profit
| **paid fees of Wallex exchange** | **63,429.08 Tomans** | **103,925.51 Tomans** | **Save 40,496.43+ Tomans** | Significant reduction of fees by artificial intelligence
| **Total cost savings and friction** | — — **56,850.58+ Tomans (1.14%)** | Fee + slippage
| **Net Realized P&L** | **+31,554.57 Tomans** | **+8,152.74 Tomans** | **+23,401.83 tomans definite superiority** | Net profit after deducting all frictions
| **Final return on total capital** | **+0.63%** | **+0.16%** | **+0.47% excess yield** | Based on the initial capital of 5,000,000 tomans
| **Maximum capital loss in Tomans (Max DD)** | **67,760.03 Tomans** | **91,396.91 Tomans** | **23,636.88 Tomans to reduce risk** | Better protection of capital
| **Maximum capital loss percentage (Max DD %)** | **1.35%** | **1.80%** | **0.45% decrease in drawdown** | In the safe range of 5.0% of the competition

### 4.2. Mathematical proof of profit assignment equation (Reconciliation Proof):
$$\Delta \text{Net Realized P\&L} = \Delta \text{Fee Savings} - \Delta \text{Gross Profit Sacrificed}$$
$$40,496.43\text{ TMN} - 17,094.60\text{ TMN} = \mathbf{23,401.83\text{ TMN}} \equiv \Delta \text{Net P\&L}$$

> [!NOTE]
> This mathematical proof shows that the superiority of artificial intelligence was not at all due to "magical prediction of the direction of the market" (Alpha); Rather, by sacrificing 17,095 Tomans of gross marginal profit, artificial intelligence has managed to pay 40,496 Tomans less fees to the exchange and gain its net advantage of 23,402 Tomans by reducing exchange costs.

---

## 5. Data accuracy audit against time coverage (Task 5 — Data Coverage vs Record Integrity)

### 5.1. Detailed breakdown of data audit definitions:
1. Record integrity (Record Integrity - PASS):  
   The dataset does not contain any incomplete data, nulls, broken rows, negative prices, out of chronological order, or duplicate records. All 8,636 BTC records are fully valid and mined directly from the exchange's API.
2. **Temporal Coverage - DOCUMENTED GAPS:**  
   The complete 90-day time grid ($89\text{d} 9\text{h}$) contains 8,641 15-minute time points; While the available data has 8,636 candles (5 candles missing in BTC).
   - **main gap:** 5 consecutive candles on 09-22-2026 between 03:00 and 04:00 UTC are missing due to the technical maintenance announced by Wallex exchange.
   - **Altcoins gaps:** 7 candles in ETH and 6 candles in SOL (including the outage of September 22nd and intermittent outages of October 19th).

### 5.2. How to manage gaps in backtesting and strategy:
- The system has refused to generalize data (Forward-fill) or assume order execution at imaginary prices during gaps.
- In the W20 time window (including September 22), the number of processed candles was recorded as 283 instead of 288, and no liquidity or transactions were simulated during the closed hours of the exchange.

---

## 6. The results of regression and reproducibility tests (Reproducibility & Verification)

### 6.1. Implementation of unit and system tests:```bash
cd wallex && .venv/bin/pytest tests/
```**Execution result:**```
tests/test_ai_agent.py ....                                              [  6%]
tests/test_data_validation.py .....                                      [ 14%]
tests/test_exchange_adapter.py ...........                               [ 32%]
tests/test_features.py ....                                              [ 38%]
tests/test_operational_failures.py ..............                        [ 61%]
tests/test_phase14_reconciliation.py .....                               [ 69%]
tests/test_portfolio.py ......                                           [ 79%]
tests/test_portfolio_engine.py .                                         [ 80%]
tests/test_risk_engine.py .........                                      [ 95%]
tests/test_strategies.py ...                                             [100%]

============================== 62 passed in 2.68s ==============================
```

### 6.2. Gate Integrity Validation:```bash
git rev-parse HEAD
# b494d60e211497f47ef3b79d6ae79a0726471172 (freeze commit left unchanged)
```

---

## 7. Remaining barriers and live operational risks (Unresolved Blockers)

Despite the accuracy of quantitative calculations, the following operational hurdles still stand in the way of enabling Live:
1. **Obstacle B-01 (API and Infrastructure Keys):** Failure to receive the unique keys of the competition account from the organizing team.
2. **Obstacle B-02 (server-side loss limit):** Wallex platform does not support OCO and stop-loss orders on the exchange side; The loss limit is managed by software in the robot, which is a risk in case of an internet outage.
3. **Barrier B-03 (API call rate ceiling):** The limit of 30 to 60 requests per minute requires continuous monitoring in case of increased fluctuations.
4. **Obstacle B-05 (Dependence on human operator):** The necessity of manual monitoring by human operator within 72 hours to confirm the complete liquidation of positions in Tomans.

---

## 8. Final verdict of phase 20.2 audit (Final Verdict)

### Technical dimension and computational adaptation (Technical Integrity):
> **Status: ✅ PASS / DEFECTS RECONCILED**  
> The signal funnel was adapted to the trade with zero residual (Residual: 0), the dynamic phenomenon of the difference of 14 trades was proved by matching the trade level, the assignment of gross profit and saving of commission was proved with Toman accuracy, and the percentage error of the profitable windows was corrected and returned to the actual historical fraction of 20.7% (6 out of 29).

### After Live Execution Authorization:
> **Status: 🛑 NOT AUTHORIZED**  
> The key variable [`live_execution_authorized = False`](../config/frozen_strategy_manifest_v0.6.0.json) is preserved unchanged throughout the repository. It is strictly forbidden to send any real orders to the exchange until the official keys of the exchange are delivered by the organizer and the operational obstacles are removed.