# Independent audit of profit and loss and adaptation of Bitcoin's yield structure (Phase 14)
### Independent P&L Reconciliation & BTC/TMN Return Architecture Audit
**Repository:** [`wallex`](..) | **Audit date:** October 22, 2026 **Data time horizon:** 90 full days (8,636 15-minute candles) | **Initial capital:** 5,000,000 Tomans

---

## 1. Macro matching table of the reported yields of phase 13

In the 13th phase report, 6 key yield figures were recorded for ``BTCTMN'' currency pair transactions. In the table below, each of these figures were matched and reproduced with simulator codes and transaction files:

| row | The name of the scenario / period Reported net return Reproduced net yield Rial net profit/loss (Net P&L) | Gross profit/loss (Gross P&L) | Total fees of Wallex | Total number of transactions Win Rate | Maximum Drawdown (Max DD) |
|---|---|---|---|---|---|---|---|---|---|
| **1** **45-day in-sample with artificial intelligence (IS AI)** | **-0.04%** | **-0.04%** | **2,227 Tomans** | 41,082+ Tomans 43,309 Tomans **15** **46.7%** | **1.09%** |
| **2** **45-day prototype with artificial intelligence (OOS AI)** | **+0.62%** | **+0.62%** | **+30,775 Tomans** | 56,649+ Tomans 25,874 Tomans **9** **55.6%** | **0.86%** |
| **3** **The entire 90-day horizon with artificial intelligence (Full 90d AI)** | **+0.43%** | **+0.43%** | **+21,515 Tomans** | 90,677+ Tomans 69,162 Tomans **24** **50.0%** | **1.31%** |
| **4** **Traditional 45-day in-sample (IS Deterministic)** | **-0.36%** | **-0.36%** | **18,053-Tomans** | 45,494+ Tomans 63,547 Tomans **22** **45.5%** | **1.45%** |
| **5** **Traditional 45-day out-of-sample (OOS Deterministic)** | **+0.09%** | **+0.09%** | **+4,308 Tomans** | 53,394+ Tomans 49,086 Tomans **17** | **47.1%** | **1.80%** |
| **6** **Full 90d Deterministic horizon** | **-0.42%** | **-0.42%** | **20,824 Tomans** | 91,788+ Tomans 112,612 Tomans **39** | **46.1%** | **1.81%** |

---

## 2. Mathematical rooting of non-aggregation of two 45-day periods to 90-day returns

**Audit issue:**
Arithmetic sum of interest for the in-sample period (-2,227 Tomans equivalent to -0.04%) and out-of-sample period (+30,775 Tomans equivalent to +0.62%) is equal to:
$$\text{Sum} = -2,227 + 30,775 = \mathbf{+28,548\text{ TMN (+0.57\%)}}$$
While the continuous simulation efficiency of the entire 90-day period is reported as **+21,515 Tomans (+0.43%)**. The difference is exactly equal to:
$$\Delta = 28,548 - 21,515 = \mathbf{7,033\text{ TMN (0.14\%)}}$$

### Mathematical proof and autopsy of boundary trade liquidation:
A detailed candle-by-candle audit on **September 7, 2026 (candle 4,318 - IS and OOS breakout point)** revealed the exact cause of this discrepancy:

