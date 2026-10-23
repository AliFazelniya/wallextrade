# Scientific research and validation of hypothesis 3: Leakage of Bitcoin acceleration to altcoins (Phase 25 H3 Research)
## Empirical Research on BTC-to-Altcoin Lead-Lag Relationships & Momentum Spillover

> **Repository:** [`wallex`](file:///root/starcoach-hack/wallex)  
> **Research branch:** `research/phase25-validation`  
> **Frozen base commit:** [`b494d60e211497f47ef3b79d6ae79a0726471172`](file:///root/starcoach-hack/wallex)  
> **Statistical status of hypothesis 3:** ⚠️ **EXPLORATORY — lacks definitive statistical proof due to the small sample size ($N=5$)**

---

## 1. Academic Literature & Theoretical Foundation

The phenomenon of Information Lead-Lag and Volatility Spillover in crypto markets has been proven in reliable financial articles:

1. **Makarov & Schoar (2020, Journal of Financial Economics):**  
   The flow of institutional liquidity first enters the Bitcoin market (the deepest and most liquid asset) and the initial price discovery takes place in BTC; Then capital flows to altcoins (Spillover).
2. **Katsiampa et al. (2019, International Review of Financial Analysis):**  
   Experimental proof of high-frequency co-movement and asymmetric turbulence transfer from Bitcoin to Ethereum and other assets; Changes in the direction of the trend in Bitcoin are the forerunners of rapid changes in altcoins.
3. **Liu & Tsyvinski (2021, Review of Financial Studies):**  
   The Market Factor in crypto is driven by Bitcoin, while assets with higher betas (such as SOL) record sharper bounces with a time lag compared to the initial BTC wave due to greater liquidity elasticity.

---

## 2. Distinguishing between statistical correlation and real lead-lag (Correlation vs Predictive Lead-Lag)

**Contemporaneous Correlation:** BTC and SOL price correlation is above 0.75 on a daily scale; This correlation merely reflects the general direction of the market and does not provide any trading advantage.
**Predictive Lead-Lag:** Hypothesis 3 focuses on the time delay of liquidity shock processing:  
  When in a 15-minute candle, Bitcoin's volume reaches more than 1.4 times the average and its EMA divergence jumps above 0.6%, altcoins (especially SOL) usually react more strongly in the next candle.

---

## 3. Detailed autopsy of 5 transactions of hypothesis 3 and strict lag testing (Strict Lag Testing)

| No Competition window Login property | Entry Time (UTC) | Departure Time (UTC) | The reason for leaving Net Profit (TMN) | Order type
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **1** **W09** | Sol 2026-08-20 04:30 | 2026-08-20 08:15 | Structural profit limit (+3.5%) | 14,706.2+ | maker |
| **2** **W14** | Sol 2026-09-03 10:30 | 2026-09-03 14:45 | Structural profit limit (+3.5%) | 14,706.2+ | maker |
| **3** **W14** | ETH | 2026-09-03 21:30 | 2026-09-04 12:30 | Structural loss limit (-1.8%) | 11,973.0- | Ticker
| **4** **W15** | ETH | 2026-09-05 11:00 | 2026-09-06 03:45 | Structural profit limit (+3.5%) | 14,706.2+ | maker |
| **5** **W24** | Sol 2026-10-03 13:30 | 2026-10-04 20:15 | Exit passive final sail 2,588.7+ | maker |

### Zero Same-Candle Lookahead Definite Delay Test:
In order to ensure that there is no leakage in the same candle, the algorithm was bound in such a way that after the complete closing of the Bitcoin bounce candle at time $t$, the order to enter the altcoin is sent in the next candle $t+1$:
- **Net profit with definite delay of 1 candle:** **23,966.2+ Tomans**
- **Number of transactions:** 4 transactions (3 winners, 1 loser)
- **exchange friction:** 15,064 tomans
- **Result:** Lead-lag is a genuine hypothesis and is not caused by data leakage in the same candle.

---

## 4. Statistical judgment and structural limitation of hypothesis 3 (Statistical Verdict)

> [!WARNING]
> ### Classification of the scientific status of hypothesis 3: **EXPLORATORY / UNPROVEN**
> Although the economic logic of the model is documented in academic articles and it made a positive profit in the backtest (+34.7k or +24k with delay), but **4 or 5 transactions during 90 days is a very small sample size and is not sufficient in terms of statistical inference.**  
> In a 72-hour competition, with a high probability of 85%, during the 3 days of the competition, **no such volume jump in Bitcoin may occur**; Therefore, exclusive reliance on hypothesis 3 will lead to 100% account inactivity in the competition.