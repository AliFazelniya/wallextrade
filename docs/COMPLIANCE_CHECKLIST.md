# Compliance Checklist

Before submitting the project or any transaction, the status of all the following items must be checked and confirmed:

- [x] **Not sending the actual order in the development and testing phase:** All tests are done in the simulator environment or with historical data.
- [x] **Preservation of Access Keys Confidentiality:** No API keys or ciphers are committed in code or git history.
- [x] **Complete independence of the risk engine:** The risk management engine has complete veto authority over any output of the artificial intelligence model.
- [x] **Capital limit of 5 million Tomans:** Risk calculations are configured based on the principal capital of 5,000,000 Tomans.
- [x] **Forbidden and illiquid markets filter:** Illegal or high spread markets are blocked in `config/market_restrictions.json`.
- [x] **Final conversion mechanism to Tomans:** The script and automatic module for closing positions in Tomans have been implemented.
- [x] **Complete decision log recording (Audit Trail):** The reasons for each decision (even non-entry) are stored in JSONL format.
- [x] **Automated and Isolated Tests:** Unit tests are done with full Pytest and Mocking and do not send orders to the real exchange.
- [ ] **Receive the full text of the Farsi competition brief from the user:** To load the detailed list of inactive credit account symbols.
- [ ] **Written confirmation of credit conditions of 5 million tomans:** Inquiring about the presence or absence of overnight credit extension fees.
- [ ] **Explicit permission of the user to activate live:** The system will remain in simulation mode until the direct command is issued.