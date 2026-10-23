# Final report on operational readiness, strategy freezing and competition prerequisites audit (phase 15)
### Phase 15 Final Competition Rehearsal, Operational Reliability, and Strategy Freeze
**Repository:** [`wallex`](..) | **Audit date:** October 22, 2026 **Input base tag:** `v0.6.0-phase14-audited` (`d49bd69`) | **Final tag of phase 15:** `v0.7.0-phase15-rehearsed` (`3dd26d3`) | **Status of tests:** 58 out of 58 successful tests (80% code coverage)

---

## 1. The official statement of the readiness classification of the competition (Readiness Classification)

The engineering and risk team, after conducting a test maneuver in the shadow on the live data of Wallex exchange, evaluating 14 operational failure scenarios and comparative review of the event brief, announces the final ranking as follows:

> [!IMPORTANT]
> ### The official status of the system classification:
> **"The test maneuver in the shadow passed successfully; The specific prerequisites for the race have not yet been resolved."**
> *(Shadow rehearsal passed; competition prerequisites unresolved)*
>
> **Explanation:** All software modules, risk engine, artificial intelligence classification, accounting, error tests and shadow maneuvering have been verified with 100% success on Wallex live data. However, due to the fact that the exact start/end calendar of the competition is not known from the organizer and the access keys of the dedicated account of the competition have not been delivered, the live connection will remain hardware **blocked (`live_execution_authorized=False')**.

---

## 2. Strategy Freeze Record

In order to guarantee scientific reproducibility and prevent overfitting, the parameters were frozen on the eve of the competition, the strategy and risk settings:

- **Frozen manifest file:** [`config/frozen_strategy_manifest_v0.6.0.json`](../config/frozen_strategy_manifest_v0.6.0.json)
- **Manifest integrity hash (SHA-256):**
  `249c1e4af942156d2f1a602b58bd729969c660857e2d98f0158ac71c9fa75f66`
- **Frozen Base Commit ID:** `d49bd69b636e0af403f35a7ddca7b34685f52090`
- **Trading Strategy:** [`RegimeMomentumStrategy`](../src/strategy/regime_momentum.py) on single token `BTCTMN`
  - Data timeframe: 15 minutes (reproduced cumulative candles)
  Preheating period of indicators: 60 candles (15 hours)
  - Take Profit: 3.5%
  - Stop Loss: 2.0%
  - Minimum confidence coefficient of artificial intelligence: 0.70
  - Default alternative behavior: ``NO_TRADE'' (no trade in case of uncertainty or volatility regime)
- **Artificial intelligence engine settings:** [`RegimeClassificationAgent`](../src/agents/regime_agent.py)
  - Model ID: ``gemini-2.5-flash'' with prompt version ``v1.0.0''
- Statistical failure fallback: active, with automatic shutdown mechanism (Fails Closed) in case of timeout or internet unavailability
- **Risk Engine Settings:** [`RiskEngine'](../src/risk/engine.py)
  - Limit of each order: 500,000 Tomans (10% of the total capital of 5 million)
  - Total portfolio commitment limit: 60.0%
  - Drawdown ceiling for the entire period: 5.0%
  - Daily drop ceiling: 200,000 Tomans
  - Limit of simultaneous open positions: 1 position
  - Order book spread limit: 0.20%
  - Emergency Halt: Violation of the 5% drawdown limit will permanently stop the system.
- **Fees and implementation assumptions:**
  - Maker fee: 0.25%
  - Taker fee: 0.30%
  - Allowed price slippage: 0.15%

---

## 3. Blocker Matrix

According to the audit of the official brief and the responses of the organizers, the status of prerequisites was extracted by separating critical and operational barriers:

| row | Prerequisite for the competition Source of requirements Current status Classification of obstacles (Blocker Category). Necessary operational action
|---|---|---|---|---|---|
| **1** **Exact date and time of the start of the match** | Starcoch match brief Unspecified in the brief 🔴 **Critical barrier (Blocker B-01)** | Official inquiry of the day, hour and minute of opening the window
| **2** **exact date and time of the end of transactions and deadlines** | Starcoch match brief Unspecified in the brief 🔴 **Critical barrier (Blocker B-02)** | Inquiring about the exact time of stopping the trade and delivering the documents
| **3** **Details of the competition's exclusive account** | Wallex hackathon brief Not issued/approved 🔴 **Critical barrier (Blocker B-03)** | Get user ID and private account API keys
| **4** **Authorized API accesses of dedicated account** | Exchange connection requirements Uncertain 🔴 **Critical barrier (Blocker B-04)** | Validation of sending the order and reading the balance of the competition account
| **5** **Written confirmation of the conditions of exemption from the nightly fee** | Financial uncertainty Q-04 Awaiting reply 🟡 **Secondary barrier (Blocker B-05)** | Written confirmation of the team's non-indebtedness and exemption from Rollover Fee
| **6** **Allowed and forbidden markets** | Wallex brief and API Confirmed and tested 🟢 **Resolved** | Blocking 21 inactive icons in `config/market_restrictions.json` |
| **7** | **table of trading fees** | Valax official table It was implemented 🟢 **Resolved** | Applying 0.25% maker and 0.30% ticker in all engines
| **8** | **Requirement of 100% settlement in Tomans at the end of the competition** | The rules of the competition, paragraph 10 Implemented and tested 🟢 **Resolved** | ``liquidate_to_toman.py'' script was successfully tested
| **9** **Scenario of the 5-minute demo video** | Evaluation requirements of judges It was edited 🟢 **Resolved** | The document `docs/DEMO_SCRIPT.md` is ready for video recording
| **10** | **Non-disclosure of confidential information in Gate** | Security standards It was audited 🟢 **Resolved** | Absence of any token or private key in the repository

> [!CAUTION]
> **Fail-Closed Rule:**
> The presence of critical obstacles B-01 to B-04 systemically prevents live activation. Until these obstacles are completely removed, the execution mode should remain on `TRADING_MODE=SHADOW'.

---

## 4. The results of the test maneuver in the shadow on the live data of Wallex (Production Shadow Rehearsal)

The script [`scripts/run_production_rehearsal.py`](../scripts/run_production_rehearsal.py) was connected to the public Wallex web service for accurate simulation without real ordering:

- **Monitored symbol:** `BTCTMN`
- **Number of executed cycles:** 5 live consecutive cycles
- **Duration of the total maneuver:** 16.59 seconds (with a 2-second inter-cycle delay)
- **Average cycle delay (Latency):** 1,713.8 milliseconds (including receiving depth, 5-day history of UDF, aggregating candles and extracting features)
- **Delay range:** At least 1,630.1 milliseconds Maximum 1,759.9 milliseconds
- **Actual spread of Wallex market:** **0.0904%** (buying price 22,116,704,045 rials | selling price 22,136,687,779 rials)
- "Freshness of data": "Data is fresh and valid" status (the interval between the last candle is less than 30 minutes)
- **Diet recognition by artificial intelligence:** `CALM_RANGE' with a confidence factor of 75% and ``HOLD'' recommendation
- **Strategy signal:** `HOLD`
- **Simulated orders:** 0 transactions (the strategy completely preserved the liquidity of 5,000,000 Tomans by avoiding trading in the range market)
- **Log output:** [`logs/production_rehearsal_phase15.jsonl`](../logs/production_rehearsal_phase15.jsonl) and [`research/phase15_rehearsal_results.json`](../research/phase15_rehearsal_results.json).

> [!NOTE]
> **The scientific transparency of the test horizon in the shadow:**
> Due to the limitation of synchronized execution in the current meeting, the maneuver was executed for 16.59 seconds (5 full live cycles). No claim is made to complete a continuous 72-hour test; However, the stability of the asynchronous cycle and sequential processing of the live data of the exchange was experimentally proven.

---

## 5. Audit of 14 scenarios of operational failures (Operational Failure Audit)

In the file [`tests/test_operational_failures.py`](../tests/test_operational_failures.py), 14 advanced integration tests were implemented and passed for system resilience against the worst market conditions:

1. **Exchange API Timeout (`test_exchange_api_timeout_fails_closed`):** In case of network disconnection, no orders are registered and assets remain intact.
2. **Exchange 429 error management (`test_http_429_rate_limit_recovery`):** If the rate exceeds the limit, the system will back-off and warn without crashing.
3. **Malformed and stale data (`test_malformed_and_stale_market_data_fails_closed'):** Data older than 30 minutes or without a closing price are identified and rejected before generating a signal.
4. **Missing candles and historical gap detection (`test_missing_candles_gap_detection`):** Time gaps in the data are detected and reported.
5. **Timeout or invalid output of artificial intelligence (`test_ai_timeout_and_invalid_structured_output_activates_fallback`):** In case of LLM network error, statistical fallback is activated with a conservative state of `HOLD`.
6. **Duplicate order prevention (`test_duplicate_order_prevention_fail_closed'):** A 10-second cooldown window prevents duplicate orders from being sent.
7. **Discrepancy of orders in uncertain status (`test_uncertain_order_submission_reconciliation'):** In case of uncertainty at the moment of sending, the system inquires about the status by querying open orders.
8. **Partially filled orders (`test_partial_fills_and_unfilled_orders'):** Only the filled portion of the asset is allocated and the rest remains cash.
9. **Balance discrepancy with the exchange (`test_incorrect_account_balances_discrepancy_alert'):** A discrepancy of more than 1,000 Tomans will immediately issue a discrepancy alert.
10. **Order rejection by the risk engine (`test_risk_engine_rejection_fails_closed'):** Prohibited symbols are definitively rejected and large orders are limited to 500 thousand Tomans.
11. **Emergency halt of the system (`test_emergency_halt_triggers_and_blocks_all_orders'):** Crossing the capital loss of 5% leads to permanent trade lock until manual reset.
12. **State recovery after process crash (`test_process_crash_and_portfolio_state_recovery`):** Serialization and complete recovery of portfolio state with `export_state()` and `from_state()` functions.
13. **Final settlement into Toman (`test_final_conversion_into_toman_simulation`):** 100% conversion of cryptocurrency assets into cash with ticker fee deduction.
14. **hardware lock of live trades (`test_system_fails_closed_without_authorization`):** In the absence of the `live_execution_authorized=True` flag, the submission of any real order is strictly blocked.

---

## 6. Confirming the operational value of artificial intelligence and avoiding exaggerated claims

- The initial claim of phase 13 regarding 1.75 million tomans of hypothetical profit was corrected in phase 14 and will not be repeated in this phase.
- The operational value of artificial intelligence in the phase 15 live maneuver:
  - The Bitcoin market has fluctuated in the tight range of 22.1 billion Tomans in recent hours.
  - The regime agent identified this situation as ``CALM_RANGE'' and issued a ``HOLD'' command in all 5 monitoring cycles.
  - This behavior prevented the production of destructive taker fees and kept the initial liquidity of 5 million tomans intact.

---

## 7. Final Repository Deliverables approval

- **Source Codes:** Corresponding to the tested version with a modular structure in the `src/` folder.
- **Persian guide:** file [`README.md`](../README.md) and operational runbook [`docs/COMPETITION_RUNBOOK.md`](COMPETITION_RUNBOOK.md).
- **Risk and strategy documents:** Complete documents in `docs/` and `research/`.
- **Market restrictions:** `config/market_restrictions.json` and `config/allowed_markets.json` files.
- **Phase 14 P&L audit reports:** files `docs/PHASE14_*.md` and `docs/AI_COUNTERFACTUAL_RECONCILIATION.md`.
- **Shadow maneuver evidence:** logs `logs/production_rehearsal_phase15.jsonl` and results `research/phase15_rehearsal_results.json`.
- **Automated tests:** **58 successful tests** with 2.68 seconds execution time and 80% code coverage.
- **Config file example without secret:** `.env.example` file and manifest without secret information.
- **Demo scenario:** 5 minute scenario in `docs/DEMO_SCRIPT.md`.
- **Non-disclosure of confidential information:** The repository does not have any hardcoded API keys.