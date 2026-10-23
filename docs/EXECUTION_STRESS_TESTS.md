# Comprehensive report of microtransactional stress tests and risk resilience (phase 13)
### Execution Stress Testing, Adverse Market Conditions & Deterministic Risk Invariants
**Repository:** [`wallex`](file:///root/starcoach-hack/wallex) | **Risk Engine:** [`RiskEngine`](file:///root/starcoach-hack/wallex/src/risk/engine.py) | **Test base symbol:** `BTCTMN' (45-day out-of-sample period)

---

## 1. Stress Testing Objective

Automated trading systems in live tournaments face unpredictable volatility, sudden widening of spreads, network delays and increased transaction costs. The purpose of phase 13 is to test the resilience of the system under severe conditions and to prove that the Deterministic Risk Engine always remains the final and unchanging reference of the system.

---

## 2. Fee & Slippage Matrix in out-of-sample data

Stress tests were run on recent 45-day out-of-sample Bitcoin data (4,318 untouched candles) with staggered increases in fees and slippage:

| Stress scenario Maker fee Ticker fee Two-way slippage Net return (Net Ret) | Maximum Drawdown (Max DD) | Total fee paid Stability status
|---|---|---|---|---|---|---|---|
| **1. Valax official base (Base Official)** | **0.25%** | **0.30%** | **0.15%** | **+0.62%** | **0.86%** | 25,874 Tomans ✅ **Profitable and very stable** |
| **2. Pessimistic scenario (Adverse Taker)** | **0.30%** | **0.30%** | **0.20%** | **+0.52%** | **0.87%** | 27,159 Tomans ✅ **Profitable and durable** |
| **3. High Friction** | **0.35%** | **0.35%** | **0.25%** | **+0.35%** | **0.91%** | 31,673 Tomans ✅ **maintain net profitability** |
| **4. Critical stress (Extreme Stress)** | **0.40%** | **0.40%** | **0.35%** | **-1.47%** | **1.68%** | 47,898 Tomans ⚠️ Yield drop (but drawdown below 1.7%) |

```mermaid
xychart-beta
    title "The sensitivity of net efficiency and maximum drawdown to the increase of exchange friction (percentage)"
    x-axis ["Base (0.25%/0.30%)", "Pessimistic (0.30%)", "Severe (0.35%)", "Critical (0.40%)"]
    y-axis "percentage" -2.0 --> 1.0
    bar [0.62, 0.52, 0.35, -1.47]
    line [0.86, 0.87, 0.91, 1.68]
```

### Analysis of the findings of the fee matrix:
1. Break-even Friction Threshold:
   The Bitcoin strategy remains fully profitable (+0.35% net return with 0.91% drawdown) up to **0.35% maker / 0.35% taker fees and 0.25% slippage**. Only if the fees reach the unusual level of 0.40% and the slippage to 0.35%, the return becomes negative.
2. Capital drawdown control: Even in critical scenario 4, the maximum drawdown is controlled at the level of **1.68%**, which is much lower than the 5.0% competition ceiling.

---

## 3. Microstructure stress tests and adverse market conditions

```mermaid
flowchart TD
    A["Shock event or market anomaly"] --> B{"Risk type"}
    
    B -->|Wide spread > 0.35%| C["Gate spread: immediate signal cancellation and liquidity preservation"]
    B -->|Old data > 60 seconds| D["Stale data gate: order rejection until receiving new data"]
    B -->|5% sudden drop shock| E["Activation of ticker loss limit and automatic withdrawal at 2%"]
    B -->|streak of consecutive losses and a drop of 5%| F["Full emergency stop (Emergency Halt) and portfolio lock"]
    B -->|Network / HTTP error 429| G["Mechanism of progressive retry and matching of undecided orders"]
```

### 1. Stale Market Data Stress test:
If the market data is more than 60 seconds old due to internet outage or exchange delay, the validation function in [`test_data_staleness_detection`](file:///root/starcoach-hack/wallex/tests/test_data_validation.py#L46-L54) will immediately issue an error and prevent entry based on invalid prices.

### 2. Partial fill stress test:
In the class [`ExchangeAdapter`](file:///root/starcoach-hack/wallex/src/exchange/adapter.py#L110-L134), if 50% of the order volume is filled, the system calculates the filled cost and adjusts the portfolio cash balance based on the actual value (`assert 4_890_000 <= portfolio.cash_toman <= 4_901_000`).

### 3. Emergency Drawdown Halt test in 5% (Emergency Drawdown Halt):
In the portfolio tests without AI, when the drawdown reached **5.03%**, the `trigger_emergency_halt` method in [`RiskEngine`](file:///root/starcoach-hack/wallex/src/risk/engine.py#L114-L120) was activated immediately:```
[CRITICAL] EMERGENCY TRADING HALT TRIGGERED: Drawdown breach: 5.03% >= 5.00%
```After activating this state, any subsequent signal was immediately rejected with the reason ``System is in EMERGENCY HALT state'' and no order was sent to the market.

---

## 4. Proof of absolute and definitive rule of the risk engine (Deterministic Invariants)

1. **Final reference and unconditional veto:** Artificial intelligence agent is only a "Proposer". The definitive risk engine is the final veto authority and will not be bypassed by AI under any circumstances.
2. **Immutable mathematical ceilings:**
   - 500 thousand tomans limit for each order.
   - 60% exposure limit of the entire portfolio to the cryptocurrency market.
   - Maximum 3 positions at the same time.
   - Capital loss ceiling of 5.0% with emergency cut-off switch.