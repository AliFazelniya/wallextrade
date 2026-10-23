# Statement of the final decision and assessment of the validity of the strategy (phase 14)
### Phase 14 Final Decision Gate & Strategy Integrity Verdict
**Repository:** [`wallex`](..) | **Date of decision:** October 22, 2026 **Input base tag:** `v0.5.0-phase13-validated` | **final audit tag:** `v0.6.0-phase14-audited` (`5356e90`)

---

## 1. Decision Gate Classification official statement

The engineering and quantitative research team, after a complete audit of the executive codes, transaction ledgers, data reproduction and statistical significance tests, announces its final decision in the following framework:

> [!IMPORTANT]
> ### Category of adopted decision:
> **"Option B: Some claims were corrected; The strategy is promising but remains statistically unproven."**
> *(Some claims corrected; strategy remains promising but unproven)*

---

## 2. Summary of phase 14 audit corrections and clarifications

During the Phase 14 independent audit, four research claims were reviewed and revised:

1. **Counterfactual Value-Add:**
   - *Initial claim of phase 13:* Creation of 1,758,202 Tomans (+35.2%) hypothetical profit through the veto of 553 signals.
   - *Audit correction:* This figure is just a raw signal classification index (Classifier Diagnostic Metric) with an accuracy of 68.4%. The real added value that can be realized in the portfolio with limited capital is **+42,339 Tomans (+0.85% of capital)**, which almost completely corresponds to **43,450 Tomans direct savings in Wallex trading fees** through the elimination of 15 untimely trades in volatile and erosion markets.
2. **Adjusting the number of vetoed signals (643 in phase 12 against 553 in phase 13):**
   - *Audit correction:* The number 643 belongs to the 3-symbol portfolio (`BTCTMN` [239] + `ETHTMN` [205] + `SOLTMN` [199]) over 36 days. The number 553 corresponds to the single symbol `BTCTMN' during 90 days. Bitcoin's daily veto rate has been quite stable between the two horizons (6.64 vs 6.14 veto per day).
3. **Adjusting the interest of the 90-day period with the total of 45-day periods:**
- *Audit correction:* The sum of IS (-2,227 Tomans) and OOS (+30,775 Tomans) period is +28,548 Tomans (+0.57%), while the 90-day continuous run has recorded +21,515 Tomans (+0.43%). The difference is exactly 7,033 Tomans, which is caused by the forced cashing of border transaction number 14 at the end of the IS period, with a loss of -5,185 Tomans at the border against its continuation up to a loss of -12,217 Tomans the next day in the continuous run.
4. **Number of 3-day windows (29 windows instead of 30 windows):**
   - *Audit correction:* By deducting 60 preheating candles of the indicators from 8,636 candles, 8,576 candles remain, which exactly forms **29 complete 72-hour windows (288 candles)**, and the remaining 224 candles (2.33 days) are insufficient for the 30th window.

---

## 3. Evaluation of statistical significance and limitation of sample size (Statistical Rigor)

Phase 14 research showed that despite the positive out-of-sample yield (+0.62% in the second 45 days and +0.43% in the entire 90-day period):
- **The number of out-of-sample transactions is small ($N = $9 transactions):**
  - Average transaction yield: 0.50% Standard error: 0.97%
  - 95% efficiency confidence interval: $[-1.73\%, +2.73\%]$
  - Test statistic: $t = 0.51$ with degree of freedom 8 ($p \approx 0.62$).
  - Since zero is within the 95% confidence interval, the null hypothesis that the strategy is superior by chance cannot be rejected with 95% confidence.
- **Distribution of 29 3-day windows ($N = $29 windows):**
  - Rate of profitable windows: 20.7% (6 windows)
  - The rate of cash capital preservation windows: 37.9% (11 windows)
  - Loss windows rate: 41.4% (12 windows)
  - 3-day average return: -0.031% Standard error: 0.051%
  - 95% confidence interval of window efficiency: $[-0.135\%, +0.073\%]$ ($t = -0.617$).

> [!WARNING]
> **Result of statistical validation:**
> In terms of portfolio econometrics and mathematics, the claim of "definitive proof of strategy profitability in a 3-day competition" is false and unscientific. The strategy has been able to protect the capital well (the maximum drawdown of the whole period is 1.31% and the maximum drawdown in each 3-day interval is 0.48%), but the net return in a random 72-hour interval is highly dependent on the macro market regime in those 3 days.

---

## 4. Operational recommendations for the day of the hackathon

1. **maintain live transaction suspension (`live_execution_authorized = False'):**
   No permission is issued to automatically connect the Wallex private key to the live transaction websocket without direct supervision and final decision of the human team.
2. **Priority strategy in case of deciding to deploy live:**
   If approved by the human team, the only strategy allowed for deployment is **Bitcoin Selective Strategy with AI Regime Filter ([`RegimeMomentumStrategy'](../src/strategy/regime_momentum.py)) with strict loss limit of 2.0% and profit limit of 3.5%**.
3. **Competitive advantage of the strategy:**
   The main advantage of the system is in preventing over-trading and preventing the burning of capital with Wallex fees. In 37.9% of the historical windows, the robot has maintained 100% liquidity by detecting erosive volatility and in 58.6% of the time the portfolio has remained loss-free.

---

## 5. Exact Reproduction Commands

For independent verification of all tables and figures in this report:

```bash
# 1. Activating the virtual environment and verifying dependencies
cd wallex
source .venv/bin/activate

# 2. Implementation of accounting and audit tests of phase 14
pytest tests/ -v

# 3. Reproduction of 90-day simulation and walkforward windows
python scripts/run_phase13_validation.py

# 4. Checking the detailed log of 24 artificial intelligence transactions
cat docs/PHASE14_PNL_RECONCILIATION.md
```
