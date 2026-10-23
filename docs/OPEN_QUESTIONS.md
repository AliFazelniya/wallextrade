# Ambiguities, open questions and audit of obstacles (Open Questions & Audit Log)

This document records and tracks all validated uncertainties, open questions and legal and executive obstacles of the Wallex trading system.

---

## 1. Unresolved Schedule

> [!IMPORTANT]
> Due to the fact that the exact calendar dates were not specified in the competition brief, no hypothetical date was determined and these cases are registered as uncertainties.

- **Q-01 (exact date and time of the start of the competition):** the exact time of the opening of the trading window of the competition (day, hour and minute of the official announcement of the organization).
- **Q-02 (exact date and time of the end of transactions):** The definite date of stopping the strategies and cashing the basket in Tomans.
- **Q-03 (exact deadline for sending documents and video):** The final deadline for delivering the GitHub repository and the report file to the referees.

---

## 2. Clarification of financial and credit uncertainties (Financial Terms Audit)

- **Q-04 (connection of normal credit conditions with Hekaton's dedicated account):**
  - *Description:* Wallex platform has a nightly credit extension fee and a debt repayment/liquidation mechanism for normal trading credit of 5 million tomans. At the same time, it is mentioned in the hackathon announcements that the original capital belongs to Wallex and the teams will have no obligation to reimburse possible losses.
  - *Status:* requires official and written approval of the organizer before live. At the moment, the risk engine will not allow any catastrophic drawdown with a conservative assumption (5% drop ceiling or 250 thousand Tomans).
- **Q-05 (exact fee rate of the match account):**
  - *Extracted official evidence:* According to the table of official fees of level one Wallex in Tomani markets:
    - Maker fee: **0.25%**
    - Taker fee: **0.30%**
  - *Status:* The accounting and backtest engine has implemented both rates separately.

---

## 3. Status of permitted and prohibited markets (Market Eligibility Audit)

- **Q-06 (list of inactive markets in the credit account):**
  - *Official Wallex API evidence:* Among the 373 Wallex currency pairs, 21 Toman currency pairs were systemically blocked due to zero volume, lack of live quotes or withdrawal from the list and registered as `credit_inactive_symbols' in `config/market_restrictions.json'.
  - *Definitive governance decision:* Any symbol that is not approved in `config/allowed_markets.json' file will not be allowed to enter the order sending engine.
- **Q-07 (transaction in Tether currency pairs):**
  - *Description:* There are 186 currency pairs based on Tether in Wallex. In order to eliminate the risk of currency parity and avoid paying two exchange fees (Toman to Tether and Tether to cryptocurrency), these currency pairs are currently completely blocked and only direct Toman markets are traded.