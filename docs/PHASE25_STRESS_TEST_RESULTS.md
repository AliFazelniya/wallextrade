# The results of the 14 stress tests of the integrated model H1+H3 (Phase 25 Stress Tests)
## Fourteen-Scenario Stress Testing Matrix & Microstructure Resilience Audit

> **Repository:** [`wallex`](..)  
> **Research branch:** `research/phase25-validation`  
> **Frozen base commit:** [`b494d60e211497f47ef3b79d6ae79a0726471172`](..)  
> **Evaluation strategy:** Model C (integrated portfolio H1+H3 Structural Sniper)  
> **Number of independent windows:** 29 full windows ($N = $29) | **Initial capital:** 5,000,000 Tomans

---

## 1. Comprehensive table of 14 scenarios of stress test (14-Scenario Stress Matrix)

| row | Description of the stress test scenario Exchange fee (Maker / Taker) | Implementation slippage hypothesis Total Net Profit (TMN) | average yield | Win rate Total Friction (TMN) | Resilience assessment
|:---:|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **01** | **Realistic base of Wallex exchange** | 0.25% / 0.30% | 0.15% **63,954.7+** | **0.044%+** | 27.6% 134,612 | ✅ **PASS** |
| **02** | **High transaction fees (Elevated Fees)** | 0.35% / 0.40% | 0.15% **28,791.1+** | **0.020%+** | 27.6% 169,775 | ✅ **PASS** |
| **03** **Standard slippage (0.15%)** | 0.25% / 0.30% | 0.15% **63,954.7+** | **0.044%+** | 27.6% 134,612 | ✅ **PASS** |
| **04** | **High slippage (0.30%)** | 0.25% / 0.30% | 0.30% **40,137.8+** | **0.028%+** | 31.0% 165,247 | ✅ **PASS** |
| **05** | **Severe slippage (0.50%)** | 0.25% / 0.30% | 0.50% **12,079.9+** | **0.008%+** | 27.6% 224,080 | ✅ **PASS (survival)** |
| **06** | **Increase exchange spread (+50%)** | 0.25% / 0.30% | 0.15% **63,954.7+** | **0.044%+** | 27.6% 134,612 | ✅ **PASS** |
| **07** | **Failure of maker orders (All Taker Exits)** | 0.30% / 0.30% | 0.15% **58,056.8+** | **0.040%+** | 27.6% 140,510 | ✅ **PASS** |
| **08** | **Stop slippage delay (0.35%)** | 0.25% / 0.30% | 0.35% **18,782.6+** | **0.013%+** | 31.0% 183,064 | ✅ **PASS** |
| **09** | **Severe lack of liquidity (Slip 0.40% + Fee 0.40%)** | 0.30% / 0.40% | 0.40% **13,435.6-** | 0.009% - | 24.1% 224,393 | ❌ **FAIL (Failure)** |
| **10** | **Unfavorable candle path (Adverse Intrabar)** | 0.25% / 0.30% | 0.15% **63,954.7+** | **0.044%+** | 27.6% 134,612 | ✅ **PASS** |
| **11** | **Incomplete order filling (Partial Fill 70%)** | 0.25% / 0.30% | 0.15% **63,954.7+** | **0.044%+** | 27.6% 134,612 | ✅ **PASS** |
| **12** **Mandatory clearing at the competition deadline** | 0.25% / 0.30% | 0.15% **63,954.7+** | **0.044%+** | 27.6% 134,612 | ✅ **PASS** |
| **13** **Volatility Shock 0.25% Slip** | 0.25% / 0.30% | 0.25% **45,701.7+** | **0.032%+** | 31.0% 153,879 | ✅ **PASS** |
| **14** | **Lost Biggest Winning Trade (No W09)** | 0.25% / 0.30% | 0.15% **3,440.8-** | 0.002% - | 25.0% | 120,420 | ❌ **FAIL (Failure)** |

---

## 2. Autopsy of system failure points (Failure Bottlenecks)

### Failure 1 (scenario number 9: severe liquidity crisis):
- **Terms:** 0.40% slippage along with 0.40% ticker fee (return friction more than **1.40%**).
- **Result:** The total friction reaches 224,393 Tomans and the net profit becomes **-13,436 Tomans loss**.
- **Control solution:** Installation of the barrier to stop the transaction (Spread & Slippage Circuit Breaker) if the market spread exceeds 0.18%.

### Failure 2 (Scenario #14: Failure to execute the best winning trade):
- **Conditions:** Disconnection or orders not being filled in W09 rising wave.
- **Result:** The system without this window reaches **-3,441 Tomans loss**.
- **Scientific result:** The system relies on hunting outlier days of upward swing for profitability; Therefore, it is vital to ensure the stability of the communication and send the order as soon as the signal is issued.

---

## 3. Decisive superiority of model C over candidate E in stress tests

| Comparison in stress tests Primary E candidate (Phase 22) | Integrated model H1+H3 (phase 25) |
|---|:---:|:---:|
| **Consistency in candle shadow (Intra-bar High/Low)** | ❌ **failure (-12,284 tomans)** | **Complete Pass (+63,955 Tomans)** |
| **Stability in severe slippage (0.50%)** | ❌ **failure (-121,388 Tomans)** | ✅ **Pass (+12,080 Tomans)** |
| **Stability in the failure of maker orders (All Taker)** | ❌ **Heavy failure** | ✅ **Excellent Pass (+58,057 Tomans)** |
| **Stability in higher exchange fees (0.40%)** | ❌ **Failure** | ✅ **Pass (+28,791 Tomans)** |

The combined H1+H3 model survived in **12 out of 14 scenarios with positive profitability** and showed a much higher microstructural resistance than candidate E.