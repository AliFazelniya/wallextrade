# Independent comparative evaluation of H1 vs H1+H3 (Phase 26 H1 vs H1+H3)
## Comparative Evaluation, Incremental Value of H3, Collinearity & Parsimony (Occam's Razor)

> **Repository:** [`wallex`](..)  
> **Research branch:** `research/phase26-forensic-validation`  
> **Frozen base commit:** [`b494d60e211497f47ef3b79d6ae79a0726471172`](..)  
> **Final judgment of the portfolio structure:** ⚖️ **Occam's razor rule: the superiority of the independent H1 model over the raw combination; Accepting H1+H3 only with floating assignment AI module**

---

## 1. Comprehensive performance comparison table of 4 models in 29 competitive windows

| performance and friction evaluation index Model A: exclusive H1 (structural trend) | Model B: Exclusive H3 (Lead-Leg Acceleration Leakage) | Model C: Deterministic H1+H3 (crude combination) | Model D: Combining H1+H3 with floating allocation artificial intelligence
|---|:---:|:---:|:---:|:---:|
| **total net profit of 29 windows (TMN)** | **63,034.8+** | 48,707.9+ | **63,954.7+** | **84,053.0+** |
| **Average efficiency of 72 hours** | 0.043%+ | 0.034%+ | 0.044%+ | **0.058%+** |
| **Incremental profit compared to H1 (TMN)** | Basis | 14,327-TMN **920+ TMN (tiny!)** | **21,018+ TMN (Dazzling)** |
| **Total number of transactions** | 33 | 6 | 35 | 35 |
| **Total Exchange Friction (TMN)** | 125,648 | **22,138** | 134,612 | 123,488 |
| **imposed additional friction (TMN)** | Basis | TMN-103,510 **8,964+ TMN** | 2,160- TMN (friction reduction) |
| **Ratio of profit to loss (Profit Factor)** | 1.50 | **3.20** | 1.48 | **1.74** |
| **Maximum capital loss (Max DD)** | 0.74% **0.32%** | 0.74% 0.74%
| **Window range rate** | 27.6% 13.8% 27.6% **31.0%** |
| **Performance in independent out-of-sample test (OOS)** | 23,509-| 29,551-| 23,509-| **18,400- (loss control)** |

---

## 2. Collinearity & Redundancy

Analysis of simultaneous behavior of two strategies in 29 windows showed:
1. **94% Overlap in Gross Profit:** Adding Model B (H3) to Model A (H1) only made **920 Tomans** additional net profit, but **8,964 Tomans in additional friction and slippage**!
2. **Colinearity Origin:** Bitcoin's breakout conditions in H3 (1.4x volume increase and moving average slope), occur exactly at the same time as the 1-hour time frame uptrend formation in H1. As a result:
   - or both models simultaneously issue a signal to Solana, which is vetoed by the Anti-Duplicate Gate clause.
   - or the capacity of 2 portfolio positions is already filled by H1 trades.
3. **Risk in bearish and erosion regimes:** In the 19-day independent test of the sample (July 2026), the H3 model recorded a loss of nearly **30,000 Tomans** with 3 consecutive losing trades; Because the Bitcoin spikes were false and were not transferred to altcoins.

---

## 3. Judging based on the principle of simplicity and Occam's Razor Verdict

> [!IMPORTANT]
> ### The principle of simplicity in algorithmic trading systems:
> If the two models produce roughly the same net profit (+63.0k vs +63.9k), the system with **less technical complexity, fewer lines of code, fewer breakpoints, and lower exchange friction** is always preferred.

1. **In the raw deterministic mode:** The combination of H1+H3 has no economic justification; Because the complexity of adding a lead-lag engine for only 920 Tomans of profit (which is statistically not significantly different from zero, $t=0.08$) is not worth the operational burden and risk of error. **H1 independent model is superior.**
2. **In the presence of floating allocation artificial intelligence (Model D):** If the calibrated artificial intelligence enters the circuit to adjust the volume, the integrated model by using both sources of opportunity and intelligently adjusting the order volume reaches **+84,053 Tomans net profit** and creates a tangible advantage of 21,000 Tomans (+33%).

### Final engineering decision for the race:
- **Final top configuration:** **H1+H3 integrated model exclusively with artificial intelligence module of floating volume allocation (``Learned Dynamic Sizing'')**.
- **Backup Configuration (Deterministic Fallback):** If any system error occurs in the artificial intelligence module, the system immediately switches to **Independent Model A (H1 Only)** to avoid unnecessary complexity.