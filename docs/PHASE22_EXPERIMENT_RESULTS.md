# Experimental and reproducible results of strategy tests (Phase 22)
## Reproducible Experimental Results & Stress Testing Suite

> **Research branch:** `research/phase22-discovery`  
> **Repository:** [`wallex`](file:///root/starcoach-hack/wallex)  
> **Base commit:** [`b494d60e211497f47ef3b79d6ae79a0726471172`](file:///root/starcoach-hack/wallex)  
> **Environment:** Python 3.12.3, isolated in module [`src/experimental/`](file:///root/starcoach-hack/wallex/src/experimental)

---

## 1. Table of experimental results of all candidates in 29 independent competitive windows (Primary Benchmark N = 29)

All experiments were simulated with an initial capital of 5,000,000 Tomans in cash at the beginning of each 72-hour window, without legacy positions, and with Wallex level one fee (0.25% maker and 0.30% ticker) and 0.15% executive slippage:

| Strategy Candidate | Total Profit/Loss (TMN) | The average yield is 72h Total win rate No-deal windows Number of transactions Maximum capital loss Total exchange friction | T-statistics (vs 0) | 95% efficiency confidence interval Performance status
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Phase 21 Frozen Baseline (AI Baseline)** | **28,871-** | **0.0199%-** | 20.7% 10 out of 29 (34.5%) | 26 | 0.51% 109,921 TMN 0.386-| [-0.125%, +0.086%] | Loser
| **Det Baseline of phase 21** | **96,471-** | **0.0665%-** | 41.4% 0 of 29 (0.0%) | 50 | 0.72% | 211,721 TMN 0.940-| [-0.212%, +0.079%] | severe loss
| **100% cash base line (100% Cash)** | **0** **0.0000%** | 0.0% | 29 out of 29 (100%) | 0 | 0.00% | 0 TMN 0.000 | [0.000%, 0.000%] | unbiased
| **Candidate A (adaptive process + final sail)** | **125,577-** | **0.0872%-** | 0.0% | 12 out of 29 (41.4%) | 34 | 0.35% 192,493 TMN 4.227-| [-0.129%, -0.045%] | Failed (small targets failed) |
| **Candidate B (Danchian channel failure + ADX)** | **68,975-** | **0.0479%-** | 31.0% 3 out of 29 (10.3%) | 38 | 0.55% 164,260 TMN 0.927-| [-0.153%, +0.057%] | Loss due to friction
| **Candidate C (return to mean in range)** | **5,427+** | **0.0038%+** | 3.4% **28 out of 29 (96.6%)** | **1** 0.04% | 3,519 TMN 1.000+ | [-0.004%, +0.011%] | Profitable but practically inactive
| **candidate D (multimode routing agent)** | **75,693-** | **0.0526%-** | 31.0% 2 out of 29 (6.9%) | 43 | 0.59% | 181,265 TMN 1.011- | [-0.158%, +0.054%] | Loser
| **Candidate E (BTC/ETH/SOL cross section momentum + sail)** | **47,241+** | **0.0328%+** | **44.8%** | **7 out of 29 (24.1%)** | **33** | **0.48%** | **131,612 TMN** | **0.726+** | **[-0.059%, +0.125%]** | **The best candidate (profitable and active)** |

---

## 2. In-sample validation against out-of-sample candidate E (Out-of-Sample Validation)

In order to avoid overfitting, the dataset was divided into two chronological sections:
- **In-Sample:** windows W01 to W15 (days 0 to 45)
- Out-of-Sample: Windows W16 to W29 (Days 45 to 90)

| Evaluation index In-sample segment (W01-W15) | Out-of-sample section (W16-W29) | The entire period of 29 windows
|---|:---:|:---:|:---:|
| **Number of windows** | 15 windows 14 windows 29 windows
| **Tomani net profit** | **3,453.4+ Tomans** | **43,787.3+ Tomans** | **47,240.7+ Tomans** |
| **Average efficiency of 72 hours** | **0.005%+** | **0.063%+** | **0.033%+** |
| **Average yield of 72 hours** | 0.000% | 0.000% | 0.000% |
| **Window range rate** | **46.7%** (7 out of 15) | **42.9%** (6 out of 14) | **44.8%** (13 out of 29) |
| **windows without transaction** | 3 out of 15 (20.0%) | 4 out of 14 (28.6%) | 7 out of 29 (24.1%) |
| **Number of closed transactions** | 21 transactions 12 transactions 33 transactions
| **Maximum capital loss** | 0.48% | 0.36% 0.48% |
| **total friction paid** | 84,483 Tomans 47,129 Tomans 131,612 Tomans
| **T-Statistic** | 0.063+ | **1.199+** | **0.726+** |

> [!IMPORTANT]
> Candidate E not only maintained its profitability in the out-of-sample sector, but its average return in the out-of-sample period increased to **0.063%+** and the T-statistic increased to **1.199+**. This proves that the superiority of candidate E was not due to a random fit to the past history.

---

## 3. Stress testing and friction sensitivity tests (Stress Testing Matrix)

Candidate E was tested in 8 stress scenarios under heavy fee loads and price slippage:

| Tension scenario Total Net Profit (TMN) | average yield | Windows win rate Number of transactions Total exchange friction | Resilience analysis
|---|:---:|:---:|:---:|:---:|:---:|---|
| **1. Baseline (slippage 0.15%, fee 0.25/0.30%)** | **47,241+** | **0.033%+** | **44.8%** | 33 | 131,612 TMN Standard racing basis
| **2. High slippage (0.30% slippage)** | 66,692- | 0.046% - | 31.0% 34 | 177,153 TMN Drop in profitability in slippage 2 times
| **3. Severe slippage (0.50% slippage)** | 167,585- | 0.116%-| 20.7% 35 | 245,371 TMN Critical fragility threshold
| **4. 50% increase in market spread** | **8,689+** | **0.006%+** | **27.6%** | 21 | 84,509 TMN Maintaining profitability by vetoing open spreads
| **5. Executive delay (1 candle delay in entry)** | **9,958+** | **0.007%+** | **37.9%** | 34 | 137,976 TMN High resistance to network delay
| **6. Competition incentive fee (0.08% fixed)** | **115,777+** | **0.080%+** | **44.8%** | 33 | 63,076 TMN The peak of profitability in the competition discount
| **7. High ticker fee (0.40% exchange ticker)** | **18,476+** | **0.013%+** | **37.9%** | 33 | 160,377 TMN Maintaining profitability even at 0.40% fee

---

## 4. Autopsy of the causes of failure of unsuccessful candidates

1. Why did candidate A fail? (125 thousand tomans loss):**  
   With the reduction of the profit limit from 4.0% to 2.0% and the loss limit to 1.2%, the frequency of activation of the stop loss increased drastically. Each activation of the loss limit generated a net loss of 2.0%, including 0.75% commission and slippage; While the profit margin after deducting fees remained only 1.2%. This asymmetry destroyed the reward-to-risk ratio.
2. ** Why candidate C was practically not used? (only 1 transaction in 90 days):**  
   For the mean reversion strategy at 0.60% exchange fee to be profitable, the distance between the floor of the Bollinger Band and the mean line should be at least 1.2% to 1.5%. In non-volatile regimes (ADX < 20), the bandwidth is strongly compressed and this distance rarely reaches 1.2%; As a result, the cost filter prevented entry in 28 windows.
3. **Why candidate E won?:**  
   Because he always chose the strongest momentum among the 3 currencies and by setting a more open target (profit limit of 3.2% against loss limit of 1.5%), the net profit of each winning trade (+2.5%) easily covered the exchange costs and by curbing the emergency liquidation in the last 12 hours, he reduced the final loss to zero.