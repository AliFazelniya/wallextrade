# Independent validation of the sample with completely pristine data (Phase 26 Independent Data Validation)
## Strict Blind Out-of-Sample Validation on Unseen Historical Market Data (July 05 - July 24, 2026)

> **Repository:** [`wallex`](file:///root/starcoach-hack/wallex)  
> **Research branch:** `research/phase26-forensic-validation`  
> **Frozen base commit:** [`b494d60e211497f47ef3b79d6ae79a0726471172`](file:///root/starcoach-hack/wallex)  
> **Pristine OOS data period:** From July 5, 2026 to July 24, 2026 (19 consecutive days before the start of the baseline data)  
> **Number of independent 15-minute candles:** **1,825 candles** per symbol (`BTCTMN`, `ETHTMN`, `SOLTMN`)  
> **Number of independent match windows ($N$):** **6 full 72-hour windows** ($W_{-06}$ to $W_{-01}$)  
> **STATISTICAL VALIDATION STATE:** ⚠️ **INCONCLUSIVE / REGIME-DEPENDENT**

---

## 1. Why the need for independent and pristine data (The Contamination Problem)

During phases 20 to 25, the 90-day dataset (July 24 to October 22, 2026, including 29 windows) was repeatedly evaluated, inspected, and calibrated.  
In financial academic standards (such as Harvey, Liu, and Zhu 2016 about the risk of frequent data snooping tests), such a dataset is called "Research Data" and it can no longer be considered a blind and intact sample test.

To break this deadlock, the Phase 26 audit team extracted an independent data set of 19 consecutive days immediately before the start of the 90-day data set (from July 5 to July 24, 2026) from the official UDF endpoint of Wallex exchange. This time period has **never been seen, touched, or optimized in any of the previous 25 phases**.

---

## 2. The table of the results of the blind test of the strategies in the independent interval of the out-sample ($N = $6 windows)

Evaluation conditions fully comply with the frozen competition rules: initial capital 5,000,000 tomans, builder fee 0.25%, order taker 0.30%, slippage 0.15%, candle shadow monitoring and limit of 2 open positions at the same time:

| Configuration of the model in the blind test Total Net Profit (TMN) | Average efficiency of 72 hours Windows win rate Number of transactions T statistic ($t$) | Maximum capital loss (Max DD) | Total Exchange Friction (TMN) |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Model A: exclusive H1 (structural trend)** | **23,509.0-** | **0.078%-** | 33.3% (2/6) | 10 | -0.71 0.75% 38,922 |
| **Model B: Exclusive H3 (Lead-Leg Acceleration Leakage)** | **29,551.2-** | **0.099%-** | 0.0% (0/6) | 3 1.56- | 0.55% 13,407 |
| **Model C: integrated combination of H1+H3** | **23,509.0-** | **0.078%-** | 33.3% (2/6) | 10 | -0.71 0.75% 38,922 |

---

## 3. Scientific autopsy of the causes of damage in the independent period (Failure Mechanism Analysis)

Examining each of the 10 transactions made in these 19 days revealed very important facts:
1. **Heavy burden of exchange friction against gross profit:**
   - Gross profit of transactions without fees: **15,413+ Tomans** (the system correctly recognized the direction of the market).
   - Total fee and slip fees: **38,922 Tomans**!
   - Net result: **23,509-tomans loss!** Exchange friction swallowed more than 2.5 times the total gross profit of transactions.
2. **Different behavior of assets:**
   - During this period, Bitcoin rose 15.9% and Ethereum 19.6%, but Solana, the previous profit leader, showed a corrective behavior with a weak growth of 5.3%.
   - The result according to the symbol: Solana **-14,222-tomans loss** and Bitcoin **-13,698-tomans loss**; While Ethereum was the only asset with a small profit (**4,411+ Tomans**).
3. **H3 model failure:**
   - The H3 model caused a loss of nearly 30 thousand tomans with 3 transactions and a 0% win rate; Because Bitcoin's rapid spikes during this period did not leak to altcoins due to erosive volatility and ended with limit activation.

---

## 4. Key lessons for hackathons and statistical validation

> [!CAUTION]
> ### The scientific truth:
> **Structural trend strategies (H1 and H3) do not have sustainable profitability in all market regimes.**  
> These strategies are only profitable during periods of high-speed waves with amplitudes of more than 4.5% to compensate for the heavy friction of 0.70% to 0.90% per trading round of Wallex exchange.  
> In erosive or fluctuating regimes (such as this independent period or the third month of the 90-day period), continuous trading leads to capital erosion.

### Final verdict of independent data audit: ``INCONCLUSIVE / CONDITIONAL''
The constant profitability hypothesis was rejected. In the 72-hour race, the system only has a chance to succeed when macro market conditions are in an explosive bullish regime; Otherwise, the default survival strategy should be **100% liquidity in Toman wallet**.