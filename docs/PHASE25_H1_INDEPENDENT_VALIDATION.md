# Independent validation of hypothesis 1: multi-temporal structural process (H1 Independent Validation)
## Multi-Timeframe Structural Trend Hypothesis Audit

> **Repository:** [`wallex`](..)  
> **Research branch:** `research/phase25-validation`  
> **Frozen base commit:** [`b494d60e211497f47ef3b79d6ae79a0726471172`](..)  
> **Hypothesis 1:** 1-hour structural trend + 15-minute entry + structural loss limit -2.2% + profit limit +4.5%

---

## 1. Answers to 10 key questions of hypothesis 1 audit (Ten Critical Research Inquiries)

### 1. Do the signals only use fully closed candles?
✅ **Yes (PASS):** The calculations of EMA, RSI, ATR and ADX indicators in the $t$ candle index are all based on the Close price of the 15-minute closed candle. The decision is recorded at the end of the candle and there is no reliance on the unfinished price of the current candle.

### 2. Is the 1-hour data consistent with the 15-minute timestamps?
✅ **YES (PASS):** The empirical conformity test showed that the continuous moving approximation (80 15-minute candles for the 20-hour EMA and 200 candles for the 50-hour EMA) has **99.00% trend direction concordance** with the real 1-hour resampled candles (with a small average error of 0.0628%). In addition to maintaining accuracy, this method also avoids the clock boundary error at the start of the match windows.

### 3. Does hypothesis 1 suffer from data leakage to the future (Lookahead Contamination)?
✅ **No (PASS):** Unlike the initial candidate E that used the 90-day total ATR average, in hypothesis 1 the dynamic spread normalization exclusively uses the **expanding retrospective window (`expanding(min_periods=60).mean()`)** and the future leakage is completely zero.

### 4. Are the -2.2% loss limit and 4.5% profit limit selected based on hindsight?
⚠️ **Data bias warning (SELECTION AWARENESS):**  
Profit limit of 4.5% and stop loss of 2.2% were formulated after observing the failure of candidate E's tight stops (-1.5%). From a scientific point of view, these parameters have a past observation bias (data snooping) on ​​the 90-day cache and should not be accepted as definitive optimal parameters without a generalizability test.

### 5. Is the performance of H1 dominated by exceptional periods of the trend?
⚠️ **Trend Regime Dependency Confirmation:**  
- In the first half (W01 to W15 when Bitcoin grew by 57%): Profit **35,446+ Tomans** with 4 wins from 15 windows.
- In the second half (W16 to W29 when the market became neutral and volatile): Profit **347+ Tomans** with 4 wins from 14 windows.
The strategy does not suffer heavy losses in the market (capital is preserved), but it makes most of its profits in uptrend waves.

### 6. Is risk-adjusted return acceptable?
✅ **Yes (PASS):**
- Total net profit: **35,793.4+ Tomans**
- Maximum capital loss (Max DD): **0.56%** (only 28 thousand Tomans loss against the 5% limit of the exchange).
- Ratio of profit to maximum drawdown: **1.28** (much better than the baseline of phase 21).

### 7. Does the strategy hold up against real transaction costs?
✅ **Yes (PASS):**
- Basic scenario (slippage 0.15% and fee 0.25/0.30%): **35,793 Tomans+ profit**
- High ticker fee scenario (0.40% ticker): **23,351 Tomans+ profit**
- Double slippage scenario (0.30% slippage): **9,592+ Tomans profit**  
Due to the appropriate width of the target (+4.5%) and the reduction of the number of transactions to 19, the exchange friction (72,587 Tomans) cannot destroy the profit margin.

### 8. Is performance stable between BTC, ETH and SOL?
❌ **Severe asymmetry (SOL Dominated):**
- Solana (SOL): 9 transactions Net profit **31,955.9+ Tomans** (89.3% of the total profit!).
- **Ethereum (ETH):** 4 transactions Net profit **8,551.5+ Tomans**.
- **Bitcoin (BTC):** 6 transactions Net loss **-4,713.9 Tomans** (33% win rate).  
Bitcoin rarely reaches the 4.5% target on a 24-hour period due to its lower beta, while Solana's volatility makes it the best platform for a structured strategy.

