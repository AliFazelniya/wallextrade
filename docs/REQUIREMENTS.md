# Technical, trading and governance requirements of the system (System Requirements)

This document defines the functional and non-functional requirements of Wallex algorithmic trading system.

---

## 1. Functional Requirements

### 1.1. Receiving and processing market data
- **FR-01 (Symbol monitoring):** Get list of valid symbols from endpoint `/v1/markets` and filter currency pairs based on Tomans (`quoteAsset == 'TMN'`).
- **FR-02 (candle and history data):** Receive OHLCV candles from the official Wallex UDF endpoint (`/v1/udf/history`) in 15-minute or 1-hour timeframes.
- **FR-03 (order office and market depth):** market depth query (`/v1/depth') to evaluate the spread (Spread), liquidity (Liquidity) and calculate the actual slippage before ordering.
- **FR-04 (Inquiry of the latest trades):** Monitoring of recent trades (`/v1/trades`) in order to estimate the speed of fluctuations and the volume of real trades.

### 1.2. Analysis and decision-making based on agent-based artificial intelligence (Agentic AI)
- **FR-05 (quantitative feature extraction):** Calculation of analytical indicators including EMA (period 20 and 50), RSI (period 14), ATR (volatility), and the volume ratio to the 20-day moving average.
- **FR-06 (Regime Agent): The structured language model is responsible for analyzing the overall market situation (Trending Bullish, Trending Bearish, Ranging/Choppy, High Volatility Panic).
- **FR-07 (Pydantic Structured Output):** The agent's response must be strictly validated in the form of a Pydantic data model that includes `regime', `confidence' (between 0 and 1), `recommended_action' and `reasoning' fields in technical language.
- **FR-08 (safe fallback system):** In case of network error, response timeout or artificial intelligence output validation error, the system automatically switches to the safe default state (not entering a new position).

### 1.3. Independent Risk Engine
- **FR-09 (ceiling value of each order):** No order should exceed 500,000 Tomans (10% of the total initial capital).
- **FR-10 (portfolio commitment ceiling):** Maximum 60% of the total value of the portfolio (3,000,000 Tomans) can be simultaneously involved in crypto assets and at least 40% must be kept in cash in the form of Tomans.
- **FR-11 (definite loss limit and profit limit):** apply a maximum loss limit of 2% and a target profit limit of 3.5% for all positions.
- **FR-12 (Max Drawdown ceiling):** If the account value deviates more than 5% from its peak value, all new transactions are stopped and open positions are evaluated.
- **FR-13 (daily loss limit):** The maximum allowed loss during 24 hours is equivalent to 200,000 Tomans (4% of the account).
- **FR-14 (Emergency Cancellation Protection Shield):** Ability to immediately cancel all open orders and prevent entry into risky transactions.

### 1.4. Order registration and execution (Execution & Exchange Adapter)
- **FR-15 (restricted order registration / market):** Send a secure order registration request to the `/v1/account/orders' endpoint using the `x-api-key' header.
- **FR-16 (Adjustment of order status):** Order ID tracking (`clientOrderId` / `orderId`) and filling status inquiry (Fills) and management of partially filled orders (Partial Fills).
- **FR-17 (final settlement in Tomans):** Exclusive module to close all positions and convert assets to Tomans in the final hours of the hackathon.

---

## 2. Non-Functional Requirements

- **NFR-01 (Validation Security):** Non-disclosure of API keys and Secrets in source code, Git commits and log files. Dedicated use of `.env' environment variables.
- **NFR-02 (Typestatics and Code Quality):** Full typehint compliance in Python, compatibility with Python 3.12, and use of Pydantic for data validation.
- **NFR-03 (Full Traceability and Auditability):** Recording of each event, signal, AI agent status and risk engine responses in JSONL structured log format.
- **NFR-04 (Reproducibility):** Ability to accurately reproduce backtest results by match judges using a simple `scripts/run_backtest.py' script.
- **NFR-05 (Automated Testability):** Covering Unit Tests with Pytest using Mock for exchange responses so that no real order is sent when the tests are run.