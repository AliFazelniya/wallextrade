# Final report of quantitative audit, matching of historical returns and final freezing of strategy
# Phase 19 Final Quantitative Reconciliation & Strategy Freeze Audit

> **Report date:** October 22, 2026 (November 1, 1405)  
> **Software version:** `v0.10.0-phase18-audited`  
> **gate branch:** `master`  
> **Audited base commit:** `95b1c6fe7ab2164fa066de44419cb9828c41d99b`  
> **Frozen Strategy Manifest Hash:** `249c1e4af942156d2f1a602b58bd729969c660857e2d98f0158ac71c9fa75f66`  
> **Results of automated tests:** **61 successful tests out of 61 (100% pass)** with **81% code coverage**  
> **Security gate status:** Code level software gate fully blocked (`live_execution_authorized = False`)

---

## 1. Official statement of final outcome classification

According to Mr. Prompt's phase 19 audit requirements, the final status of the system is hereby officially declared:

```
╔═════════════════════════════════════════════════════════════════════════════════════════╗
║                                                                                         ║
║   Approved classification: 3. Audit slightly reproduced, pending final approval by race organizers     ║
║   Outcome: Quantitative audit reproduced, organizer confirmation pending               ║
║                                                                                         ║
╚═════════════════════════════════════════════════════════════════════════════════════════╝
```

```mermaid
flowchart TD
    A["Quantitative audit and 100% reproduction of historical results\n(adjustment of yields, spread sensitivity audit and test of 5 order paths)\nStatus: QUANTITATIVE AUDIT REPRODUCED ✅"] --> C{"The five external obstacles of the organizer\n(B-01 to B-05)"}
    B["Capital security and code level software gate\nlive_execution_authorized=False 🔒"] --> C
    C -- "Non-receipt of official calendar, keys and financial confirmation" --> D["Definitive classification of phase 19:\nQuantitative audit reproduced, organizer confirmation pending 🟡"]
    D --> E["Final step:\nOfficial submission docs/ORGANIZER_BLOCKER_REQUEST_FA.md by Human Leader\nAnd during the 8-item checklist of human permission"]
```

---

## 2. Independently Reproduced Facts

The engineering research and audit team reproduced all of the following results by independently executing the source codes, reproduction scripts, and without manipulation or fraud:

