# Audited shadow test report on the live data of Wallex exchange (Audited Shadow Test Report)

This document documents observations, agent decisions, risk engine checks, and logging status in Shadow Mode on the Wallex live market.

---

## 1. Strict separation of data inquiry from order submission (Zero Live Orders)

> [!IMPORTANT]
> During the entire shadow testing process, **no real orders were sent to Wallex exchange**.
> - Orderbook queries (`/v1/depth`) and history candles (`/v1/udf/history`) are all **Read-Only**.
> - The `ExchangeAdapter` module is hardware locked with `live_execution_authorized=False` flag and has vetoed any live order submission.

---

## 2. Test specifications and metadata in the shadow
- **Execution date and time:** October 22, 2026 (10:41:45 to 10:42:31 UTC time)
- **Environment:** Server with Python 3.12 and direct connection to Wallex API
- **Number of registered cycles:** 3 complete cycles on 5 main cashable symbols
- **Number of log records recorded in this run:** 15 new audit logs in [`logs/trading_decisions.jsonl`](file:///root/starcoach-hack/wallex/logs/trading_decisions.jsonl)
- **Nominal portfolio capital:** 5,000,000 Tomans

---

## 3. Table of life cycle observations and decisions

| Symbol | Live Price (TMN) | Spread order book AI detected regime | Confidence AI | Strategy decision Risk situation Live order? |
|---|---|---|---|---|---|---|---|
| **USDTTMN** | 271,036 | 0.017% | CALM_RANGE | 75% HOLD | ⛔ Hold | ❌ No (Simulation) |
| **PEPETMN** | 1.1 0.080% | CALM_RANGE | 75% HOLD | ⛔ Hold | ❌ No (Simulation) |
| **BTCTMN** | 22,265,343,087 | 0.049% | CALM_RANGE | 75% HOLD | ⛔ Hold | ❌ No (Simulation) |
| **PUMPTMN** | 1,304 | 0.150% | CALM_RANGE | 75% HOLD | ⛔ Hold | ❌ No (Simulation) |
| **ETHTMN** | 653,000,005 | 0.099% | CALM_RANGE | 75% HOLD | ⛔ Hold | ❌ No (Simulation) |

---

## 4. Audit results and test limitations

> [!WARNING]
> Running 3 test cycles in the shadow is just a **system integrity and performance evaluation test (Smoke Test)** to prove the health of communication lines, processing speed below 300 milliseconds and error-free recording of JSONL logs. This test should not be considered as definitive proof of long-term profitability. Continuous monitoring is required during the event.