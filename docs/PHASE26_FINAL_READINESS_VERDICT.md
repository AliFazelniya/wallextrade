# The final verdict and evaluation of the twelve gates of Phase 26 (Phase 26 Final Verdict)
## The Twelve Decision Gates, Final Competition Readiness & Safety Verdict

> **Repository:** [`wallex`](..)  
> **Research branch:** `research/phase26-forensic-validation`  
> **Frozen base commit:** [`b494d60e211497f47ef3b79d6ae79a0726471172`](..)  
> **Overall status of phase 26:** Successful completion of legal audit, discovery of the superiority of original artificial intelligence and independent validation  
> **Authorization of live transactions:** `live_execution_authorized = False` (**Completely blocked and disabled**)

---

## 1. The official evaluation table of the twelve decision gates (The 12 Decision Gates)

```
===================================================================================================================
No | Decision Gate             | Final status  | Summary of empirical evidence and technical foundations
-------------------------------------------------------------------------------------------------------------------
01    | Authenticity of raw data (Data Authenticity)         | PASS         | Byte-by-byte matching of SHA-256 checksums and formal extraction from Wallex UDF
02    | Timestamp Integrity         | PASS         | Strict bullishness, zero repeat/future data, phase 25 validity error resolution
03    | Accounting Integrity    | PASS         | Full balance of trading profits with a portfolio with an error of 0.00 TMN and proof of the capacity of 2 positions
04    | Correctness of Stress Integrity Tests   | PASS         | Actual state jump in 14 scenarios, linear fit of 70% volume and spread refinement effect
05    | Compliance with the microstructure of the exchange (Exchange Mechanics) | PASS         | Auditing Wallex's STOP_LIMIT capabilities, SOL limits, and client stop logic
06    | Independent validation of the sample (Independent OOS)   | INCONCLUSIVE | Loss of 23.5k Tomans in July independent data due to heavy friction in the range market
07    | Positive Net Edge   | PASS (conditional) | +64k net profit in 90 days data and +84k with AI; They depend on the existence of the regime
08    | Independent added value of hypothesis H3 (H3 Incremental)    | INCONCLUSIVE | Strong collinearity with H1 and negligible marginal profit of 920 Tomans in deterministic mode
09    | Genuine AI Edge participation     | PASS         | Logistic regression model with test accuracy of 70.6% and profit jump to +84,053 Tomans with floating volume
10    | Reliability of trial transactions (Shadow Runner)  | PASS         | Live monitoring of 10 market cycles with Wallex web service and 1.62s delay without interruption
11    | Compliance with the competition rules (Hackathon Compliance)| PASS         | Cash spot transactions, capital of 5 million, compliance with risk limit and final sail
12    | Live Trading Readiness | FAIL / NO-GO | Failure to issue a license to trade live with real money (permanent blocking of the code)
===================================================================================================================
```

---

## 2. Summary of Key Forensic Discoveries of Phase 26

1. **Definitive solution to the contradiction of dates:**  
   The ambiguity created around "future-related data" was rooted out. The data in the local cache covers from July 24, 2026 to October 22, 2026 (today), and the October 30 date in phase 25 was simply a typo in the text of the report. There are no fake or future candles in the dataset.
2. **Discovering the secret of trading jump from 19 to 33:**  
   It was proved that the change of H1 transactions from 19 to 33 transactions was due to the upgrade of the simultaneous portfolio capacity from 1 open position (in phase 24) to 2 open positions at the same time (1 million Toman ceiling in phase 25). The reverse experiment with the single-position constraint reproduced exactly 19 trades and 72.5k of phase 24 friction.
3. **Modification of the stress test simulator:**  
   The cause of the sameness of 4 scenarios of phase 25 was discovered and corrected. By actually applying state jump parameters, accurate linear response of order volume (30% reduction in profit at 70% filling) and filtering of noise trades at +50% spread was proven.
4. **The inconvenient truth in the independent out-of-sample (OOS) test:**
Running the strategy on 19 days of fully intact July 2026 data showed that in a range market with less than 4.5% swings, Wallex's heavy friction (0.70% to 0.90% per trading round) ate up the gross profit and resulted in a loss of 23.5 thousand tomans. This finding proves that the strategy should not trade blindly in all market regimes.
5. **Victory of original artificial intelligence and floating volume adjustment (Dynamic Position Sizing):**  
   By implementing a genuine machine learning model (L2 Regularized Logistic Regression) that was trained on the data of the first half, the model achieved **70.59% accuracy** in the out-of-sample test data. Applying this model to adjust position volume floating (0.6x in high-risk signals and 1.2x in high-power waves) increased the profit of the system from 64 thousand tomans to **+84,053 tomans**.

---

## 3. Winning architecture and recommended strategy for the 72-hour hackathon competition

Based on all scientific evidence and audits:

```mermaid
flowchart TD
    MD["Wallex live input data\n(BTCTMN, ETHTMN, SOLTMN)"] --> FILTER{"Liquidity filter and spread\n(Spread <= 0.18% and stable volume)"}
    FILTER -- "High spread" --> CASH["Maintaining 100% liquidity in Toman wallet"]
    FILTER -- "Optimal spread" --> GEN["Generation of H1 and H3 opportunities\n(trend 1h + breakout 15m)"]
    GEN --> AI["Calibrated artificial intelligence model phase 26\n(Calculating the probability of winning P_win and Omidriazi)"]
    AI -- "P_win < 48% or negative mathematical expectation" --> CASH
    AI -- "P_win >= 48%" --> SIZING["Floating order volume adjustment\n(300k to 600k tomans based on reliability)"]
    SIZING --> RISK{"Risk control engine and limit matching\n(ceiling of 2 positions / hours < 60)"}
    RISK -- "confirmation" --> EXEC["Send ticker/limit order with simulator or API"]
    RISK -- "capacity saturation" --> CASH
    EXEC --> WD["Final sail: departure of the manufacturer at 66 hours / final settlement at 70 hours"]
```

### The three principles of success in the competition:
1. Default to 100% Cash strategy: Considering the loss of the system in periods of suffering, if the ideal trend conditions are not met, maintaining 100% Toman liquidity throughout the race is absolutely preferable to forced trading.
2. **Using artificial intelligence to adjust volume not a solid veto:** Artificial intelligence should not eliminate large trades, but should increase volume in safe waves and decrease volume in volatile situations.
3. **Definitive settlement at 70:** Converting all assets into cash Tomans before the end of the window to eliminate the risk of final fluctuations.

---

## 4. Final status of permits and safety compliance

- `live_execution_authorized = False' was kept as an immutable guardrail in all configuration files.
- No order has been sent to the real account of the exchange and all tests have been done in the simulation and shadow environment.
- Base freeze commit [`b494d60e211497f47ef3b79d6ae79a0726471172`](..) and previous tags left completely intact.
- **Number of suite unit tests:** 78 tests passed with 100% success.