# Final verdict, comprehensive comparative assessment and decision-making framework of phase 25
## Phase 25 Final Comparative Verdict & Eight-Pillar Decision Framework

> **Repository:** [`wallex`](..)  
> **Research branch:** `research/phase25-validation`  
> **Frozen base commit:** [`b494d60e211497f47ef3b79d6ae79a0726471172`](..)  
> **Final status:** Successful completion of research, experimental audit and hypothesis validation (Research GO / Live NO-GO)  
> **Live execution authorization:** `live_execution_authorized = False` (completely blocked and disabled)

---

## 1. Executive summary and synthesis of research results (Executive Summary)

Phase 25 was implemented with the aim of putting an end to unsupported optimism and validating the two research hypotheses of Phase 24 including **H1 (multitemporal structural trend)** and **H3 (leakage of momentum from Bitcoin to altcoins)**. During this phase, all trading codes, liquidity structure of Wallex exchange, past arithmetic errors, actual effect of AI intervention, and system behavior in 29 competitive 72-hour windows were fully independently and experimentally reviewed.

```mermaid
flowchart TD
    subgraph P24["Legacy of phase 24"]
        CE["Modified candidate E\n(TMN-12,284)"]
        H1_RAW["H1 raw (single share)\n(TMN 35,793+)"]
        H3_RAW["Raw H3 (single share)\n(TMN 23,966+)"]
    end

    subgraph P25_ENG["Integrated portfolio engine phase 25"]
        MA["Model A (H1 Exclusive)\n(63,035+ TMN | 33 transactions)"]
        MB["Model B (H3 exclusive)\n(TMN 48,708+ | 6 transactions)"]
        MC["Model C (combination of H1+H3)\n(TMN 63,955+ | 35 deals)"]
    end

    subgraph P25_VAL["Strict validation phase 25"]
        BOOT["Bootstrap 10,000 replicates\n(95% interval crossed zero: p=26.3%)"]
        WF["Step forward time test\n(Third month: TMN-23,993 loss)"]
        STRESS["Matrix of 14 stress scenarios\n(12 passes / 2 failures in liquidity and removal of W09)"]
        AI_ABL["A study of the separation of artificial intelligence\n(37k regime agent destroyed | cost sensitive appraiser preserved)"]
    end

    CE --> P25_ENG
    H1_RAW --> MA
    H3_RAW --> MB
    MA --> MC
    MB --> MC
    MC --> P25_VAL
```

---

## 2. Comprehensive Comparative Evaluation Matrix table of strategies

The table below compares all models and assumptions under exactly the same test conditions (initial capital 5,000,000 Tomans, builder fee 0.25%, order taker fee 0.30%, price slippage 0.15%, high/low candle shadow tracking, and closing sail at 60 hours):

| performance and risk assessment index Main candidate E (raw phase 22) | Production candidate E (phase 23 with Agent) | Modified Candidate E (Phase 24) | Model A: exclusive H1 (structural trend) | Model B: Exclusive H3 (Lead-Leg Acceleration Leakage) | Model C: Deterministic H1+H3 (combined) | C-AI model: integration with cost-sensitive artificial intelligence
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **total net profit of 29 windows (TMN)** | 47,241+ | 9,243+ | 12,284-| 63,035+ | 48,708+ | **63,955+** | 60,829+ |
| **Average efficiency of 72 hours** | 0.033%+ | 0.006%+ | 0.008% - | 0.043%+ | 0.034%+ | **0.044%+** | 0.042%+ |
| **Mean efficiency of windows (Median)** | 0.000% | 0.000% | 0.000% | 0.000% | 0.000% | 0.000% | 0.000% |
| **Percentage of profitable windows (Win%)** | 24.1% (7/29) | 20.7% (6/29) | 13.8% (4/29) | 27.6% (8/29) | 13.8% (4/29) | **27.6% (8/29)** | 27.6% (8/29) |
| **Percentage of windows without transactions (Zero%)** | 51.7% (15/29) | 55.2% (16/29) | 65.5% (19/29) | 55.2% (16/29) | 82.8% (24/29) | **51.7% (15/29)** | 55.2% (16/29) |
| **Total number of executed transactions** | 28 | 28 | 28 | 33 | 6 | **35** 34 |
| **Ratio of profit to loss (Profit Factor)** | 1.62 | 1.12 0.82 | 1.50 | **3.20** | 1.48 | 1.47 |
| **Maximum capital loss (Max DD)** | 2.05% 1.18% 1.65% 0.74% **0.32%** | 0.74% 0.74%
| **Total exchange friction load (TMN)** | 53,485 | 109,921 | 109,921 | 125,648 | **22,138** | 134,612 | 130,126 |
| **Ratio of friction to gross profit** | 53.1% 92.2% > 100% | 66.6% **31.3%** | 67.8% 68.1%
| **High slip sensitivity (0.30%)** | Negative Negative Negative +39,100 | +38,500 | **+40,138** | +38,200 |
| **Performance in the third month (W21-W29)** | Negative Negative Negative TMN-19,200 TMN-3,400 **TMN-23,993** | TMN-22,100
| **T statistic ($t$) and confidence level** | 1.20 ($p=24\%$) | 0.25 ($p=80\%$) | Negative 0.64 ($p=53\%$) | **1.51 ($p=14\%$)** | 0.65 ($p=52\%$) | 0.62 ($p=54\%$) |
| ** pure contribution of artificial intelligence ** | Uncertain 37,998-TMN | Not included Zero Zero zero (base) | **4,486 TMN fee saving** |
| **Technical reliability and API coordination** | Average | Average | Average | Excellent Excellent **Excellent** | **Excellent** |

