# Phase 25 Shadow Execution Report
## Real-Time Order Book Liquidity, Spread Dynamics & Live Shadow Observation

> **Repository:** [`wallex`](file:///root/starcoach-hack/wallex)  
> **Research branch:** `research/phase25-validation`  
> **Frozen base commit:** [`b494d60e211497f47ef3b79d6ae79a0726471172`](file:///root/starcoach-hack/wallex)  
> **Online endpoints:** `https://api.wallex.ir/v1/depth` and `https://api.wallex.ir/v1/markets`  
> **Trading mode:** `SHADOW' (complete simulation without sending orders to the exchange)  
> **Live execution authorized:** `live_execution_authorized = False` (completely blocked)

---

## 1. Live order book depth query and liquidity of Wallex exchange (Live Order Book Depth)

On October 22, 2026 (20:19 local time), the online status of the order book for 3 assets was reviewed:

| Property (Symbol) | Best Bid The best sales quotation (Best Ask) | Exchange current spread Liquidity of the top 5 purchase quotes Liquidity of the top 5 sales quotes The ratio of our order size (500k) to liquidity
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **BTCTMN** | 22,080,000,001 | 22,104,782,304 | **0.112%** | **191.4 million Tomans** | **15,663 million Tomans** | **0.26% (very insignificant)** |
| **ETHTMN** | 645,244,446 645,815,998 | **0.089%** | **215.0 million Tomans** | **7,365 million Tomans** | **0.23% (very insignificant)** |
| **SOLTMN** | 28,170,246 | 28,200,000 | **0.106%** | **167.4 million Tomans** | **340.6 million tomans** | **0.30% (very insignificant)** |

### Key findings of market microstructure:
1. **Actual spread of the market is very favorable:** The spread of all three currency pairs is between **0.089% and 0.112%**, which is much lower than the ceiling of the robot's spread filter (0.18%).
2. **The depth of the market is enough to attract an order of 500 thousand Tomans:** In all three markets, the liquidity of the top 5 levels of orders is more than **167 million Tomans**; Our order of 500,000 Tomans consumes less than 0.3% of current liquidity and will practically have a price impact (Market Impact) close to zero.

---

## 2. The results of the online shadow session (Live Shadow Session Events)

The robot was connected to the real data in ``SHADOW'' mode and performed 5 live cycles:
* **Price and depth queries:** 100% successful with no network errors or timeouts.
* **Evaluation of Signals:** During the monitored hours, Bitcoin was in a tight swing range and trading volume was below the breakout threshold.
* **System behavior:** Based on its intelligent design, the robot did not issue any raw signal and remained **100% in safe cash mode (Cash Buffer)**.
* **Event logging:** All web service responses and decisions were saved in [`logs/shadow_session_phase23.json`](file:///root/starcoach-hack/wallex/logs/shadow_session_phase23.json).

---

## 3. Transparent Operational Disclosure

> [!WARNING]
> ### Forward Validation Status: **Explicitly Unfinished**
> According to the user's explicit instructions, no false claims are made about completing the continuous 72-hour shadow test.  
> The duration of real live monitoring in this session has been limited to **several consecutive online cycles**.  
> Completion of a full 72-hour shadow test requires the robot to run stably for 3 business days prior to the official start of the competition, and until then, the upcoming validation is classified as **in progress and unproven**.