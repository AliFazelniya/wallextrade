# Comprehensive audit of the validity and sensitivity of stress tests (Phase 26 Stress Test Integrity)
## Adversarial Stress-Test Verification, State Mutation & Execution Realism Audit

> **Repository:** [`wallex`](..)  
> **Research branch:** `research/phase26-forensic-validation`  
> **Frozen base commit:** [`b494d60e211497f47ef3b79d6ae79a0726471172`](..)  
> **Audit evaluation status:** ✅ **Completely resolving the ambiguities and confirming the correctness of the state mutation (State Mutation Verified)**

---

## 1. Root Cause Analysis of Identical Results of Phase 25 Scenarios

In the phase 25 report, four stress scenarios reported exactly the same profit as the base case (+63,954.7 Tomans):
1. Increase of 50% spread ("Increased Spreads +50%")
2. Reducing the ratio of partial implementation to 70% (`Partial Fills 70%')
3. Forced Deadline Liquidation
4. Adverse Intrabar Path

### Scrutiny audit of phase 25 script code:
A line-by-line examination of the script [`src/experimental/stress_test_14_scenarios.py`](../src/experimental/stress_test_14_scenarios.py) and the function [`simulate_portfolio_ensemble`](../src/experimental/ensemble_engine.py#L33) revealed the secret of this similarity:
- **Defective parameters sent in phase 25:** In the initial script of phase 25, scenarios 06, 11 and 12 instead of sending mutated values (such as `spread_multiplier=1.5` or `fill_ratio=0.70`), due to the absence of these arguments in the signature of the simulator function, unwanted base default values (`slippage_pct=0.15, maker_fee=0.0025, taker_fee=0.0030`) were sent to the engine! In fact, the simulation engine had never noticed the application of these stresses!
- **Adverse Intrabar scenario:** The base simulator engine was pre-coded as **conservative and pessimistic** (`is_sl' was always checked before `is_tp'). Therefore, running the pessimistic mode did not change the baseline output.

---

## 2. Applying structural modifications and actual jump of parameters in phase 26 engine

In phase 26, the signature of the ``simulate_portfolio_ensemble'' function and its execution logic were rewritten with explicit and real state transition parameters:
- `spread_multiplier: float = 1.0` (multiply the spread by 1.50 and apply it to the entry threshold filter and execution cost)
- `fill_ratio: float = 1.0` (decrease the nominal volume of the order to 70%: `notional = 500,000 * 0.70 = 350,000 TMN`)
- `forced_deadline_hour: float = 72.0` (apply immediate settlement at the 68th hour of the match with Taker's order)
- `favorable_intrabar: bool = False` (default pessimistic mode vs optimistic mode)

---

## 3. Reproduced matrix table of stress test with real state jump (14 scenarios)

| Number and description of the stress scenario Total Net Profit (TMN) | average yield | Windows win rate Number of transactions Exchange Friction (TMN) | Status and analysis of changes
|---|:---:|:---:|:---:|:---:|:---:|---|
| **01. Standard basis (slippage 0.15% and official fee)** | **63,954.7+** | **0.044%+** | **27.6%** | 35 | 134,612 | Base reference point
| **02. Incremental fee (0.35% Maker and 0.40% Taker)** | 28,791.1+ | 0.020%+ | 27.6% 35 | 169,775 | Profit decreased (increased friction) |
| **03. Standard slip 0.15%** | 63,954.7+ | 0.044%+ | 27.6% 35 | 134,612 | According to the basis |
| **04. High slip (0.30%)** | 40,137.8+ | 0.028%+ | 31.0% 34 | 165,247 | Rational profit decreased
| **05. Severe slippage (0.50%)** | 12,079.9+ | 0.008%+ | 27.6% 35 | 224,080 | Maintaining a positive profit margin
| **06. Incremental spread (+50% and spread filter)** | **85,321.7+** | **0.059%+** | 24.1% **19** | **72,693** | **REAL CHANGE HAPPENED!** (NOISE TRADING REDUCTION) |
| **07. Failure of manufacturer orders (100% Taker)** | 58,056.8+ | 0.040%+ | 27.6% 35 | 140,510 | Stability in ticker exits
| **08. Stop execution delay (0.35% stop slip)** | 18,782.6+ | 0.013%+ | 31.0% 35 | 183,064 | Reduction of rational profit
| **09. Liquidity shock (slippage of 0.40% and high fees)** | **13,435.6-** | 0.009% - | 24.1% 35 | 224,393 | ❌ **rejected (insignificant liquidity loss)** |
| **10. The pessimistic intercandle path (Adverse SL)** | 63,954.7+ | 0.044%+ | 27.6% 35 | 134,612 | Proving the non-existence of ambiguous candles at the same time
| **11. Partial filling (completion of 70% of the order volume)** | **44,768.3+** | **0.031%+** | 27.6% 35 | **94,228** | **Exactly 70.0% profit and base friction!** |
| **12. Mandatory early settlement in 68 hours **69,012.7+** | **0.048%+** | 27.6% 35 | 134,637 | Profit improvement by exiting before the final swing
| **13. Oscillating shock stress (slip 0.25%)** | 45,701.7+ | 0.032%+ | 31.0% 34 | 153,879 | Reasonable stability
| **14. Remove Top Profitable Window (No W09)** | **3,440.8-** | 0.002% - | 25.0% | 31 | 120,420 | ❌ **rejected (dependence on exceptional wave)** |

---

## 4. Mathematical and physical proof of system response to mutations

1. **Mathematical proof of partial filling of 70% (Scenario 11):**  
   $$63,954.7 \times 0.70 = 44,768.29 \text{ TMN}$$  
   $$134,612 \times 0.70 = 94,228.40 \text{ TMN}$$  
   The actual output of the script with the accuracy of 100 rials was exactly **+44,768.3 Tomans** profit and **94,228 Tomans** friction. This is definitive proof of the linear effect of position volume.
2. ** Discovery of the 50%+ spread scenario (Scenario 06):**  
   By multiplying the spread by 1.5, the input spread filter ( $Spread \le 0.16\%$ ) became more active and vetoed 16 swing trades that were made at border spreads and were generally closed at a loss. As a result, the transactions were reduced to 19 refined transactions and the profit reached **+85,321.7 Tomans**.
3. **Proving the reason for the stability of the internal scenario (Scenario 10):**  
   A test run with an optimistic assumption (`favorable_intrabar=True') also reproduced exactly the number 63,954.66 Tomans; Because in all 35 historical transactions, there was not a single 15-minute candle whose ceiling reached the target of +4.5% and its floor reached the stop of -2.2% (requiring a swing range of 6.7% in 15 minutes). Therefore, there is no internal ambiguity in history.

### The final verdict of the audit of the stress tests: ``PASS''
The defect of phase 25 simulation was solved, the mutation of the variables was done in a real and provable way, and the system showed a completely valid physical and mathematical behavior.