### 9. Is the duration of transactions consistent with the 72-hour deadline?
✅ **Yes (PASS):**
- Average trading time: **22.9 hours**.
- Minimum time: 4.8 hours Maximum time: 45.0 hours.
- Only 1 out of 19 transactions cleared the 72-hour limit (-6,076 Tomans); In 6 trades, the final sail mechanism (passive exit after 66 hours) saved the profit with the maker fee (+34,536 Tomans).

### 10. Does the -2.2% loss limit expose the account to unacceptable capital loss?
✅ **No (PASS):**  
The size of each position is 500,000 Tomans (10% of the total capital of 5 million). The gross loss of 2.2% along with fees and slippage limits the maximum loss of each stop to **-13,967 Tomans (equivalent to 0.28% of the total account)**. Even 5 stops in a row only reduces the account by 1.4%, which is perfectly in line with the 5% safe margin of the match.

---

## 2. Detailed ledger of 19 H1 transactions

| window | Symbol | Entry Time (UTC) | Departure Time (UTC) | The reason for leaving Net Profit (TMN) | Exit order type
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **W01** | Sol 2026-07-27 01:00 | 2026-07-27 20:45 | Passive final sail 103.5- | maker |
| **W02** | ETH | 2026-07-28 23:15 | 2026-07-30 20:15 | Passive final sail 2,173.2+ | maker |
| **W04** | BTC | 2026-08-03 19:15 | 2026-08-05 13:30 | Structural loss limit (-2.2%) | 13,967.0- | Ticker
| **W09** | BTC | 2026-08-18 14:00 | 2026-08-19 15:15 | Structural profit limit (+4.5%) | 19,693.8+ | maker |
| **W09** | Sol 2026-08-20 04:15 | 2026-08-20 20:15 | Passive final sail 8,314.2+ | maker |
| **W11** | BTC | 2026-08-24 10:45 | 2026-08-24 17:15 | End point stop 1,009.9-| maker |
| **W14** | ETH | 2026-09-03 10:15 | 2026-09-04 04:30 | Structural profit limit (+4.5%) | 19,693.7+ | maker |
| **W15** | ETH | 2026-09-05 11:30 | 2026-09-06 15:15 | End point stop 651.5+ | maker |
| **W16** | BTC | 2026-09-09 09:00 | 2026-09-11 02:00 | Mandatory clearing of the 72h border 6,076.5- | Ticker
| **W19** | Sol 2026-09-18 08:00 | 2026-09-18 15:45 | Structural profit limit (+4.5%) | 19,693.8+ | maker |
| **W19** | Sol 2026-09-18 20:30 | 2026-09-19 21:15 | Structural loss limit (-2.2%) | 13,967.0- | Ticker
| **W20** | Sol 2026-09-21 01:30 | 2026-09-21 09:30 | Structural profit limit (+4.5%) | 19,693.7+ | maker |
| **W20** | Sol 2026-09-21 13:00 | 2026-09-22 22:30 | Passive final sail 263.2+ | maker |
| **W21** | Sol 2026-09-24 21:30 | 2026-09-25 20:15 | Passive final sail 13,276.6+ | maker |
| **W22** | BTC | 2026-09-27 09:00 | 2026-09-28 20:15 | Passive final sail 10,612.7+ | maker |
| **W23** | ETH | 2026-09-29 10:30 | 2026-09-29 15:15 | Structural loss limit (-2.2%) | 13,967.0- | Ticker
| **W24** | Sol 2026-10-03 11:00 | 2026-10-04 11:00 | End point stop 1,248.2- | maker |
| **W28** | BTC | 2026-10-14 11:30 | 2026-10-15 02:15 | Structural loss limit (-2.2%) | 13,967.0- | Ticker
| **W28** | Sol 2026-10-15 22:00 | 2026-10-16 15:00 | Structural loss limit (-2.2%) | 13,967.0- | Ticker

---

## 3. H1 audit conclusion

H1 is microstructurally and financially valid; Its wide targets make it possible to survive candle shadow fluctuations and Wallex costs. However, due to the concentration of returns on SOL and the drop in profits in W16-W29, it cannot be considered a definitive guarantee on its own.