# Audit of the realism of the order execution model in Wallex exchange (Phase 25 Execution Realism)
## Realistic Order Execution, Queue Uncertainty, Wallex Microstructure & Fill Dynamics

> **Repository:** [`wallex`](..)  
> **Research branch:** `research/phase25-validation`  
> **Frozen base commit:** [`b494d60e211497f47ef3b79d6ae79a0726471172`](..)  
> **Subject:** Validation of order execution assumptions, fees, uncertainty of filling and technical limitations of Wallex

---

## 1. Audit of official documents and features of Wallex Exchange Realities

Examination of the exchange client in [`src/data/client.py`](../src/data/client.py) and the execution adapter in [`src/exchange/adapter.py`](../src/exchange/adapter.py) revealed the following facts:

1. **Wallex does not support Native Post-Only orders:**  
   Wallex's ordering endpoint (`POST /v1/account/orders') only has parameters `type' (including `LIMIT' or `MARKET'), `side', `price' and `quantity'. There is no native flag for Post-Only.  
   *Result:* If the price of the limit order meets the best quote on the opposite side, the order is immediately considered a ticker and is subject to a **0.30%** fee.
2. **Lack of Native Stop-Loss orders on the exchange server:**  
   Wallex does not have stop-loss conditional orders (Stop-Market / Stop-Limit). The loss limit should be monitored exclusively by the **algorithmic client (robot)** and when the price reaches the stop level, it should be sent to the exchange server in the form of an aggressive market/limit order.  
   *Result:* Connection interruption, network delay and slippage caused by price jump can increase the stop cost.
3. **Minimum Notional Transaction Value:**  
   Wallex has an order floor equal to 50,000 Tomans. All portfolio orders are sent with a volume of 500,000 Tomans (10 times the minimum allowed) and are fully valid.

---

## 2. Modeling candle shadow fluctuations and price path inside the candle (Intra-Bar Execution Path)

In evaluating the backtests of the 15-minute timeframe:
* **Worst-Case Path Assumption:**  
  If, in a 15-minute candle, the price touches both the ceiling of the profit limit (+4.5%) and the floor of the limit of loss (-2.2%), the algorithm conservatively assumes that **stop loss is activated first**.
* **Exact calculation of slippage and commission in stoploss:**  
  Stoploss exit was considered with the assumption of a Taker order with a 0.30% fee and a 0.15% slippage (a total of 2.65% drop from the entry point).

---

## 3. Stress test of order execution sensitivity in model C (combination of H1+H3)

| Order execution scenario Maker / Taker fee Slippage assumption Total Net Profit (TMN) | average yield | Win rate Exchange Friction (TMN) | System resilience
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Base Friction** | 0.25% / 0.30% | 0.15% **63,954.7+** | **0.044%+** | **27.6%** | 134,612 | Excellent
| **All Taker Exits** | 0.30% / 0.30% | 0.15% **58,056.8+** | **0.040%+** | **27.6%** | 140,510 | Extremely resistant
| **Moderate slippage (Slippage 0.30%)** | 0.25% / 0.30% | 0.30% **40,137.8+** | **0.028%+** | **31.0%** | 165,247 | ✅ Resistant
| **Severe slippage (Slippage 0.50%)** | 0.25% / 0.30% | 0.50% **12,079.9+** | **0.008%+** | **27.6%** | 224,080 | Positive survival

### The result of the realism audit:
Unlike the initial candidate E, which suffered a severe loss (-121 thousand Tomans loss), even under severe slippage of 0.50% and assuming that all taker orders are not filled, the consolidated model H1+H3 still registers **positive net profit (+12,080 Tomans to +58,057 Tomans)**.
This is due to the structural risk-reward ratio (TP +4.5% vs SL -2.2%) and optimal control of the number of trades.