# Final report of Pre-Competition Readiness Assessment
### Phase 11: Definitive Audit, Strategy Verification and System Governance Assessment for Wallex x Starcoach Hackathon

This document provides a comprehensive, independent and evidence-based evaluation of all parts of the algorithmic trading system in the [`wallex'](file:///root/starcoach-hack/wallex) repository before the event begins.

---

## 1. Audit results and separation of sets of symbols (Market List Set-Difference Audit)

From a total of **373 active markets** queried from the official programming interface of the Wallex exchange (`https://api.wallex.ir/v1/markets`), the mathematical separation process with an automatic script [`scripts/audit_market_restrictions.py`] (file:///root/starcoach-hack/wallex/scripts/audit_market_restrictions.py) was proved as complete and dual-separate (Disjoint & Complete) as follows:

```
[ All Wallex symbols: 373 ]
   ├── 1. Approved authorized trading world (Allowed Universe): 16 symbols (4.3%)
   └── 2. All symbols blocked (Restricted Universe): 357 symbols (95.7%)
          ├── Inactive symbols / no liquidity in credit account: 21 symbols
          ├── Tether currency pairs are excluded: 186 symbols
          ├── Small Toman symbols (The 24-hour volume is below 5 billion tomans): 139 symbols
          └── Tomani symbols have a wide spread (above 0.35%): 11 symbols
```

### 1.1. The results of the validation of the interference and accuracy of the sets
- **Accidental Allowlist Inclusions:** **0 symbols** (allowed and blocked list subscription is exactly zero $\emptyset$).
- **Missing symbols from the system (Missing Symbols):** **0 symbols** (all 373 exchange symbols are in one of the two lists).
- ** Duplicate or invalid symbols (Malformed / Duplicate): ** 0 cases ** (all symbols are normalized and capitalized).
- **Sovereign guarantee:** Applying explicit restrictions is always preferable to volume and spread criteria; Even if a stock tokenized asset (such as `TSLAXTMN` or `AMZNXTMN`) has volume, it will be filtered at the first layer and never reach the order portal due to the inactivity in Wallex credit accounts.

---

## 2. Independent verification of candle aggregation (Candle Aggregation Reproducibility)

By running the verification script [`scripts/verify_candle_aggregation.py`](file:///root/starcoach-hack/wallex/scripts/verify_candle_aggregation.py) the following microstructural results were independently reproduced on the main currency pairs:

| Audit index Bitcoin to Toman (**BTCTMN**) | Ethereum to Toman (**ETHTMN**) |
|---|---|---|
| **Number of raw records received from Wallex** | 27,344 candles 27,318 candles
| **Raw time step distribution (Interval Distribution)** | 27,341 steps 60 seconds, 1 step 180 seconds, 1 step 840 seconds 27,315 steps 60 seconds, 1 step 180 seconds, 1 step 2400 seconds
| **Raw data time frame** | 2026-10-03 10:49:00 to 2026-10-22 10:47:00 (UTC) | 2026-10-03 10:49:00 to 2026-10-22 10:47:00 (UTC) |
| **The number of missing candles (relative to the continuous step of 60 seconds)** | 15 candles (0.05%) | 41 candles (0.15%) |
| **Duplicate candles** | 0 items 0 items
| **Total number of 15-minute time bins (Output Bins)** | 1,825 baskets 1,825 baskets
| **Complete baskets (including all 15 1-minute candles)** | 1,820 baskets 1,818 baskets
| **Incomplete baskets (1 to 14 candles)** | 5 baskets 5 baskets
| **Empty baskets (0 candles)** | 0 basket 2 baskets
| **valid final candles (Valid 15m Candles)** | **1,825 candles** | **1,823 candles** |
| **Input candles to the strategy (after 50 warm-up candles)** | 1,775 candles 1,773 candles
| ** Mathematical rules of aggregation (Open=1st, High=max, Low=min, Close=last, Vol=sum)** | ✅ **100% confirmed** | ✅ **100% confirmed** |

### Definitive policy for dealing with incomplete data and current candles:
1. **In-progress candle:** The current open candle of the market is never fed into the strategy so that the lookahead bias does not occur.
2. **Empty Bins:** are completely removed with ``dropna()'' method to avoid the production of fake flat candles and false signals.
3. **Incomplete Bins:** are accepted only if they have at least 10 valid 1-minute observations.

---

## 3. Audit of the fee model, slippage and execution assumptions (Execution & Fee Model)

- **Maker Fee:** **0.25%** (0.0025) based on the official Wallex level 1 table for limited orders (`LIMIT') sitting in the order book.
- **Taker Fee:** **0.30%** (0.0030) for Marketable Limit orders (which take liquidity immediately), stop loss orders, and final settlement.
- **Price slippage:** 0.15% assumed in each purchase or sale transaction.
- **Non-execution of orders (Unfilled Orders):** Purchase orders are filled only if the lowest candle price (`Low') does not exceed the order price (`Low <= OrderPrice').

---

## 4. Strategy audit results and 4-Way Baseline Comparison with benchmarks

Based on an independent execution of the script [`scripts/validate_strategy_and_baselines.py`](file:///root/starcoach-hack/wallex/scripts/validate_strategy_and_baselines.py) on 1,825 real 15-minute Wallex candles, the following comparative results were obtained:

### 4.1. Bitcoin to Toman symbol (BTCTMN)
| approach/strategy Net Return | Maximum Drawdown (Max DD) | Net Profit/Loss (TMN) | Number of closed transactions Turnover |
|---|---|---|---|---|---|
| **1. Buying and holding (Buy & Hold)** | -1.96% **10.38%** | 98,244 Tomans 1 1.0x |
| **2. Maintaining 100% liquidity in Tomans** **0.00%** | **0.00%** | 0 tomans 0 | 0.0x |
| **3. Definitive strategy without artificial intelligence** | -1.22% 1.82% 60,902 Tomans 7 | 1.4x |
| **4. Strategy with AI assistant (Regime Filter)** | **-0.36%** | **0.51%** | **17,794 Tomans** | **2** **0.4x** |

### 4.2. Ethereum symbol to Toman (ETHTMN)
| approach/strategy Net Return | Maximum Drawdown (Max DD) | Net Profit/Loss (TMN) | Number of closed transactions Turnover |
|---|---|---|---|---|---|
| **1. Buying and holding (Buy & Hold)** | -9.46% **17.86%** | 472,946 Tomans 1 1.0x |
| **2. Maintaining 100% liquidity in Tomans** **0.00%** | **0.00%** | 0 tomans 0 | 0.0x |
| **3. Definitive strategy without artificial intelligence** | -1.37% 2.11% 68,435 tomans 7 | 1.4x |
| **4. Strategy with AI assistant (Regime Filter)** | **-0.89%** | **1.22%** | **Tomans 44,704** | **6** **1.19x** |

### 4.3. Assessing the role and real value of artificial intelligence (AI Value-Add Evidence)
- **Numerical evidence:** In the Bitcoin symbol, the traditional deterministic strategy entered 7 trades, which resulted in commission losses due to the eroding market. By detecting the ``CALM_RANGE'' regime, the artificial intelligence agent prevented the reopening of 5 erosion trades and **reduced the amount of net loss by 71%** (-17 thousand tomans against -60 thousand tomans) and increased the maximum drawdown from **1.82% to 0.51%**.
- **On the Ethereum token:** The AI-assisted strategy curbed the losses of the Ethereum market from **-9.46% in Buy & Hold to -0.89%** and reduced the drawdown from **17.86% to 1.22%**.

### 4.4. fee sensitivity scenarios
- **Base scenario (0.25% maker / 0.30% ticker):** return -0.36% (Bitcoin) / -0.89% (Ethereum).
- **All ticker pessimistic scenario (0.30% ticker / 0.30% ticker):** return -0.36% (Bitcoin) / -0.90% (Ethereum).
- **Severe stress scenario (fee 0.35% / 0.35%):** Return -0.38% (Bitcoin) / -0.96% (Ethereum).
- **Conclusion:** Changes of ±0.05% in the fee have a very small effect (~0.02% to 0.07%) on the result, and the main pillar of capital preservation is the artificial intelligence filter and risk ceiling.

---

## 5. Evidence of automated tests and code coverage (Automated Testing & Coverage)

Unit and integration tests were run with pytest-cov tool:

```
Name                          Stmts   Miss  Cover
-------------------------------------------------
src/agents/regime_agent.py       40     15    62%
src/agents/schemas.py            41      0   100%
src/data/client.py               85     52    39%
src/data/fetcher.py              60     43    28%
src/exchange/adapter.py          83     21    75%
src/features/indicators.py       43      6    86%
src/portfolio/accounting.py     119     29    76%
src/risk/engine.py               76     11    86%
-------------------------------------------------
TOTAL                           547    177    68%
============================== 31 passed in 1.16s ==============================
```

- **Total number of tests:** 31 tests (100% passed, 0 errors, 0 ignored).
- **Measured code coverage:**
  - Independent risk management engine ([`src/risk/engine.py`](file:///root/starcoach-hack/wallex/src/risk/engine.py)): **86%**
  - Quantitative indicators extraction ([`src/features/indicators.py`](file:///root/starcoach-hack/wallex/src/features/indicators.py)): **86%**
  - Portfolio accounting and fees ([`src/portfolio/accounting.py`](file:///root/starcoach-hack/wallex/src/portfolio/accounting.py)): **76%**
  - Order execution adapter and authorized filter ([`src/exchange/adapter.py`](file:///root/starcoach-hack/wallex/src/exchange/adapter.py)): **75%**
  - Pydantic structured models ([`src/agents/schemas.py`](file:///root/starcoach-hack/wallex/src/agents/schemas.py)): **100%**

---

## 6. Live-Trading Isolation

> [!CAUTION]
> - Environment variable `TRADING_MODE` is set to `SIMULATION`.
> - The `live_execution_authorized' variable is set to `False', which acts as a **Software Authorization Gate** and issues an exception [`ExecutionError'](file:///root/starcoach-hack/wallex/src/exchange/adapter.py#L26-L27) in case of any live order attempt.
> - No private keys or authentication tokens are registered in git or documentation.

---

## 7. Remaining obstacles and final assessment of readiness level (Readiness Assessment)

### Unresolved Blockers:
1. Absence of definite start and end calendar dates in the text of the brief.
2. Non-confirmation in writing of the nightly fee status of the credit account of 5 million tomans by Wallex officials.

### 🎯 system readiness rating (Readiness Classification):
Due to the completion of audits and software tests:

> **"Validated live transaction prerequisites, pending explicit human authorization"**
> *(Live-trading prerequisites verified, awaiting explicit authorization)*

- **Gate-based commit:** `a492b831f98e67ed3ebdcfaf6eb92fa73bde42e5`
- **New commit hash with phase 11 audit:** `9f8548568e9bbf5a121a10692bf5bafd73634310`
- **Gate official tag:** `v0.3.0-pre-competition`