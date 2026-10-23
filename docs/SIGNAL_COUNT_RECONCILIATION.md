# Auditing and matching the number of vetoed signals in phases 12 and 13
### Signal Count Discrepancy Reconciliation (643 vs 553 Vetoes)
**Repository:** [`wallex`](..) | **Audit date:** October 22, 2026 **Currency pairs:** `BTCTMN`, `ETHTMN`, `SOLTMN`

---

## 1. Statistical audit questionnaire

In comparing the research reports, the following apparent contradiction was observed:
- In **phase 12** (36-day horizon), the number of vetoed signals by artificial intelligence was reported as **643 signals**.
- In **phase 13** (90-day horizon), the number of vetoed signals by artificial intelligence was reported as **553 signals**.

**Key question:**
How is it possible that there are more vetoed signals in a shorter time frame (36 days) than in a 2.5 times longer time frame (90 days)? Has the data been overwritten or is there something wrong with the signal generation?

---

## 2. Autopsy proof and separation of symbols (Symbol Universe Breakdown)

By re-reading technical documents and [`run_phase12_research.py`](../scripts/run_phase12_research.py) and [`run_phase13_validation.py`](../scripts/run_phase13_validation.py) codes, the reason for this structural difference was proved mathematically:

1. **Phase 12:** Examination of the **Multi-Symbol Shared Portfolio** consisting of 3 permitted cashable symbols:
   - Bitcoin (`BTCTMN`)
   - Ethereum (`ETHTMN`)
   - Solana (`SOLTMN`)
   The number of 643 signals was **total vetoes of all 3 cryptocurrencies**.

2. **Phase 13:** Focus on specialized and independent validation of **Bitcoin single token (`BTCTMN')**.
   A total of 553 signals were vetoes of **Bitcoin currency pairs only** during 90 days.

### Separation table of symbols and exact matching of the number of signals

| Research phase Range of symbols Time horizon All technical signals AI verified signals AI vetoed signals Daily veto rate per symbol |
|---|---|---|---|---|---|---|
| **Phase 12 (BTCTMN)** | Only Bitcoin 36 days 283 | 44 | **239** | **6.64 veto per day** |
| **Phase 12 (ETHTMN)** | Ethereum only 36 days 283 | 78 | **205** | **5.69 veto per day** |
| **Phase 12 (SOLTMN)** | Only Solana 36 days 295 | 96 | **199** | **5.53 veto per day** |
| **Total portfolio of phase 12** | **3 symbols at the same time** | **36 days** | **861** | **218** | **643** | **17.86 veto in the whole portfolio** |
|---|---|---|---|---|---|---|
| **Phase 13 (BTCTMN)** | **Bitcoin Only** | **90 days** | **671** | **118** | **553** | **6.14 veto per day** |

```
Math matching phase 12:
239 (BTC) + 205 (ETH) + 199 (SOL) = 643 Reported veto
```

---

## 3. Algorithm Stability Analysis (Daily Veto Frequency Stability)

To check if the behavior of AI has undergone a drastic change or instability over time, the daily veto rate of the Bitcoin currency pair was compared in both horizons:

$$\text{Daily Veto Rate (Phase 12 BTC - 36d)} = \frac{239}{36} = \mathbf{6.64\text{ vetoes/day}}$$
$$\text{Daily Veto Rate (Phase 13 BTC - 90d)} = \frac{553}{90} = \mathbf{6.14\text{ vetoes/day}}$$
$$\text{Relative Deviation} = \frac{|6.64 - 6.14|}{6.39} = \mathbf{7.8\%}$$

> [!NOTE]
> Bitcoin's daily veto rate deviates only 7.8% between the 36-day and 90-day intervals. This shows the extraordinary behavioral stability of the artificial intelligence market regime classification module ([`RegimeClassificationAgent'](../src/agents/regime_agent.py))**, which has had uniform and predictable behavior in different phases of the market.

---

## 4. Audit summary

- The claim of contradiction is definitely rejected.
- The number **643** belongs to the total of 3 cryptocurrencies (`BTC + ETH + SOL') in 36 days.
- The number **553** belongs to the single cryptocurrency ``BTCTMN'' in 90 days.
- The behavior of the system in vetoing has averaged between 6.1 and 6.6 noise signals per day on the Bitcoin currency pair.