1. **Complete health and exam suite coverage:**
   - 61 unit tests and automatic integration tests were passed without errors (100% pass rate).
   - Code coverage in all `src/` modules is equivalent to **81%**.
   - Order execution module coverage ([`src/exchange/adapter.py`](file:///root/starcoach-hack/wallex/src/exchange/adapter.py)) reached **92%**.
2. ** Cryptographic Hash of the Frozen Strategy Manifesto:**
   - The file [`config/frozen_strategy_manifest_v0.6.0.json`](file:///root/starcoach-hack/wallex/config/frozen_strategy_manifest_v0.6.0.json) has a valid hash without any changes:
     `249c1e4af942156d2f1a602b58bd729969c660857e2d98f0158ac71c9fa75f66`
3. **Historical data file integrity (`data/cache/`):**
   - `BTCTMN_15m_90d.csv` (8,636 candles): `54292673b433a9a95e19ebab0dc446fdfc1458c9b8e4ea5672a6b5ad51775a9e`
   - `ETHTMN_15m_90d.csv` (8,637 candles): `106970901976cf4015a1de237486ea79f3daa93d8b321b697d6f74d8b41df0d9`
   - `SOLTMN_15m_90d.csv` (8,636 candles): `27a82f586859eb92a608abf1db9c8cdceef2fe4f29e1570e8d77de5618702f0a`
4. **Reproducing the results of phase 13 accurately to the hundredth percent:**
   - AI strategy in 45-day in-sample period (IS): net return **-0.04% (loss 1,800 Tomans), 15 trades, 43,309 Tomans fee.
   - AI strategy in 45-day out-of-sample period (OOS): net return **0.62%+** (profit 31,000 Tomans), 9 trades, 25,874 Tomans fees.
   - AI strategy in the full period of 90 continuous days: net return **0.43%+** (profit 21,515 Tomans), 24 trades (12 wins, 12 losses), 69,162 Tomans fees.
5. **Independent verification of 5 order paths:**
   - The definite separation of maker (0.25%) in passive limits, and ticker (0.30%) in aggressive limits, market orders, loss limit and emergency cashing was confirmed in Tomans.

---

## 3. Results inherited from previous reports (Inherited Results)

To understand the historical development path, the following results were extracted and structured from the previous phases:
- **Phase 12:** Separation of single symbol efficiency and common portfolio; Proving that portfolio losses were caused by strong friction and high spreads of Ethereum and Solana, and focusing on the single token ``BTCTMN'' saved capital.
- **Phase 14:** Auditing the difference of 7,032 Tomans between IS and OOS period; Proving that early liquidation of the open position at the border of the period (Candle 4,318) caused a loss of 5,185 Tomans, while the continuation of the position in the continuous run led to a loss of 2% (12,217 Tomans loss).
- **Phase 15:** Comprehensive tests of operational failures (14 crisis scenarios) and successful test maneuver in the shadow on Wallex live data.
- **Phase 16:** The official registry of race obstacles (B-01 to B-05) and the implementation of an incremental data pipeline without network delay.
- **Phase 17 and 18:** Setting up the official draft of the competition barriers query ([`docs/ORGANIZER_BLOCKER_REQUEST_FA.md`](file:///root/starcoach-hack/wallex/docs/ORGANIZER_BLOCKER_REQUEST_FA.md)) and modeling the implementation costs.

---

## 4. Simulation Assumptions

1. **Wallex basic fee:** Level 1 Toman (0.25% Maker and 0.30% Taker).
2. **Unfavorable slippage 0.15%:** Increase of 15 pips from the reference price (Mid/Close) in buying and decrease of 15 pips in selling to cover the crossing of the half-spread and penetrating the depth of the book.
3. **Initial capital:** 5,000,000 Tomans initial cash.
4. **Order ceiling:** 500,000 Tomans (10% of the total capital).
5. **Minimum transaction value:** 50,000 Tomans according to Wallex technical standards.
6. **Spread contract:** $\frac{Ask - Bid}{Bid} \times 100$.

---

## 5. Autopsy and mathematical matching of historical yield discrepancies (Task 2)

The following table shows a complete reconciliation and detailed dissection of the difference between the reported yields in phases 13, 14, 18 and 19:

| Row number Description of configuration and scenario Time horizon Type of strategy Spread model Number of transactions Winning Trades (TP) | Losing Trades (SL) | Fee paid (tomans) | Net yield (%) | The reason for the difference and the structural root
|---|---|---|---|---|---|---|---|---|---|---|
| **1** Phase 13 - In-sample (IS) | The first 45 days With artificial intelligence (AI) | Fixed 0.05% 15 | 7 | 7 (+1 settlement) | 43,309 | **-0.04%** | The suffering and downward market of the first phase, mandatory review of the border transaction
| **2** Phase 13 - Out-of-sample (OOS) | 45 second day With artificial intelligence (AI) | Fixed 0.05% 9 | 5 | 3 (+1 transaction) | 25,874 | **+0.62%** | Fall 2026 fast rising market
| **3** Phase 13 - continuous for 90 days Total 90 days With artificial intelligence (AI) | Fixed 0.05% 24 | 12 | 12 | 69,162 | **+0.43%** | Continuous combination of IS and OOS without border stop |
| **4** Phase 13 - Deter ministic without AI Total 90 days No AI (pure technical) | Fixed 0.05% 39 | 18 | 21 | 112,612 | **-0.42%** | Surplus and loss transactions in suffering markets
| **5** Phase 18 - Deter ministic (Gate 0.20%) | Total 90 days No AI (pure technical) | Valax dynamic variable 36 | 17 | 18 | 103,926 | **+0.16%** | Filtering 3 trades with wide spread by gate 0.20% |
| **6** Phase 19 - AI Strategy (Gate 0.20%) | Total 90 days With artificial intelligence (AI) | Valax dynamic variable 22 | 11 | 10 (+1 review) | 63,429 | **+0.63%** | **Synergy of artificial intelligence + 0.20% dynamic spread filter** |

### 5.1. Discovering the root of the difference in efficiency of phase 18 (+0.16%) against phase 13 (+0.43%):
- In phase 18, the simulation script was run to evaluate the gate spread conservatively on **technical strategy without artificial intelligence**. In phase 13, the strategy without artificial intelligence had a yield of **-0.42%; But applying a gate spread of 0.20% in phase 18 by removing 3 trades in wide spreads improved the return to **0.16%+**.
- When the gate spread of 0.20% was applied to **main strategy equipped with artificial intelligence** (row 6), the number of trades decreased to 22, 2 low-quality trades were filtered, the fee dropped from 69 thousand to 63 thousand tomans, and the net return reached **0.63%+**.

### 5.2. Why did the 0.18% cap give +0.46% yield but the 0.20% cap gave +0.16% yield?
- By candle-by-candle inspection, it was found that in Deter Ministic strategy, by changing the ceiling from 0.18% to 0.20%, exactly **one excess transaction** (transaction number 36) entered the basket, the spread of which was between 0.18% and 0.19%.
- This transaction hit the loss limit and caused a net loss of exactly **12,963 Tomans**. The loss of this single transaction on a capital of 5 million tomans is exactly equal to **0.26% - efficiency loss** and reduced the gross profit from 124 thousand to 112 thousand tomans.

---

## 6. Gate spread sensitivity audit and multi-criteria selection criteria (Task 4)

The comprehensive table for evaluating the sensitivity of the spread ceiling in the 90-day horizon:

```
───────────────────────────────────────────────────────────────────────────────────────────────────
Cap Spread Signals Veto Signal Trades Gross Profit Fees Slippage Net Return Max Drawdown (DD)  3-day windows
(Threshold)  (Candidates) (Vetoes)    (Trades)     (TMN)        (TMN)      (TMN)       (Net %)         (Max DD)     (Win / BE / Loss)
───────────────────────────────────────────────────────────────────────────────────────────────────
[Strategy equipped with artificial intelligence - AI Assisted]:
  0.15%          670         152         18       +85,908      51,921     20,108      +0.68%          1.16%         10 / 8 / 11
  0.18%          670          66         22       +92,944      63,423     24,559      +0.59%          1.28%          9 / 7 / 13
  0.20% [Freeze]   670          35         22       +94,984      63,429     24,562      +0.63%          1.35%         10 / 7 / 12
  0.25%          670          14         22       +94,984      63,429     24,562      +0.63%          1.35%         10 / 7 / 12
  0.35%          670           0         24      +100,022      69,185     26,791      +0.62%          1.28%         10 / 7 / 12

[Deterministic strategy without artificial intelligence - No-AI Baseline]:
  0.15%          670         152         34      +137,897      98,001     37,950      +0.80%          1.49%         12 / 0 / 17
  0.18%          670          66         35      +124,131     100,963     39,439      +0.46%          1.49%         12 / 0 / 17
  0.20% [Freeze]   670          35         36      +112,078     103,926     40,916      +0.16%          1.80%         12 / 0 / 17
  0.25%          670          14         37      +100,756     106,892     42,399      -0.12%          1.80%         12 / 0 / 17
  0.35%          670           0         39      +105,798     112,647     44,628      -0.14%          1.80%         12 / 0 / 17
───────────────────────────────────────────────────────────────────────────────────────────────────
```

### 6.1. Why is the 0.20% ceiling maintained as a frozen baseline?
1. **Avoid retrospective manipulation (No Data-Snooping Bias):**  
   If, based on the results of this tested data, the ceiling is changed to 0.15% or 0.18%, the parameter is overfitting; Because there is no third independent intact dataset to revalidate.
2. Compliance with the Multi-Objective Criterion Framework:  
   - The ceiling of 0.15% has a very high veto rate (22.7% veto) and may prevent entry into powerful bullish opportunities during the periodic fluctuations of the match day.
   - The ceiling of 0.20% is exactly the optimal balance between the elimination of abnormal spreads and entry into optimal liquidity, and keeps the returns of both artificial intelligence (+0.63%) and Deterministic (+0.16%) strategies positive.
3. **Final audit decision:**  
   The ceiling of **0.20%** remains frozen in the strategy manifesto and the values of 0.15% and 0.18% are recorded as **Exploratory Thresholds** in the documents.

---

## 7. Explicit statement of statistical and methodological limitations (Statistical Limitations)

The research team announces the following for maximum transparency:
1. **Sample number of 3-day windows:** In 90 days, there are only 29 independent 3-day windows, which in terms of statistics is a small sample size (Small Sample Size) to claim certainty with a 99% confidence interval.
2. **Heavy dependence on the competitive market regime:** In a calm and neutral 3-day period, the algorithm may remain in the ``CALM_RANGE'' mode and register zero trades (0.0% return) to avoid the sting of fees.
3. **Lack of L2 historical depth:** Simulations are based on OHLCV candles and run with conservative slippage assumptions. Performance in the actual market may be affected by fluctuations in book value order depth.

---

## 8. Recommended Frozen Configuration

| System component Approved parameter | Reference file Audit status
|---|---|---|---|
| **Target trading symbol** | ``BTCTMN'' | [`frozen_strategy_manifest_v0.6.0.json`](file:///root/starcoach-hack/wallex/config/frozen_strategy_manifest_v0.6.0.json) | ✅ Frozen |
| **Data Timeframe** | 15 minutes (`15`) | [`fetcher.py`](file:///root/starcoach-hack/wallex/src/data/fetcher.py) | ✅ Frozen |
| **Take Profit** | 3.5% (`take_profit_pct=3.5`) | [`regime_momentum.py`](file:///root/starcoach-hack/wallex/src/strategy/regime_momentum.py#L28) | ✅ Frozen |
| **Loss Limit (Stop Loss)** | 2.0% (`stop_loss_pct=2.0`) | [`regime_momentum.py`](file:///root/starcoach-hack/wallex/src/strategy/regime_momentum.py#L27) | ✅ Frozen |
| **allowed spread ceiling** | 0.20% (`max_spread_pct=0.20`) | [`frozen_strategy_manifest_v0.6.0.json`](file:///root/starcoach-hack/wallex/config/frozen_strategy_manifest_v0.6.0.json#L14) | ✅ Frozen |
| **Tomani order ceiling** | 500,000 Tomans [`engine.py`](file:///root/starcoach-hack/wallex/src/risk/engine.py#L43) | ✅ Frozen |
| **Emergency drawdown ceiling** | 5.0% [`engine.py`](file:///root/starcoach-hack/wallex/src/risk/engine.py#L45) | ✅ Frozen |
| **Compulsory settlement in Tomans** | 100% balance 30 minutes before the end [`accounting.py`](file:///root/starcoach-hack/wallex/src/portfolio/accounting.py#L205) | ✅ Frozen |
| **Live transaction software gate** | `live_execution_authorized = False` | [`adapter.py`](file:///root/starcoach-hack/wallex/src/exchange/adapter.py#L142) | 🔒 active software lock

---

## 9. The final steps before the start of the competition

1. The human operator sends the official request text [`docs/ORGANIZER_BLOCKER_REQUEST_FA.md`](file:///root/starcoach-hack/wallex/docs/ORGANIZER_BLOCKER_REQUEST_FA.md) to Wallex and Starcoach support.
2. As soon as the time and special keys of the race account are delivered, the final human authorization checklist in [`docs/PHASE18_FINAL_AUTHORIZATION_GATE.md`](file:///root/starcoach-hack/wallex/docs/PHASE18_FINAL_AUTHORIZATION_GATE.md) is passed, and after performing the read-only test of the account balance, the live connection license is issued by the user.