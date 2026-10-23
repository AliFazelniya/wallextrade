# Controlled study of artificial intelligence effect separation in H1+H3 portfolio (Phase 25 AI Ablation)
## Three-Way AI Ablation Study: Deterministic Baseline vs Phase 23 Agent vs Cost-Sensitive AI

> **Repository:** [`wallex`](..)  
> **Research branch:** `research/phase25-validation`  
> **Frozen base commit:** [`b494d60e211497f47ef3b79d6ae79a0726471172`](..)  
> **Test environment:** Same conditions in 29 competition windows ($N = $29) with execution of candle shadow and official exchange fees

---

## 1. Table of direct comparison of three artificial intelligence separation configurations (Ablation Matrix)

| Evaluation configuration How to participate in artificial intelligence Total Net Profit (TMN) | Average efficiency of 72 hours Win rate Number of transactions T statistic ($t$) | Delta compared to deterministic | Exchange Friction (TMN) |
|---|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **1. Pure Deterministic (No AI)** | Zero (H1+H3 structural rules only) | **63,954.7+** | **0.044%+** | **27.6%** | 35 | **0.65+** | Basis | 134,612 |
| **2. Phase 23 agent (Regime Agent)** | Regime classification with strict Boolean conditions **26,631.6+** | 0.018%+ | 24.1% 32 | 0.27+ | **37,323- TMN (destruction)** | 123,029 |
| **3. Cost-sensitive probabilistic estimator The model for estimating the probability of profit and profit margin **60,829.2+** | 0.042%+ | 27.6% 34 | 0.62+ | **TMN-3,125** | 130,126 |

---

## 2. Scientific rooting of profit destruction by Phase 23 agent (Regime Agent Failure Analysis)

Why did the artificial intelligence agent reduce the profit of phase 23 by more than **37,000 tomans**?
1. Rigid Boolean Thresholds:  
   The previous agent code in [`src/agents/regime_agent.py`](../src/agents/regime_agent.py#L79) defined the ascending regime condition exclusively as:```python
   if f.ema_spread_pct > 0.4 and 52 <= f.rsi_14 <= 68 and f.vol_ratio >= 1.15:
   ```2. **Veto of gold transactions at trend peaks:**  
   On the strongest bullish days of the market (such as the W09 and W22 windows), on the breakout breakout candles, the RSI indicator reached 69.5 or the volume ratio reached 1.12 for several candles due to the strength of the price acceleration.  
   The previous agent misclassified these conditions as "quiet suffering" or "risky buying saturation" and blocked entry into the market's most profitable 4.5%+ waves!
3. **Asymmetry of cost and reward:**  
   The previous agent reduced the profit by 37 thousand tomans by removing 3 big winning trades under the pretext of risk, while the friction fee was reduced by only 11 thousand tomans.

---

## 3. AI audit conclusion and final solution for the competition

> [!IMPORTANT]
> ### Unvarnished Truth:
> **The pure deterministic model performs better than the phase 23 regime factor in this structure.**  
> To satisfy the mandatory race condition (meaningful contribution of AI without degrading system efficiency), AI should not be used as a rigid Boolean elimination filter.  
> **Correct role of artificial intelligence agent:**
> - Use as **probability evaluator and calculator of profit margin compared to fee (Cost-Sensitive Hurdle Rate)**
> - Arbitrage in case of simultaneous conflict of signals (choice between SOL and ETH)
> - Floating adjustment of order volume (Position Sizing) instead of complete veto of high quality positions.