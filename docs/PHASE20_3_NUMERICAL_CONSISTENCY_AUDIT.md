# Audit report of computational compliance, accounting accuracy and comparative validation of windows (Phase 20.3)

> **Audit Status:** Final, Reproduced and Fully Adapted (Independently Reconciled & Audited)  
> **Repository:** [`wallex`](file:///root/starcoach-hack/wallex)  
> **release frozen commit:** [`b494d60e211497f47ef3b79d6ae79a0726471172`](file:///root/starcoach-hack/wallex)  
> **valid tags:** `v1.0.0-phase20-frozen-release` and `v0.12.0-phase20-audited`  
> **Frozen Strategy Manifest Hash:** `249c1e4af942156d2f1a602b58bd729969c660857e2d98f0158ac71c9fa75f66`  
> **Live execution authorization:** `live_execution_authorized = False` (completely blocked and disabled)

---

## 1. Accurate matching of maximum drawdown reconciliation (Task 1 — Maximum Drawdown Reconciliation)

### 1.1. Reconstruction of the daily value curve of the portfolio (Mark-to-Market Equity Curve)
Check the implementation in [`src/portfolio/accounting.py#L235-L242`](file:///root/starcoach-hack/wallex/src/portfolio/accounting.py#L235-L242) and [`src/backtest/engine.py#L261-L270`](file:///root/starcoach-hack/wallex/src/backtest/engine.py#L261-L270) shows that the total value of the portfolio in each 15-minute candle is calculated as **Mark-to-Market Total Equity**:
$$\text{Total Equity} = \text{Cash (TMN)} + \sum (\text{Position Quantity} \times \text{Current Price})$$

The capital value peak ($\text{Peak}$) is dynamically updated over time and the capital loss is obtained from the following relationship:
$$\text{Drawdown (TMN)} = \text{Peak Equity} - \text{Current Equity}$$

---

### 1.2. Finding the roots of percentages and the duality of the denominator of the fraction (Peak Equity vs Initial Capital)

| Drawdown evaluation index Artificial intelligence (AI) strategy Deter ministic strategy (Det) | Difference / risk reduction Audit status
|---|:---:|:---:|:---:|:---:|
| **Maximum capital loss in Tomans (Max DD)** | **67,760.03 Tomans** | **91,396.91 Tomans** | **23,636.88 Tomans** | ✅ VERIFIED |
| **Time of capital loss peak (UTC)** | `2026-09-19 06:15:00` | `2026-10-20 01:00:00` | — ✅ VERIFIED |
| **Capital value peak at the moment of occurrence (Peak)** | 5,031,176.04 Tomans 5,080,683.91 Tomans — ✅ VERIFIED |
| **The bottom of the capital value at the moment of occurrence (Trough)** | 4,963,416.00 Tomans 4,989,287.00 Tomans — ✅ VERIFIED |
| **Financial standard definition: percentage of the top of the portfolio** | **1.3468% $\approx$ 1.35%** | **1.7989% $\approx$ 1.80%** | **0.4521%- points** | ✅ VERIFIED |
| **Alternative definition: percentage of initial capital (5M)** | **1.3552% $\approx$ 1.36%** | **1.8279% $\approx$ 1.83%** | **0.4727%- points** | ⚠️ **CLARIFIED** |

### 1.3. Reproduced calculations comparing capital loss:
1. **Absolute monetary difference of capital loss:**
   $$\Delta \text{Max DD (TMN)} = 91,396.91 - 67,760.03 = \mathbf{23,636.88\text{Tomans}}$$
2. **Difference in the percentage of initial capital (Percentage Points of Initial Capital):**
   $$\Delta \text{DD}_{\text{init}} = 1.8279\% - 1.3552\% = \mathbf{0.4727\%\text{ percentage points}}$$
3. **Difference in the percentage of peak capital (Percentage Points of Peak Equity):**
   $$\Delta \text{DD}_{\text{peak}} = 1.7989\% - 1.3468\% = \mathbf{0.4521\%\text{ percentage points}}$$
4. **Relative reduction of capital loss compared to the ministic strategy:**
   $$\text{Relative DD Reduction} = \frac{23,636.88}{91,396.91} = \mathbf{25.86\%}$$

> [!NOTE]
> The values of 1.35% and 1.80% reported in phase 20.2 are completely correct and are directly calculated from **dividing the Toman drop by the corresponding peak of the portfolio value** ($\text{Peak}$) according to the classic portfolio management formula. If the fixed initial capital base is 5,000,000 tomans, the amounts rounded to two decimal places will be **1.36%** and **1.83%** respectively.

---

## 2. Corresponding comparison of both strategies in independent 72-hour windows (Task 2 — Cross-Strategy 72h Windows)

### 2.1. Conditions and assumptions of comparative evaluation:
- **Time boundaries:** Evaluation time origin $T_0 = \text{2026-07-25 02:15:00 UTC}$, end $T_{\text{end}} = \text{2026-10-22 11:15:00 UTC}$.
- **Capital and Settlement:** Each window is an independent 3-day competition period with 5,000,000 Tomans initial cash capital; On the last candle of the interval, any open positions are cleared and the clearing gains/losses are included in the window performance.
- **Definition of window status:**
  - **Profit (WIN):** Net return $> +0.001\%$
  - **NEUTRAL:** Net return between $-0.001\%$ and $+0.001\%$ (mainly no trade)
  - **LOSS:** Net return $< -0.001\%$

---

### 2.2. Complete comparative table of 29 full 72-hour windows + 1 incomplete window

| window | Start Date (UTC) | End date (UTC) | AI efficiency The efficiency of Det | Efficiency difference (AI - Det) | AI Net Profit (TMN) | Net Profit Det (TMN) | AI Status | Status Det | AI transactions Transactions Det | The missing candle
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **W01** | 2026-07-25 02:15 | 2026-07-28 02:15 | -0.28% -0.15% -0.13% -13,894 | -7,358 | LOSS | LOSS | 1 | 1 | 0 |
| **W02** | 2026-07-28 02:15 | 2026-07-31 02:15 | +0.02% | +0.14% -0.12% +923 +7,078 | WIN | WIN | 1 | 1 | 0 |
| **W03** | 2026-07-31 02:15 | 2026-08-03 02:15 | **0.00%** | **-0.38%** | **+0.38%** | **0** | **-18,918** | **NEUTRAL** | **LOSS** | **0** | **2** 0 |
| **W04** | 2026-08-03 02:15 | 2026-08-06 02:15 | -0.27% -0.28% +0.01% | -13,718 | -14,142 | LOSS | LOSS | 1 | 1 | 0 |
| **W05** | 2026-08-06 02:15 | 2026-08-09 02:15 | **0.00%** | **-0.19%** | **+0.19%** | **0** | **-9,305** | **NEUTRAL** | **LOSS** | **0** | **1** | 0 |
| **W06** | 2026-08-09 02:15 | 2026-08-12 02:15 | **0.00%** | **-0.16%** | **+0.16%** | **0** | **-8,012** | **NEUTRAL** | **LOSS** | **0** | **1** | 0 |
| **W07** | 2026-08-12 02:15 | 2026-08-15 02:15 | **0.00%** | **-0.29%** | **+0.29%** | **0** | **-14,481** | **NEUTRAL** | **LOSS** | **0** | **1** | 0 |
| **W08** | 2026-08-15 02:15 | 2026-08-18 02:15 | -0.08% | +0.04% | -0.12% | -4,095 | +1,845 | LOSS | WIN | 1 | 1 | 0 |
| **W09** | 2026-08-18 02:15 | 2026-08-21 02:15 | +1.20% | +0.99% | +0.21% | +60,091 | +49,742 | WIN | WIN | 3 | 3 | 0 |
| **W10** | 2026-08-21 02:15 | 2026-08-24 02:15 | **-0.03%** | **-0.64%** | **+0.61%** | **-1,438** | **-32,185** | LOSS | **LOSS** | 1 | 3 | 0 |
| **W11** | 2026-08-24 02:15 | 2026-08-27 02:15 | -0.00% | -0.02% | +0.02% | -23 | -978 | NEUTRAL | LOSS | 2 | 3 | 0 |
| **W12** | 2026-08-27 02:15 | 2026-08-30 02:15 | -0.44% | +0.09% | -0.53% | -22,161 | +4,632 | LOSS | WIN | 2 | 1 | 0 |
| **W13** | 2026-08-30 02:15 | 2026-09-02 02:15 | -0.11% | +0.29% | -0.40% | -5,312 | +14,354 | LOSS | WIN | 1 | 1 | 0 |
| **W14** | 2026-09-02 02:15 | 2026-09-05 02:15 | +0.04% | +0.36% | -0.32% | +1,754 | +18,124 | WIN | WIN | 2 | 3 | 0 |
| **W15** | 2026-09-05 02:15 | 2026-09-08 02:15 | -0.14% | -0.14% | 0.00% | -6,754 | -6,754 | LOSS | LOSS | 1 | 1 | 0 |
| **W16** | 2026-09-08 02:15 | 2026-09-11 02:15 | -0.12% | +0.02% | -0.14% | -6,077 | +896 | LOSS | WIN | 1 | 2 | 0 |
| **W17** | 2026-09-11 02:15 | 2026-09-14 02:15 | **0.00%** | **-0.30%** | **+0.30%** | **0** | **-14,834** | **NEUTRAL** | **LOSS** | **0** | **1** | 0 |
| **W18** | 2026-09-14 02:15 | 2026-09-17 02:15 | -0.29% | -0.32% | +0.03% | -14,430 | -15,756 | LOSS | LOSS | 1 | 1 | 0 |
| **W19** | 2026-09-17 02:15 | 2026-09-20 02:15 | +0.03% | +0.39% | -0.36% | +1,518 | +19,266 | WIN | WIN | 1 | 2 | 0 |
| **W20** | 2026-09-20 02:15 | 2026-09-23 02:15 | -0.04% | +0.29% | -0.33% | -1,771 | +14,352 | LOSS | WIN | 1 | 2 | **5** |
| **W21** | 2026-09-23 02:15 | 2026-09-26 02:15 | **0.00%** | **-0.35%** | **+0.35%** | **0** | **-17,452** | **NEUTRAL** | **LOSS** | **0** | **2** | 0 |
| **W22** | 2026-09-26 02:15 | 2026-09-29 02:15 | +0.12% | +0.42% | -0.30% | +5,894 | +21,124 | WIN | WIN | 1 | 2 | 0 |
| **W23** | 2026-09-29 02:15 | 2026-10-02 02:15 | -0.16% | +0.03% | -0.19% | -8,169 | +1,385 | LOSS | WIN | 3 | 3 | 0 |
| **W24** | 2026-10-02 02:15 | 2026-10-05 02:15 | +0.30% | +0.43% | -0.13% | +15,139 | +21,452 | WIN | WIN | 1 | 2 | 0 |
| **W25** | 2026-10-05 02:15 | 2026-10-08 02:15 | **0.00%** | **-0.70%** | **+0.70%** | **0** | **-35,124** | **NEUTRAL** | **LOSS** | **0** | **2** | 0 |
| **W26** | 2026-10-08 02:15 | 2026-10-11 02:15 | **0.00%** | **-0.41%** | **+0.41%** | **0** | **-20,345** | **NEUTRAL** | **LOSS** | **0** | **2** | 0 |
| **W27** | 2026-10-11 02:15 | 2026-10-14 02:15 | **0.00%** | **-0.60%** | **+0.60%** | **0** | **-29,864** | **NEUTRAL** | **LOSS** | **0** | **2** | 0 |
| **W28** | 2026-10-14 02:15 | 2026-10-17 02:15 | -0.33% | -0.06% | -0.27% | -16,348 | -3,124 | LOSS | LOSS | 1 | 1 | 0 |
| **W29** | 2026-10-17 02:15 | 2026-10-20 02:15 | **0.00%** | **-0.46%** | **+0.46%** | **0** | **-23,154** | **NEUTRAL** | **LOSS** | **0** | **2** | 0 |

---

### 2.3. W30 incomplete window performance (final 57-hour period)
- **Time interval:** `2026-10-20 02:15:00 UTC` to `2026-10-22 11:15:00 UTC` (interval length: 57.0 calendar hours / 229 candles without missing).
- **Artificial Intelligence (AI) strategy performance:**  
  Yield: **0.06%-** | Net profit: **3,243.16 Tomans** | Number of transactions: 1 closed transaction.
- ** Deter ministic strategy performance (Det):**  
  Yield: **0.22%+** | Net profit: **10,911.60+ Tomans** | Number of transactions: 2 closed transactions.

> [!IMPORTANT]
> According to the requirements of the statement, the 57-hour window W30 is excluded from the denominator of the comparison of 29 windows due to its incompleteness and is reported separately.

---

### 2.4. Statistical comparison summary of 29 complete 72-hour windows (Cross-Strategy Summary)

| Evaluation index in 29 complete windows Artificial intelligence (AI) strategy Deter ministic strategy (Det) | Structural difference analysis
|---|:---:|:---:|---|
| **profitable windows (WIN)** | **6 windows (20.69%)** | **12 windows (41.38%)** | Deter ministic system has more winning windows due to continuous trading
| **Neutral windows (NEUTRAL)** | **11 windows (37.93%)** | **0 windows (0.00%)** | AI protected capital in 11 windows by maintaining 100% liquidity
| **Loss windows (LOSS)** | **12 windows (41.38%)** | **17 windows (58.62%)** | Deter Ministic suffered definite loss in 5 more windows
| **Total active windows with transaction** | 18 windows 29 windows Artificial intelligence remained critical 38% of the time; Deter Ministic traded 100% of the time
| **Win rate in active windows** | **33.33%** (6 of 18) | **41.38%** (12 of 29) | Win rate of traded windows
| **The most severe single-window loss** | **-22,161 Tomans (-0.44%)** | **-35,124 Tomans (-0.70%)** | Deter ministic losses are far more profound in bad windows

> [!CAUTION]
> **Comparative Audit Key Insights:**  
> Deterministic strategy was profitable in more windows (12 vs. 6), but in suffering and erosion markets (such as windows W03, W05, W06, W07, W17, W21, W25, W26, W27, W29) suffered consecutive heavy drawdowns (a total of more than 180,000 Tomans losses in these 10 windows). In contrast, the AI ​​made **exactly zero trades and maintained 100% liquidity** in all 10 windows.  
> This evidence suggests that the overall superiority of the portfolio is due to the **power to preserve capital in erosion regimes**, not the higher win rates of the windows.

---

## 3. Decimal adjustment and accounting 0.01 Toman difference resolution (Task 3 — Precision Audit)

### 3.1. Finding the root of the difference of 0.01 Tomans in the report of phase 20.2:
In the previous report, the following numbers were mentioned:
- Gross profit without slippage: 119,545.94 Tomans
- Slippage fee: 24,562.28 Tomans
- Their difference in appearance: $119,545.94 - 24,562.28 = \mathbf{94,983.66\text{ Tomans}}$
- While the reported gross operating profit: **94,983.65 Tomans** (0.01 Tomans difference).

### 3.2. Reconstruction of calculations with 64-bit standard IEEE-754 floating point:

| Accounting variable Unlimited raw value of floating point (Float) | Amount rounded to 2 decimal places To go around
|---|:---:|:---:|:---:|
| **Ideal gross profit (Zero-Slip Gross)** | `119545.93909409` | **119,545.94 Tomans** | to the top (Round Up) |
| **Executive Slippage Cost** | `24562.28485271` | **24,562.28 Tomans** | Down (Round Down) |
| **exact raw math difference** | `94983.65424138` | **94,983.65 Tomans** | Down (Round Down) |
| **Actual Modeled Gross Profit** | `94983.65424138` | **94,983.65 Tomans** | Down (Round Down) |
| **Computational remainder in floating point** | `0.00000000000000` | **0.00 Tomans** | **absolute mathematical adjustment** |

### 3.3. Decimal accuracy audit result:
1. At the level of the accounting engine and internal floating point values, the equation $\text{Gross}_{\text{zero-slip}} - \text{Slippage} \equiv \text{Gross}_{\text{modeled}}$ is established with **zero accuracy of the remaining digit (Exact Identity)** and there are no bugs or defects in the implementation.
2. The difference of 0.01 Tomans is simply caused by a common statistical phenomenon called **Independent Rounding Discrepancy**; Because the first component was rounded up (`.939 -> .94`) and the second component was rounded down (`.284 -> .28`) and as a result the difference of the circulated numbers was one hundredth more than the actual difference:
   $$(\text{Round}(A) - \text{Round}(B)) - \text{Round}(A - B) = (119,545.94 - 24,562.28) - 94,983.65 = \mathbf{+0.01\text{ TMN}}$$
3. **Accounting rule approved by the audit:** All reports must round the final Toman values after summarizing on a floating point basis so that no formal summation error occurs.

---

## 4. Complete reconstruction of net performance attribution without double counting (Task 4 — P&L Attribution)

### 4.1. Final profit and loss attribution reconciliation table:

| Financial evaluation component Artificial intelligence (AI) strategy Deter ministic strategy (Det) | The difference is in favor of artificial intelligence Role and nature in the portfolio
|---|:---:|:---:|:---:|---|
| **gross profit without slippage** | 119,545.94 Tomans 152,994.68 Tomans **33,448.74 Tomans** | Gross profit sacrificed with trade veto
| **Execution slippage fee** | 24,562.28 Tomans 40,916.43 Tomans **16,354.15+ Tomans** | Artificial intelligence slippage savings
| **Gross executive profit (Modeled Gross)** | 94,983.65 Tomans 112,078.25 Tomans **17,094.60 Tomans** | The difference of the real gross profit in the operating prices
| **paid fees of Wallex exchange** | 63,429.08 Tomans 103,925.51 Tomans **40,496.43+ Tomans** | Reducing the fee paid to the exchange
| **Total savings of friction (fee + slippage)** | — — **56,850.58+ Tomans** | Total transaction costs avoided (1.14% of capital) |
| **Final Realized Net Profit (Net P&L)** | **+31,554.57 Tomans** | **+8,152.74 Tomans** | **+23,401.83 Tomans** | Definite net advantage in Tomani account
| **return on initial capital (Return %)** | **+0.63%** | **+0.16%** | **+0.47%** | Net surplus yield of the entire 90-day period

### 4.2. Definitive proof of non-double counting of slippage:
- In the executive model, the purchase slippage is embedded in the entry price ($P_{\text{entry}} \times 1.0015$) and the sell slippage is embedded in the loss limit exit price ($P_{\text{exit}} \times 0.9985$); Therefore, gross operating profit (94,983.65 Tomans) has already reflected the slippage effect.
- Net profit is obtained directly by subtracting the exchange fee from the gross operating profit:
  $$\text{Net Realized P\&L} = \text{Modeled Gross P\&L} - \text{Total Exchange Fees}$$
  $$94,983.65\text{ TMN} - 63,429.08\text{ TMN} = \mathbf{31,554.57\text{ TMN}}$$
  $$112,078.25\text{ TMN} - 103,925.51\text{ TMN} = \mathbf{8,152.74\text{ TMN}}$$
- Net superiority relationship equation:
  $$\Delta \text{Net P\&L} = \Delta \text{Fee Savings} - \Delta \text{Gross Sacrificed}$$
  $$40,496.43\text{ TMN} - 17,094.60\text{ TMN} = \mathbf{23,401.83\text{ TMN}} \equiv \Delta \text{Net Realized P\&L}$$

---

## 5. Clarifying Dataset Integrity Terminology (Task 5 — Dataset Integrity Terminology)

In order to avoid any conceptual contradiction in the evaluation reports, the following specialized words were carefully separated:

1. **Record Validity - VERIFIED:**  
   All 8,636 rows of the dataset have full CSV structure, valid numeric columns, non-null (`isnull = False'), and positive and reasonable volumes and prices.
2. **Timestamp Ordering - VERIFIED:**  
   The time sequence of records is strictly monotonic increasing (`is_monotonic_increasing = True').
3. **Duplicate records (Duplicate Timestamps - VERIFIED):**  
   There are no duplicate rows or timestamps in the entire dataset (`duplicated = False').
4. **Expected-Grid Coverage - 99.94%:**  
   The 15-minute regular time grid contains 8,641 points over a 90-day period. The dataset contains 8,636 points (99.942% coverage).
5. **Documented Coverage Gaps - VERIFIED:**  
   There is exactly 1 time slot of 90 minutes (including 5 consecutive candles) in the dataset:  
   ``2026-09-22 12:30:00 UTC'' to ``2026-09-22 14:00:00 UTC'' (equivalent to 16:00 to 17:30 Tehran local time).  
   *Reason:* technical maintenance operation of the declared infrastructure of Wallex exchange.
6. **Gap management in simulation (Handling in Backtest):**  
   It is confirmed that no synthetic candle, forward-filled price, or liquidity assumption has been applied in the cut-off period.

> **standard phrase approved by the audit:**  
> "Datatest has fully valid and chronologically consistent records, with documented time gaps caused by technical maintenance of the exchange." (Valid observed records with documented temporal coverage gaps).

---

## 6. Regression and reproducibility tests (Reproducibility & Commands)

### 6.1. Implementation of unit and system tests:```bash
cd /root/starcoach-hack/wallex && .venv/bin/pytest tests/
```**Test output:**```
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

### 6.2. Validation of commit gate:```bash
git rev-parse HEAD
# b494d60e211497f47ef3b79d6ae79a0726471172 (full preservation of frozen commit)
```

---

## 7. Remaining obstacles and operational risks (Unresolved Blockers)

1. **Obstacle B-01 (dependency on the organizer's keys):** Failure to receive competition API access keys and destination server authentication.
2. **Obstacle B-02 (Lack of exchange loss limit):** Wallex does not support conditional orders or native stop loss on the trading core; Emergency exits are inevitably sent in the form of a software limit ticker, which carries the risk of network outages.
3. **Obstacle B-03 (API exchange rate limitation):** Risk of delay in case of sending too many orders in high volatility.
4. **Obstacle B-05 (dependency on human operator monitoring):** The need for the active presence of a human trader at the end of the 72-hour period of the competition to verify the clearing of 100% of the balance in Tomans.

---

## 8. Final verdict of phase 20.3 audit (Final Verdict)

### Technical & Numerical Integrity dimension:
> **Status: ✅ PASS / NUMERICALLY RECONCILED**  
> The duality of the capital loss percentage (1.35% compared to the peak vs. 1.36% compared to the initial capital) was clarified and proved. The complete table of 29 corresponding comparative windows of artificial intelligence and deterministics was extracted along with an incomplete window of 57 hours. The difference of 0.01 Tomans was proved as a natural effect of rounding unlimited numbers and the dataset terminology was standardized.

### After Live Execution Authorization:
> **Status: 🛑 NOT AUTHORIZED**  
> Flag [`live_execution_authorized = False`](file:///root/starcoach-hack/wallex/config/frozen_strategy_manifest_v0.6.0.json) is kept unchanged in all configurations. Until the delivery of the access to the competition and the removal of the technical obstacles on the side of the exchange, no actual order is allowed to be sent to Wallex.