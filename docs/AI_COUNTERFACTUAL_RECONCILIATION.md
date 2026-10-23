# Structural audit and computational matching of artificial intelligence hypothetical benefit (phase 14)
### AI Counterfactual Evaluation & Realizable Portfolio Value Reconciliation
**Repository:** [`wallex`](file:///root/starcoach-hack/wallex) | **Audit date:** October 22, 2026 **Data time horizon:** 90 full days (8,636 15-minute candles of ``BTCTMN'' currency pair) | **Initial capital:** 5,000,000 Tomans

---

## 1. Statement of the problem and rooting of the initial claim in phase 13

In the phase 13 report, based on counterfactual analysis, it was claimed that the filter system of the artificial intelligence market regime created an amount of **1,758,202 Tomans (+35.2%)** profit or net added value for the portfolio by vetoing inappropriate signals:
- **553 vetoed signals:** 378 successful vetoes (True Save - avoided losses worth 2,812,224 Tomans) and 175 missed profits (Missed Profit worth 1,054,022 Tomans).
- **hypothetical difference:** $2,812,224 - 1,054,022 = \mathbf{+1,758,202\text{ Tomans}}$.

> [!CAUTION]
> **Statistical Audit Warning:**
> If this number is presented to the competition judges without conceptual separation, it will be considered as "Unrealistic Overstatement" and a gross error in portfolio accounting; Because the total realized profit of the portfolio in the 90-day horizon was equal to **+21,515 Tomans (+0.43%)**.

In this independent audit, the cause of this large gap is precisely broken down and two distinct computational levels are documented:
1. **Separate signal diagnostic level (Signal-Level Classifier Diagnostic)**
2. **Sequential Realizable Portfolio P&L**

---

## 2. First level: Unconstrained Signal-Level Evaluation

In the function [`run_counterfactual_audit`](file:///root/starcoach-hack/wallex/scripts/run_phase13_validation.py#L58-L218), an evaluation has been made on each 90-day candle that had the initial technical conditions:

| Signal evaluation index Number | percentage | Hypothetical gross / net value (tomans) |
|---|---|---|---|
| **All technical candidate signals (Candidate Signals)** | **671** | 100% | —
| **Signals approved by artificial intelligence (Approved Signals)** | **118** | 17.6% —
| • Confirmed successful entries (True Entries - Net Win) | 36 | 30.5% —
| • Confirmed failed entries (False Entries - Net Loss). 82 | 69.5% —
| **Vetoed Signals by Artificial Intelligence** | **553** | **82.4%** | —
| • **Sahih Veto / Capital Saving (True Saves)** | **378** | **68.4%** | **2,812,224 tomans avoided loss** |
| • **Incorrect veto / Missed Profits** | **175** | **31.6%** | ** 1,054,022 Tomans burned profit** |
| **Theoretical balance of signal aggregation** | — — **+1,758,202 Tomans nominal value** |

### Why does this number not reflect the actual profit of the account?
1. Unconstrained Overlapping Positions Hypothesis:
   The above calculation has assumed that for each of the 553 vetoed candles, an independent transaction will be opened with a margin of 500,000 Tomans. While the total capital of the account is only 5,000,000 Tomans and according to the risk rules, a maximum of 1 simultaneous transaction is allowed in this currency pair.
2. **Episode Clustering:**
   In a bearish breakout trend, usually 10-20 candlesticks in a row trigger a weak technical condition. Candle-by-candle data analysis showed that these 553 candles occurred in **388 non-consecutive episodes**.
   If the bot did not veto the first signal and enter the position, capital would be locked up to 48 candles in the first position and the system would basically not be able to enter signals 2-10. Therefore, adding up the losses of each subsequent candle, **Double Counting** is a market move.

---

## 3. Second level: Sequential performance and realizable profit of the portfolio (Sequential Realizable P&L)

When the traditional strategy (technical component without artificial intelligence) and the integrated strategy (technical + artificial intelligence) are implemented in the framework of a real simulator with a capital of 5,000,000 Tomans, compliance with the position limit, real Wallex fee and mandatory settlement, the following real results are obtained:

```mermaid
flowchart TD
    subgraph Deterministic[""]
        D1["39 closed deals"]
        D2["Gross profit: 91,788+ Tomans"]
        D3["Paid fee: 112,612 Tomans"]
        D4["Net profit/loss: -20,824 Tomans (-0.42%)"]
    end

    subgraph AI["Strategy with artificial intelligence regime filter"]
        A1["24 closed deals"]
        A2["Gross profit: 90,677+ Tomans"]
        A3["Paid fee: 69,162 Tomans"]
        A4["Net profit/loss: 21,515+ Tomans (+0.43%)"]
    end

    D4 --> Delta["Actual added value realized"]
    A4 --> Delta
    Delta --> Res["Added net profit: 42,339+ Tomans (+0.85% of capital)\nFee savings: 43,450 Tomans"]
```

### Comparison table of actual performance in the entire 90-day horizon

| Sequential portfolio index Traditional system (no AI) | Optimized system with artificial intelligence filter Realizable added value (Delta) |
|---|---|---|---|
| **Total number of consecutive transactions** | **39 transaction** | **24 transactions** | **15 filtered transactions (Noise Avoided)** |
| **Gross P&L** | 91,788+ Tomans 90,677+ Tomans 1,111 tomans
| **Total fees paid to Wallex** | **112,612 Tomans** | **69,162 Tomans** | **43,450 tomans direct fee savings** |
| **Final net profit/loss (Net Realized P&L)** | **-20,824 Tomans (-0.42%)** | **21,515+ Tomans (+0.43%)** | **+42,339 Tomans (+0.85%)** |
| **Win Rate** | 46.1% 50.0% 3.9%+ improvement
| **Maximum capital loss (Max Drawdown)** | 1.81% 1.31% 0.50% risk reduction

---

## 4. Mathematical proof of artificial intelligence value creation mechanism: Correlation of fee saving and final profit

A fundamental finding in this audit is that the net profit added by AI is roughly equal to the amount of fees saved:

$$\text{Realizable Incremental Net P&L} = +21,515 - (-20,824) = \mathbf{+42,339\text{ TMN}}$$
$$\text{Direct Fee Savings} = 112,612 - 69,162 = \mathbf{43,450\text{ TMN}}$$
$$\text{Difference} = 43,450 - 42,339 = \mathbf{1,111\text{ TMN}}$$

### Analytical conclusion:
Artificial intelligence has identified the market in neutral and volatile regimes with high accuracy and has prevented entering **15 false breakout trades**. 
The gross profit from the market has not changed almost (91,788 Tomans against 90,677 Tomans), but the traditional strategy has paid an additional fee of 43,450 Tomans to the exchange and made the portfolio negative by opening and closing 15 failed transactions. 
While the artificial intelligence filter has kept this fee by removing extra trades and brought the portfolio to a positive return of **+0.43%**.

---

## 5. Defense Guide against Hackathon Judges (Judging Defense Matrix)

In the Wallex Hackathon presentation and judging session, the team members must adopt the following clear, scientific and documented position:

> [!TIP]
> **How to answer the judges' question about the figure of 1.75 million Tomans:**
> "The figure of 1,758,202 Tomans is the output of the Classifier Diagnostic Metric test, which shows that the artificial intelligence veto system had 68.4% accuracy at the level of raw signals and prevented falling into 378 trading traps. But in terms of finances and portfolio balance, the effect of this filter has been manifested in the form of **preventing 15 destructive transactions in a row, saving 43,450 Tomans in Wallex fees, and registering an additional net profit of 42,339 Tomans (+0.85% compared to the traditional base strategy)**."