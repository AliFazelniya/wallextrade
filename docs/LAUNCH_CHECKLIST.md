# Checklist before flight and live activation (Live Launch Readiness Checklist)

Before activating any real transaction on the Wallex exchange account, all the rows in the following table must be approved by the architect and team leader:

| row | Control item Confirmation and test method Status | Approver
|---|---|---|---|---|
| **1** **Complete understanding of Wallex credit account conditions** | Receive the official answer of the organizers to the question Q-01 regarding the nightly fee and capital Awaiting confirmation System architect
| **2** **Adaptation and complete filter of inactive symbols** | Upload the full text of the brief in `config/market_restrictions.json` Waiting for the text of the brief Data engineer
| **3** **Validation of the environment and confidential variables** | Create `.env' file and put the Wallex key without commit in Git Passed Security engineer
| **4** **Complete success of automatic tests of the unit** | Running `pytest tests/` (12 successful tests with Pytest) | ✅ Passed (12/12) | QA engineer
| **5** **Successful completion of historical backtest of 30 days** | Running `scripts/run_backtest.py` with actual Wallex UDF data Passed Quantitative engineer
| **6** **Completing the test in the shadow (Shadow Mode)** | Running `scripts/run_shadow.py' on 3 live market cycles Passed Strategist
| **7** | **Activation of the limits of the risk engine ** | 500 thousand tomans limit per order, commitment limit 60%, and drawdown limit 5% It has been confirmed Risk engineer
| **8** | ** Correct operation of the emergency stop mechanism (Halt)** | Test `test_drawdown_limit_triggers_halt` in Pytest | Passed Risk engineer
| **9** **Preparation of the cashing protocol in Tomans** | Script `scripts/liquidate_to_toman.py` is ready to run It is ready Strategist
| **10** | ** Health and stability of decision logs (Audit Trail)** | `logs/trading_decisions.jsonl` file in structured format Tested QA engineer
| **11** | **Explicit human permission to activate live** | Issuance of flag `live_execution_authorized=True' by user | 🛑 Waiting for user command User

> [!CAUTION]
> Until items 1, 2 and 11 are completed, the system will keep the real transactions blocked as a hardware lock and will remain in a secure simulation/shutdown mode.