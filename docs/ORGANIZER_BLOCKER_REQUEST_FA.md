# Official letter of inquiry and removal of operational obstacles of the competition (Starkoch × Valks)
# Official Organizer Blocker Resolution Inquiry (Starcoach × Wallex)

> [!CAUTION]
> **Supervisory warning and safety protocol (Operator Action Required):**
> This document is an official draft for technical and operational inquiries from Hackaton Starcoch Secretariat and Wallex Exchange technical team.
> **This request should not be sent automatically or by a robot under any circumstances.**
> Any submission of this text should only be done after final review and approval by the team's human leader and through the competition's valid communication channels (starcoach dashboard ticket, hackathon official email, or Wallex support coordination group).

---

**To: the honorable secretariat of Starkoch artificial intelligence hackathon and technical and support team of Wallex exchange**  
**From: Intelligent algorithmic trading system engineering team (Wallex x Starcoach Algorithmic Trading Team)**  
**Subject: Request to remove five operational obstacles (B-01 to B-05) for final connection and start of live transactions**  
**Setting date:** October 22, 2026 (November 1, 1405)  
**System Version:** `v0.8.0-phase16-audited` / Frozen Strategy Manifest `v0.6.0`

---

### With regards and regards;

Our engineering team has successfully completed the design, development, statistical validation, shadow execution, stress reduction tests and financial audits of the automated trading system. The current technical status of the system is as follows:

- **Coverage of automated tests:** 60 tests out of 60 unit tests and successful integration (100% pass) with 81% code coverage.
- **Strategy Freeze:** Strategy based on intelligent detection of the market regime with `regime_momentum' model and fixed parameters (manifest hash: `249c1e4af...`).
- **Independent risk engine and validation gate:** Pre-order defensive barrier with definitive filter of 357 blocked symbols and strict control of order limit, capital loss and allowed spread.
- **Software Readiness Status:** **Technical GO Ready**, with code-level software gate to prevent live transactions until human approval (`live_execution_authorized=False').

In order to complete the process of connecting to the live account, prevent any operational interference and officially start the 3-day trading window, it is requested that you inform this team of the following 5 things in an official and written form to apply to the software infrastructure:

---

### Paragraph 1 — The exact calendar date and time of the start of the competition window (obstacle B-01)
In the initial documents, the duration of the competition is stated as "three days", but the exact calendar time origin for the start of the counting is not announced.
- **Request:** What is the exact calendar date (year, month, day) and the exact hour and minute of the start of the trading window in Iran's official time (IRST / UTC+03:30) or the ISO 8601 standard format?
- **Technical importance:** The data warm-up pipeline and incremental reception of 15-minute candles must be started synchronously 60 candles before the start time.

### Paragraph 2 - The exact date of the end of transactions and the deadline for sending documents (obstacle B-02)
To manage regular withdrawal from the market and delivery of arbitration items:
- **Request:**
  1. The exact time of the end of the trading window of the competition to execute the forced settlement script to Toman (`liquidate_all_to_toman').
  2. The final deadline for registering the last commit in the GitHub repository, sending the repository link and uploading the 5-minute video of the judges' demo presentation.
- **Technical importance:** The algorithm must review all active crypto positions without critical slippage at least 30 minutes before the window closes.

### Paragraph 3 - Allocation and details of the competition credit account (obstacle B-03)
According to the rules of the competition, an initial credit equal to 5 million Tomans is allocated to each team.
- **Request:** What is the User ID, wallet number or Wallex account details assigned to this team and when will the balance of 5 million Tomans be credited to the account?
- **Technical importance:** Automatic validation of the initial balance (`PortfolioEngine.reconcile_with_exchange`) requires initial checking of the account before entering.

### Clause 4 — Issuance and delivery of competition account API access keys (obstacle B-04)
In order to send orders and check the private account balance:
- **Request:** How and when will the access key (`x-api-key') and the secret key related to the exclusive account of the competition be delivered? Is a header or double ID needed to separate hackathon orders in Wallex API?
- **Technical importance:** Our team has designed the read-only test scenario so that before any transaction, access and private methods are validated without registering an order.

### Paragraph 5 - Official confirmation of credit extension conditions and exemption from overnight fees (barrier B-05)
In the normal use of Wallex, credit facilities are subject to rollover/overnight fee and debt settlement.
- **Request:** Is the credit of 5 million tomans granted during the 3 days of the competition subject to any overnight fee, daily interest or credit extension fee? Is there a complete waiver of facility fees for participants?
- **Technical importance:** If there is any renewal fee or daily profit, these figures must be exactly modeled in the portfolio accounting module ([`src/portfolio/accounting.py`](../src/portfolio/accounting.py)) so that the net profit and the actual value of the account balance do not deviate.

---

### Summary of the team's technical information to facilitate the secretariat's follow-up:

| System parameter | Registered technical value
|---|---|
| **team/project name** | Algorithmic system of Starcoch x Wallex competition
| **Language and development environment** | Python 3.12 / Linux / Financial engineering standard packages
| **software version** | Release `v0.8.0-phase16-audited` |
| **Strategy Manifest Hash** | `249c1e4af942156d2f1a602b58bd729969c660857e2d98f0158ac71c9fa75f66` |
| **covering software tests** | 60 successful automated tests with 81% code coverage
| **trading target market** | Exclusively ``BTCTMN'' currency pair (with 21-symbol programming cut-off filter disabled) |

We are grateful in advance for the cooperation and guidance of the honorable secretariat and the Wallex technical team.

**Thanks and Regards,**  
**Algorithmic trading system engineering and management team**  
*(signature of the human representative and leader of the team)*