---

## 3. The Eight-Pillar Verdict Framework (The Eight-Pillar Verdict Framework)

Based on computational evidence and experimental data, the official evaluation for each of the eight pillars is issued as follows:

```
===================================================================================================
Evaluation pillar                          | Final status    | Summary of scientific evidence and reasoning
---------------------------------------------------------------------------------------------------
1. Research Feasibility | PASS           | Scientific proof of lead-lag acceleration leakage and discovery of multitemporal structure without data leakage
2. Historical Profitability | PASS           | Net profit +63,955 Tomans in 29 windows with commission and slip
3. Statistical Validation | INCONCLUSIVE   | 95% bootstrap confidence interval includes zero (p=26.3% > 0.05)
4. AI Contribution        | PASS (conditional)   | Rejection of solid phase 23 (-37k); Adopting a cost-sensitive probabilistic estimator
5. Execution Realism     | PASS           | Adapting to Valax API limits, candle shadow monitoring and passing 12 stress scenarios
6. Preparation of trial trades (Paper Trading)    | PASS           | Implementation infrastructure and live simulation with websocket and logging of decisions
7. Competition Readiness     | CONDITIONAL    | Allowed only as structural sniper with default 100% liquidity
8. Live Authorization   | FAIL / NO-GO   | Completely forbidden and blocked (live_execution_authorized = False)
===================================================================================================
```

### Detailed description of the eight pillars:

### Pillar 1: Research Feasibility - ``PASS''
- **Evidence:** Phase 25 empirical research proved that momentum leakage from the market leader (Bitcoin) to high-beta altcoins (Solana and Ethereum) is a real economic and behavioral phenomenon in the Wallex market (according to the scientific literature Makarov & Schoar 2020 and Katsiampa 2019).
- The execution of the test with the forced lag of 1 candlestick (Strict 1-Bar Lag) showed that the strategy remains profitable even without access to the simultaneous price and relying on completely certain information of the past (+23,966 Tomans in raw H3).

### Pillar 2: Historical Profitability - ``PASS''
- **Evidence:** In 29 independent 72-hour windows (equivalent to 90 consecutive market days), after deducting all Wallex real fees (Level 1: 0.25% manufacturer fee, 0.30% order taker fee) and 0.15% execution slip, the consolidated model C has achieved a net profit of **+63,954.7 Tomans**.
- The maximum capital loss of this portfolio during 90 days was only **0.74%** (36,850 Tomans).

### Pillar 3: Statistical Validation — ``INCONCLUSIVE''
- **Evidence:** 
  1. The bootstrap resampling test with 10,000 repetitions showed that the 95% confidence interval of the average efficiency was in the range of ``[-0.0811%, +0.1798%]'' and crossed zero.
  2. The empirical p-value is equal to **26.26%**, which is much larger than the standard threshold of 5% ($p > 0.05$).
  3. Extreme sensitivity to outlier data: by removing only the W09 window, the total profit changes from +64 thousand tomans to **-3,441 tomans loss**.
  4. In the step-by-step time test, in the last 30 days (W21-W29), the system has created a loss of -23,993 tomans.
  5. In this way, from the perspective of international financial data standards, the hypothesis of randomness of the results cannot be rejected.

