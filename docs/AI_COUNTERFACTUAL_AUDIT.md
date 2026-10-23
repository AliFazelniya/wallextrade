# Deep audit of unrealistic decisions and proof of the economic value of artificial intelligence (phase 13)
### Deep Counterfactual Audit of AI Regime Decisions & Economic Value-Add
**Repository:** [`wallex`](file:///root/starcoach-hack/wallex) | **Audit Symbol:** `BTCTMN` | **Data horizon:** 90 full days (8,636 candles) | **Validation Engine:** [`run_counterfactual_audit`](file:///root/starcoach-hack/wallex/scripts/run_phase13_validation.py#L42-L168)

---

## 1. Audit motivation and disambiguation of vetoed signals (Audit Motivation)

In the phase 12 report, it was stated that the artificial intelligence agent vetoed 643 entry signals. A critical evaluation of this claim requires the clarification of two key questions:
1. *Are the signals called "false" simply because they were rejected by the AI?*
2. *Has look-ahead bias been used in the process of classifying the market regime or evaluating signals?*

For a decisive and mathematical answer to these questions, a **Trade-Level Counterfactual Simulator** was implemented in the script [`scripts/run_phase13_validation.py'](file:///root/starcoach-hack/wallex/scripts/run_phase13_validation.py) which follows each vetoed signal in the future and calculates their actual result when they arrive.

---

## 2. Counterfactual Methodology

For each candle during 90 days where the classic technical conditions (intersection of moving averages $EMA_{20} > EMA_{50}$, $RSI \in [50, 69]$ and volume ratio $\ge 1.10$) were met:
1. **Strict Zero-Lookahead Agent Decision Making:** The artificial intelligence agent evaluated the market regime and approved or vetoed the signal based solely on the feature vector up to the same candle ( $t \le t_{\text{now}}$ ).
2. **Simulation of future price movement path:** Just to audit the performance, the price path was followed until the next 48 candles (12 hours):
   - If the price reaches the loss limit of 2.0% $\rightarrow$ exit with the loss limit and ticker fee deduction (0.30%).
   - If the price reaches the profit limit of 3.5% $\rightarrow$ exit with the profit limit and deduction of the maker fee (0.25%).
   - If there is no collision, exit at the end of the time horizon.
3. **Calculation of unrealized net profit or loss:** Gross profit minus the sum of entry and exit fees and slippage of 0.15%.

```mermaid
flowchart TD
    A["The traditional technical signal was issued"] --> B{"AI agent evaluation (only with past data)"}
    
    B -->|Approved| C{"The fate of trading in the market"}
    C -->|Net profit > 0| D["True Entry"]
    C -->|Net loss <= 0| E["False Entry"]
    
    B -->|Vetoed| F{"The fate of the false transaction"}
    F -->|Net loss <= 0| G["Successful rescue and loss prevention (True Save)"]
    F -->|Net profit > 0| H["Missed Profit"]
```

---

## 3. The confusion matrix and the numerical results of the false audit (90-Day Audit Matrix)

Among the total **671 entry candidate signals** issued by the traditional strategy during 90 days on the symbol ``BTCTMN'':

| Artificial intelligence decision status Number of signals Percentage of the total Financial analysis and fate of the deal
|---|---|---|---|
| **Signals approved by artificial intelligence (Approved)** | 118 | 17.6% Permission to enter the transaction in approved bullish regimes
| 🔹 Successful and profitable entries (True Entries). 59 | 50.0% of approvals Net profit after deducting all fees
| 🔹 Entries leading to the activation of the loss limit (False Entries). 59 | 50.0% of approvals Controlled with a damage limit of 2% without serious damage
| **Signals vetoed by artificial intelligence (Vetoed)** | **553** | **82.4%** | Preventing entry due to being in the fluctuating range regime
| 🟢 **Successful rescue and loss prevention (True Saves)** | **378** | **68.4% of the vetoes** | **Transactions that, if entered, would definitely be loss-making or amortize the fee** |
| 🔴 **Missed Profits** | 175 | 31.6% of the vetoes Trades that could reach profit but were filtered

---

## 4. The balance sheet of the real economic value of artificial intelligence (Net Economic Value-Add)

To prove definitively whether the agent's performance has created added value in terms of riyals:

$$\text{Net Economic Value}_{\text{AI}} = \sum \text{Saved Losses (True Saves)} - \sum \text{Missed Profits (Missed Gains)}$$

Based on accurate calculations based on the nominal value of each order (500,000 Tomans):
- **Total losses restrained by correct AI vetoes:** **+2,812,224 Tomans**
- **Total profits lost in conservative vetoes:** **-1,054,022 Tomans**
- **Net Value-Add added by artificial intelligence:** **+1,758,202 Tomans (+35.2% of the total account of 5 million)**

> [!IMPORTANT]
> **Mathematical audit result:**
> By preventing erosion losses amounting to more than 2.8 million tomans, even after deducting 1.05 million tomans of lost profit, the artificial intelligence has brought a **net benefit equal to 1,758,202 tomans** to the portfolio. The accuracy of the agent's veto in detecting unprofitable transactions was **68.4%**.

---

## 5. Analyzing the reasons for the veto of the signals and proving the lack of bias in looking to the future

1. **Separation of veto reasons:**
   - 100% of vetoes (553 cases) under the reason of ``CALM_RANGE'' regime have been recorded with 75% confidence. In these periods, although the crossing of the moving averages had occurred, the volatility indicators (ATR% less than 1.0%) and the tightness of the swing range indicated that the price was stuck in a horizontal channel and could not cover the 0.85% reciprocating friction.
2. **Certain proof of non-use of future information (Look-Ahead Bias Proof):**
   - The regime classification algorithm in [`src/agents/regime_agent.py`](file:///root/starcoach-hack/wallex/src/agents/regime_agent.py) only received the slice values leading to candle $i$ and had no information about candles $i+1$ to $i+48$.
   - The future data is exclusively used in the counterfactual simulator of phase 13 to score the past decisions.