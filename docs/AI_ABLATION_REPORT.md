# Audit report on the impact and study of artificial intelligence ablation (phase 12)
### AI Contribution & Ablation Study with Counterfactual Logging
**Repository:** [`wallex`](..) | **Artificial Intelligence Agent:** [`RegimeClassificationAgent`](../src/agents/regime_agent.py) | **Study symbols:** `BTCTMN`, `ETHTMN`, `SOLTMN`

---

## 1. The purpose and methodology of the ablation study (Ablation Methodology)

In algorithmic trading systems, this basic question is always raised:
> *Does adding an agentic AI layer really add mathematical and experimental value, or is it just a decorative layer?*

For an unbiased and evidence-based answer to this question, a detailed ablation study was conducted with a head-to-head comparison between the following two conditions:
1. **Test mode (AI-Assisted System):** System with combination of technical rules, artificial intelligence market regime and confidence threshold of at least 70% (`use_ai=True').
2. **Traditional Baseline Mode (Deterministic Baseline):** System with only classic technical rules (EMA intersection and RSI condition) without the participation of artificial intelligence (`use_ai=False').
3. Counterfactual Logging: Recording one by one the points where the traditional system wanted to enter the transaction, but the artificial intelligence vetoed it, and analyzing the fate of the price after the veto.

---

## 2. Flow chart of agent decision making and safety gate

```mermaid
flowchart TD
    A["Technical input signal (EMA20 > EMA50)"] --> B["Calculation of microstructural features (ATR, Spread, VolRatio, RSI)"]
    B --> C["AI Regime Agent"]
    
    C --> D{"Regime detection and confidence level"}
    D -->|"BULLISH_TREND & Confidence >= 70%"| E["Confirmation of entry signal (Approved)"]
    D -->|"CALM_RANGE (range fluctuating market)"| F["Artificial intelligence veto: maintaining liquidity and not trading"]
    D -->|"BEARISH_TREND / PANIC"| G["Emergency exit order"]
    D -->|"confidence < 70%"| H[""]
    
    E --> I["Risk Engine"]
    F --> J["Registration in Counterfactual Log"]
    H --> J
```

---

## 3. Statistical results of head-to-head comparison (Head-to-Head Empirical Metrics)

### 3.1. At the level of the Bitcoin symbol (BTCTMN)
| performance index Traditional mode without artificial intelligence (Deterministic). Artificial intelligence mode (AI-Assisted) | The difference and achievement of artificial intelligence
|---|---|---|---|
| **Net Return** | +0.67% (+33,492 t) | **+1.19% (+59,609 tons)** | **+78% increase in final net profit** |
| **Maximum capital loss (Max Drawdown)** | 1.79% **0.50%** | **72% decrease in portfolio drawdown** |
| **Number of closed transactions** | 13 transactions **7 deals** | **46% reduction in erosion transactions** |
| **Fees paid to the exchange** | 37,398 Tomans **19,942 Tomans** | **Saving 17,456 Tomans in fees** |
| **Win Rate** | 53.85% **71.43%** | **+17.6% improvement in signal accuracy** |
| **Financial turnover (Turnover)** | 2.61x | **1.42x** | Optimal capital management

### 3.2. At the joint polynomial portfolio level (BTCTMN + ETHTMN + SOLTMN)
| Total portfolio index Portfolio without AI (Deterministic) | Portfolio with artificial intelligence (AI-Assisted) | Added value of artificial intelligence
|---|---|---|---|
| **Maximum capital loss (Max DD)** | **5.70% (🛑 Violation of the 5% Hackathon ceiling)** | **3.49% (Fully compliant with the rules)** | **Save the account from blocking and deletion** |
| **Total deducted fees** | 141,334 Tomans **121,320 Tomans** | **Reduction of 20,014 Tomans in fee** |
| **Number of vetoed signals** | 0 items **643 false entry signals were vetoed** | Avoid trading in erosion waves
| **system emergency stop** | **🛑 Activated (Breach of 5%)** | ** ✅ did not activate (safe and stable) ** | Maintaining operational stability

---

## 4. Sampling Counterfactual Case Studies

Analysis of real samples recorded in [`research/phase12_simulation_results.json`](../research/phase12_simulation_results.json) shows:

1. **Case 1: Avoid buying at the swing ceiling of the range in the symbol BTCTMN:**
   - *Traditional signal:* Cross-sectional bullish intersection of 20 and 50 averages due to the short-term jump of 2 candles. The traditional system issued a buy signal at the price of 21,150,000,000 Rials.
   - *AI Agent Detection:* The market regime was classified as ``CALM_RANGE'' with weak volatility (ATR less than 0.8%) and veto signal.
   - *Counterfactual Outcome:* In the next 4 candles, the price fell by 1.2% and the traditional system registered a loss of 11,500 Tomans with the activation of the 2% loss limit and 0.30% ticker fee deduction. AI veto prevented this loss.

2. **Case 2: Veto of false waves of altcoins in macro collapse:**
   - In the symbols `ETHTMN' and `SOLTMN', on October 10 to 12, the market was in a bearish erosion regime. Every small reversal wave would fool the traditional systems and issue an entry signal.
   - Artificial intelligence vetoed a total of **643 entry signals**, which analysis shows that more than 74% of them, if entered, would have led to commission losses or loss limits.

---

## 5. Ablation audit conclusion

The empirical evidence of this test proves that:
1. Artificial intelligence in this system is not a marketing concept, but an Anti-Churn Mathematical Filter.
2. The main value of artificial intelligence in high-fee markets lies in "not trading in bad conditions".
3. Separation of range-eroding regimes (`CALM_RANGE') from stable trending regimes (`BULLISH_TREND') has directly increased the win rate to 17.6% and prevented hackathon from violating the 5% drawdown limit.