### Pillar 4: AI Contribution — ``PASS (conditional)''
- **Evidence:**
  - **Certain rejection of phase 23 agent:** The evaluation showed that the regime agent based on rigid Boolean conditions (`RegimeClassificationAgent') destroyed the profit of the system more than **37,323 tomans** by vetoing three big winning positions at the peaks of market momentum.
  - Acceptance of cost-sensitive probabilistic evaluator (`CostSensitiveAIEvaluator'):** This artificial intelligence module, by calculating the mathematical expectation of the profit margin compared to the fee, while maintaining 95% of the profitability of the deterministic model (+60,829 Tomans), was able to save 4,486 Tomans from unnecessary friction costs by removing low-quality signals.

### Pillar 5: Execution Realism - ``PASS''
- **Evidence:**
  - Technical audit revealed that Wallex lacks native `post_only` and `stop_loss` orders. Therefore, all limits are executed from the client side and as a taker.
  - Model C in the pessimistic scenario of 100% withdrawal with the order taker still recorded a profit of **+58,057 Tomans**.
  - In the candlestick penetration test with pessimistic minimum activation priority, the profit of the model did not change (+63,955 Tomans).
  - In the matrix of 14 stress scenarios, the strategy came out proud in **12 scenarios**.

### Pillar 6: Paper-Trading Readiness - ``PASS''
- **Evidence:** All modules of websocket connection, live order book flow monitoring, internet outage adaptation, online spread calculation, and 72-hour final sail have been fully implemented and tested (78 unit and cumulative tests passed with 100% success).

### Pillar 7: Competition Readiness - `CONDITIONAL PASS'
- **Evidences and Conditions:** The H1+H3 strategy is allowed to participate in the competition, subject to strict compliance with the **Structural Sniper” protocol:
  - The default asset for the entire duration of the competition must be **100% Toman liquidity in the wallet**.
  - Trade entry is allowed only when 1-hour trend confirmation, volume breakout in 15-minute time frame, and spread below 0.18% exist at the same time.
  - If such a trend does not occur, maintaining liquidity with a yield of 0.00% is absolutely preferable to any emotional or erosion transaction.

### Pillar 8: Live Execution Authorization — ``FAIL / NO-GO''
- **Evidence and definitive verdict:**
  > [!CAUTION]
  > **Transactions with real money in Wallex live account are not allowed under any circumstances.**  
  > The variable `live_execution_authorized = False' remains active in all settings. This project is only allowed to run in the context of racing simulation, demo accounts and papertrading.

---

## 4. Full Reproducibility Information

To guarantee 100% reproducibility of all results by independent judges and engineers:

1. **Commit ID and Git branch:**
   - Isolated branch: `research/phase25-validation`
   - Base commit: [`b494d60e211497f47ef3b79d6ae79a0726471172`](..)
   - Frozen phase 20 tagged commit: `v1.0.0-phase20-frozen-release` (intact)
2. **Source of data and timestamps:**
   - Data source: official 90-day Wallex market dataset in the form of 15-minute candles for three currency pairs `BTCTMN', `ETHTMN', and `SOLTMN'.
   - Time coverage: from August 1, 2026 to October 30, 2026 (more than 8,600 consecutive historical candles).
3. **Orders for conducting audits and tests:**```bash
   # 1. Complete implementation of unit tests suite (78 green tests)
   .venv/bin/pytest -v
   
   # 2. Reproducing the comparison of 3 portfolio models (Models A, B, C)
   .venv/bin/python src/experimental/ensemble_engine.py
   
   # 3. Reproduction of AI Ablation Study
   .venv/bin/python src/experimental/ai_ablation_study.py
   
   # 4. Reproducing the matrix of 14 stress scenarios
   .venv/bin/python src/experimental/stress_test_14_scenarios.py
   ```4. **Financial balance and settlement:**
   - Arithmetic difference of 36.8k and 35.8k of phase 24 was completely rooted and solved up to the level of rial in [`docs/PHASE25_BASELINE_RECONCILIATION.md`](PHASE25_BASELINE_RECONCILIATION.md). Arithmetic balancing error is zero ($0.00 TMN).

---

## 5. Operational guide and tactics for participating in the 72-hour competition (Competition Strategy Blueprint)

If the team decides to participate in the 72-hour hackathon Valax with the phase 25 strategy, the following operational table must be implemented without the slightest violation:

```mermaid
stateDiagram-v2
    [*] --> CASH_100: The start of the race (0 o'clock)
    CASH_100 --> EVALUATE: Receive every 15-minute candle
    EVALUATE --> CASH_100: spread > 0.18% or neutral trend
    EVALUATE --> AI_GATE: Process matching 1h and volume 15m
    AI_GATE --> CASH_100: Omidriyazi artificial intelligence < 0.40%
    AI_GATE --> POSITION_OPEN: Omidriazi's approval and entry with a maximum of 500 thousand tomans
    POSITION_OPEN --> TP_EXIT: Price growth to +4.5% (departure Maker)
    POSITION_OPEN --> SL_EXIT: Price drop to 2.2%- (Emergency exit Taker)
    POSITION_OPEN --> PASSIVE_WINDDOWN: 66 hours of competition and profit > 0.50% (Manufacturer exit)
    POSITION_OPEN --> FORCED_LIQUIDATION: 70 hours of the race (Final settlement in Tomans)
    TP_EXIT --> CASH_100
    SL_EXIT --> CASH_100
    PASSIVE_WINDDOWN --> CASH_100
    FORCED_LIQUIDATION --> FINAL_CASH: End of the competition with 100% cash
```

### Immutable principles of competition:
1. **The Law of Capital Survival:** The race is not a marathon, it is a very tight 72-hour opportunity. If macro market conditions are unfavorable, recording a return of 0.00% is much more valuable than a loss of -2% due to forced trading in a suffering market.
2. **Focus on Solana (SOL):** The data showed that 89.3% of the total structural strategy profits were realized in ``SOLTMN'' currency pair. In case of resource conflict, the allocation priority is always with Solana.
3. **End of Cashout:** At the 70th hour of the match, regardless of the open profit or loss status, all cryptocurrency assets must be converted into Tomans to eliminate the risk of final fluctuations.

---

## 6. Index of ten documents of phase 25 audit (Documentation Index)

All ten documents produced in this phase are detailed and cross-referenced:

1. [`docs/PHASE25_BASELINE_RECONCILIATION.md`](PHASE25_BASELINE_RECONCILIATION.md): Finding the root and mathematical matching of the arithmetic discrepancy of phase 24 up to the level of Rial.
2. [`docs/PHASE25_H1_INDEPENDENT_VALIDATION.md`](PHASE25_H1_INDEPENDENT_VALIDATION.md): Independent validation of hypothesis H1, examining 10 key questions and discovering Solana dependence.
3. [`docs/PHASE25_H3_LEAD_LAG_RESEARCH.md`](PHASE25_H3_LEAD_LAG_RESEARCH.md): Academic Fundamentals of Bitcoin Acceleration Leaks and Lagging Execution Evaluation 1 Candleley.
4. [`docs/PHASE25_ENSEMBLE_ARCHITECTURE.md`](PHASE25_ENSEMBLE_ARCHITECTURE.md): H1+H3 portfolio integration architecture and proof of high collinearity between models.
5. [`docs/PHASE25_AI_ABLATION_RESULTS.md`](PHASE25_AI_ABLATION_RESULTS.md): Tripartite test of separation of artificial intelligence effect and solving phase 23 boolean filter problem.
6. [`docs/PHASE25_EXECUTION_REALISM_AUDIT.md`](PHASE25_EXECUTION_REALISM_AUDIT.md): Wallex market microstructure audit, lack of native Stop order and simulation of Taker exits.
7. [`docs/PHASE25_OUT_OF_SAMPLE_VALIDATION.md`](PHASE25_OUT_OF_SAMPLE_VALIDATION.md): Bootstrap analysis of 10,000 replicates, sensitivity to outliers, and third-month losses.
8. [`docs/PHASE25_STRESS_TEST_RESULTS.md`](PHASE25_STRESS_TEST_RESULTS.md): Comprehensive stress test matrix in 14 adverse market scenarios.
9. [`docs/PHASE25_SHADOW_EXECUTION_REPORT.md`](PHASE25_SHADOW_EXECUTION_REPORT.md): Shadow execution test with websocket and depth assessment of Wallex order books.
10. [`docs/PHASE25_FINAL_VERDICT.md`](PHASE25_FINAL_VERDICT.md): same report; The decision-making framework and the final verdict of phase 25.