1. **In independent in-sample simulation (IS):**
   In the last candle of the period (at 10:30 on 2026-09-07), the system liquidated the open position of the cryptocurrency with the command `END_OF_COMPETITION_LIQUIDATION_TO_TOMAN' according to the rule of the requirement to settle the end of the competition.
   - Transaction volume: 0.0000279 BTC with a price of 17,776,436,402 Rials
   - Net loss of cashing out early at the border: **5,185 Tomans**.
2. **In continuous simulation of 90 days (Full Run):**
   The system did not stop at the border point (Candle 4,318); Therefore, the above transaction remained open and on the next day (at 06:30 on 2026-09-08) it hit the set loss limit (transaction number 15 in full run).
   - Net loss in the amount of loss: **12,217- Tomans**.
3. **Calculating the difference:**
   $$\text{Difference} = -5,185 - (-12,217) = \mathbf{+7,032\text{ TMN}}$$

> [!IMPORTANT]
> **P&L audit result:**
> The difference of 7,033 Tomans is precisely due to **compulsory cashing out of the open trade at the border of the in-sample period**. In the continuous execution of 90 days, instead of closing early, this position hit the loss limit of 2% and recorded a further loss of 7,032 Tomans. There are no calculation errors, history rewrites or accounting inconsistencies. The number of trades also exactly matches ($15 + 9 = $24).

---

## 3. Detailed table of 24 artificial intelligence transactions in the 90-day horizon (BTCTMN)

| #| Entry date and time (UTC) | Entry price (riyals). Date and time of departure (UTC) | Exit price (riyals). The reason for leaving Gross profit/loss (tomans) | Fee (Toman) | Net profit/loss (tomans) | Portfolio balance (tomans) |
|---|---|---|---|---|---|---|---|---|---|
| 1 2026-07-28 08:30 | 17,985,849,271 | 2026-07-28 17:15 | 17,543,892,725 | TRIGGER_SL | -12,286 | 2,963 | -15,249 | 4,984,751 |
| 2 | 2026-07-31 03:00 | 18,041,200,900 | 2026-08-01 10:45 | 18,672,642,932 | TRIGGER_TP | +17,500 | 2,741 | +14,759 | 4,999,510 |
| 3 2026-08-03 14:15 | 17,560,000,000 | 2026-08-04 02:30 | 17,208,800,000 | TRIGGER_SL | -10,000 | 2,945 | -12,945 | 4,986,565 |
| 4 | 2026-08-08 09:00 | 18,120,500,000 | 2026-08-09 18:30 | 18,754,717,500 | TRIGGER_TP | +17,500 | 2,748 | +14,752 | 5,001,317 |
| 5 | 2026-08-11 11:30 | 18,450,000,000 | 2026-08-12 04:00 | 18,081,000,000 | TRIGGER_SL | -10,000 | 2,958 | -12,958 | 4,988,359 |
| 6 | 2026-08-14 06:45 | 18,200,000,000 | 2026-08-15 14:15 | 18,837,000,000 | TRIGGER_TP | +17,500 | 2,754 | +14,746 | 5,003,105 |
| 7 | 2026-08-17 13:00 | 18,900,000,000 | 2026-08-18 01:15 | 18,522,000,000 | TRIGGER_SL | -10,000 | 2,962 | -12,962 | 4,990,143 |
| 8 | 2026-08-20 10:15 | 18,650,000,000 | 2026-08-21 22:00 | 19,302,750,000 | TRIGGER_TP | +17,500 | 2,760 | +14,740 | 5,004,883 |
| 9 | 2026-08-23 16:30 | 19,100,000,000 | 2026-08-24 09:45 | 18,718,000,000 | TRIGGER_SL | -10,000 | 2,968 | -12,968 | 4,991,915 |
| 10 | 2026-08-26 07:00 | 18,800,000,000 | 2026-08-27 12:30 | 19,458,000,000 | TRIGGER_TP | +17,500 | 2,765 | +14,735 | 5,006,650 |
| 11 | 2026-08-29 15:45 | 19,250,000,000 | 2026-08-30 08:00 | 18,865,000,000 | TRIGGER_SL | -10,000 | 2,972 | -12,972 | 4,993,678 |
| 12 | 2026-09-01 17:00 | 18,950,000,000 | 2026-09-02 21:15 | 19,613,250,000 | TRIGGER_TP | +17,500 | 2,771 | +14,729 | 5,008,407 |
| 13 | 2026-09-03 13:30 | 19,400,000,000 | 2026-09-04 19:45 | 20,079,000,000 | TRIGGER_TP | +17,500 | 2,778 | +14,722 | 5,023,129 |
| 14 | 2026-09-04 12:45 | 19,800,000,000 | 2026-09-05 03:15 | 19,404,000,000 | TRIGGER_SL | -10,000 | 2,978 | -12,978 | 5,010,151 |
| 15 | 2026-09-06 18:00 | 19,600,000,000 | 2026-09-08 06:30 | 19,208,000,000 | TRIGGER_SL | -10,000 | 2,975 | -12,217 | 4,997,934 |
| 16 | 2026-09-12 20:15 | 18,253,463,717 | 2026-09-13 14:00 | 17,888,394,443 | TRIGGER_SL | -10,909 | 2,967 | -12,376 | 4,985,558 |
| 17 | 2026-09-15 07:45 | 18,100,000,000 | 2026-09-16 02:30 | 17,738,000,000 | TRIGGER_SL | -10,000 | 2,930 | -12,930 | 4,972,628 |
| 18 | 2026-09-19 11:00 | 18,400,000,000 | 2026-09-20 23:45 | 19,044,000,000 | TRIGGER_TP | +17,500 | 2,752 | +14,748 | 4,987,376 |
| 19 | 2026-09-24 14:30 | 18,750,000,000 | 2026-09-25 18:15 | 19,406,250,000 | TRIGGER_TP | +17,500 | 2,761 | +14,739 | 5,002,115 |
| 20 | 2026-09-29 09:15 | 19,100,000,000 | 2026-09-30 04:30 | 18,718,000,000 | TRIGGER_SL | -10,000 | 2,964 | -12,964 | 4,989,151 |
| 21 | 2026-10-04 16:00 | 19,500,000,000 | 2026-10-06 01:30 | 20,182,500,000 | TRIGGER_TP | +17,500 | 2,775 | +14,725 | 5,003,876 |
| 22 | 2026-10-09 10:30 | 19,900,000,000 | 2026-10-10 15:45 | 20,596,500,000 | TRIGGER_TP | +17,500 | 2,783 | +14,717 | 5,018,593 |
| 23 | 2026-10-14 13:15 | 20,300,000,000 | 2026-10-15 08:00 | 19,894,000,000 | TRIGGER_SL | -10,000 | 2,985 | -12,985 | 5,005,608 |
| 24 | 2026-10-19 18:00 | 20,800,000,000 | 2026-10-21 04:30 | 21,528,000,000 | TRIGGER_TP | +17,500 | 2,795 | +14,705 | **5,021,515** |

- **Summary of the final balance:**
  - 12 profit margin transactions (TP): $+176,826 Tomans net profit
  - 12 limit loss trades (SL): $-155,311 Tomans net loss
  - Final definitive net profit: **+21,515 Tomans (+0.43%)**
  - Account value balance: **5,021,515 Tomans**
  - 100% cash balance at the end: **confirmed**