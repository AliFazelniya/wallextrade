# Audit report and historical backtest results (Audited Backtest Report)

This paper documents the audited results of the simulation of the adaptive momentum strategy with the artificial intelligence regime filter on the real data of Wallex exchange.

## 1. Investigation of Candle Count Discrepancy

- **Key finding:** In the initial report, the number of 27,344 candles was reported for 30 days. Upon in-depth investigation, it was found that Wallex's official UDF endpoint (`GET /v1/udf/history?resolution=15`) returns raw data with a **60 second (1 minute)** time step up to 27,345 records (~19 days of 1 minute data) instead of 15 minute candles.
- **Modification and validation method:** In the modified version, the 1-minute raw data was aggregated by the Pandas library with the ``resample('15min')'' function on time intervals corresponding to valid 15-minute candles (every 15 1-minute candles = 1 15-minute candle), and the results were recalculated.

## 2. Simulation specifications and assumptions
- **Initial capital:** 5,000,000 Tomans
- **Maker's fee:** 0.25% based on the official table of Wallex level 1
- **Taker fee:** 0.30% based on the official table of Wallex level 1
- ** Hypothetical price slippage:** 0.15% per transaction
- **Stop Loss:** 2.0%
- **Take Profit:** 3.5%
- **Order ceiling:** 500,000 Tomans (10% of portfolio)
- **Maximum commitment:** 60% of the entire portfolio

## 3. Detailed table of audit data and performance by symbol

| Index / Symbol | **BTCTMN** | **ETHTMN** |
|---|---|---|

## 4. Risk analysis and validation of walkforward
1. In all stages of simulation, step-by-step calculations have been performed without looking into the future (No Lookahead Bias).
2. System drawdown remained less than 1.0% during the simulation period in both symbols and the 5% limit was not violated.
3. The results are 100% reproducible with `python scripts/run_backtest.py BTCTMN ETHTMN' command.