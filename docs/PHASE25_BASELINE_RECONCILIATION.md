# Phase 25 Baseline Reconciliation
## Forensic Resolution of Arithmetic Inconsistencies and Trade-Ledger Audit

> **Repository:** [`wallex`](file:///root/starcoach-hack/wallex)  
> **Research branch:** `research/phase25-validation`  
> **Frozen base commit:** [`b494d60e211497f47ef3b79d6ae79a0726471172`](file:///root/starcoach-hack/wallex)  
> **Initial capital of each window:** 5,000,000 Tomans in cash ($N = 29$ independent window of 72 hours)  
> **Status of live transactions:** `live_execution_authorized = False' (fully blocked and secure)

---

## 1. Resolution of Arithmetic Discrepancy Phase 24

### Statement of the problem:
It was mentioned in the text report of phase 24:
- Window W09: profit 36,800+ Tomans
- Window W23: Profit 16,209+ Tomans
- Total of 27 other match windows: reported as -35,800 Tomans loss
- Initial reported total: 47,241+ Tomans

The sum of these figures is equal to:
$$36,800 + 16,209 - 35,800 = +17,209 \neq +47,241 \text{ TMN}$$

### rooting and accurate numerical matching (Forensic Root Cause):
The audit of the trade ledger showed that in the writing of the phase 24 report, **the numbers of two different test phases were mistakenly combined with each other (Conflated):
1. The figure **36,800+ Tomans (W09)** and the figure **47,241+ Tomans (Total)** belonged to **Step 1 (Candidate E Raw - Deterministic with total average ATR and Close exit)**. At this stage, the total of 27 other windows of the competition was exactly equal to **5,768.60 Tomans**:
   $$+36,800.18 + 16,209.11 - 5,768.60 = \mathbf{+47,240.68 \text{ TMN}}$$
2. The figure **35,800 Tomans** belongs to **stage 3 (Candidate E with AI agent filter and expandable window)**. In phase 3, the profit of the W09 window was reduced to 28,834.63 Tomans, and the total of the other 27 windows was exactly **-35,800.64 Tomans**, the sum of which constituted the final profit of 9,243.10 Tomans for phase 23:
   $$+28,834.63 + 16,209.11 - 35,800.64 = \mathbf{+9,243.10 \text{ TMN}}$$
3. The author of the previous report had mistakenly included the results of the 27 windows of stage 3 (-35,800 Tomans) next to the figures of stage 1 (+36,800 Tomans and +47,241 Tomans), which led to a formal contradiction of $17,209 \neq $47,241.

---

## 2. Comprehensive table of accounting adjustment in all stages of development and audit ($N = $29)

| Modeling stage and strategy version Window profit W09 (Toman) | Profit window W23 (Toman) | Total W09 + W23 | A total of 27 other windows Total net profit (tomans) | Balance check status ($Sum$) |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| **Stage 1 (Raw Phase 22 - Global ATR, Close)** | 36,800.18+ | 16,209.11+ | 53,009.28+ | **5,768.60-** | **47,240.68+** | ✅ Accurate ($0.00 error) |
| **Step 2 (Cleaning the leak - Expanding ATR, Close)** | 29,347.66+ | 16,209.11+ | 45,556.77+ | **13,370.89-** | **32,185.88+** | ✅ Accurate ($0.00 error) |
| **Phase 3 (Industrial Phase 23 - Expanding ATR + AI)** | 28,834.63+ | 16,209.11+ | 45,043.74+ | **35,800.64-** | **9,243.10+** | ✅ Accurate ($0.00 error) |
| **Step 4 (Real Execution - Intra-bar High/Low Wicks)** | 15,192.34+ | 13,210.00+ | 28,402.34+ | **40,686.43-** | **12,284.09-** | ✅ Accurate ($0.00 error) |

---

## 3. Independent reproduction of phase 24 hypothesis outputs (Independent Reproduction)

Phase 24 executable codes in module [`src/experimental/phase24_research_engine.py`](file:///root/starcoach-hack/wallex/src/experimental/phase24_research_engine.py) were reproduced independently on raw Wallex data cache:

| The name of the hypothesis / strategy Reported Total Net Profit (TMN) | Reproduced Net Profit (TMN) | Number of transactions T statistic ($t$) | Windows win rate Computational matching
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| **Corrected E candidate (stage 4)** | 12,284-| **12,284.1-** | 28 | -0.45 34.5% ✅ 100% PASS
| **H1: multitemporal structural trend** | 35,793+ | **35,793.4+** | 19 | 0.64+ | 27.6% ✅ 100% PASS
| **H2: Return after the fall (Dip)** | 11,803+ | **11,803.0+** | 13 | 0.43+ | 20.7% ✅ 100% PASS
| **H3: Acceleration leakage from BTC to Altcoins** | 34,735+ | **34,734.5+** | 5 | 1.70+ 13.8% ✅ 100% PASS
| **H4: Walk-Forward machine learning meta-model** | 11,973- | **11,973.0-** | 1 1.00- | 0.0% | ✅ 100% PASS

---

## 4. Baseline status summary for phase 25

1. ** Arithmetic uncertainty is completely resolved:** The balance of the portfolio in all 29 windows of the competition in four stages was confirmed accurately cent by cent.
2. **candidate E completely excluded:** There is no justification for using candidate E in the contest; Because in actual implementation with candle shadow, it makes a loss of -12,284 tomans.
3. **Hypotheses H1 and H3 will be the focus of Phase 25:** Both hypotheses have positive profitability, but their fundamental challenges (very small number of H3 trades with 5 trades, and decline of H1 out-of-sample profit in W16-W29) require independent dissection, advanced tests, and rigorous execution tests.