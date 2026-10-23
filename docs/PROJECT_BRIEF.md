# Project summary: Algorithmic trading system based on agent-oriented artificial intelligence (Starcoach × Wallex)

## 1. Introducing the event and purpose
This project has been designed and implemented as a comprehensive solution for Agentic AI Hackathon jointly by **Starcoach** and **Wallex**.

The main goal is to develop an automated, reproducible, algorithmic trading engine based on quantitative trading principles and intelligent decision-making based on agentic AI, which:
1. Get live and historical market data from Wallex exchange.
2. Identify low-risk trading positions by accurately separating tasks (Regime Classification, Signal Generation, Risk Management).
3. Apply deterministic risk controls.
4. Execute orders automatically through Wallex API.
5. It has the ability to perform historical backtesting and shadow testing.
6. At the end of the competition, liquidate all assets successfully and with the least price slippage to **Toman (TMN)**.

---

## 2. Competition specifications and conditions

- **Initial nominal capital:** 5,000,000 Tomans (allocated for each team).
- **Competition duration:** 3-day intensive event.
- **Basic settlement unit:** Toman (TMN) - At the end of the period, all assets must be converted into Toman.
- **Trading account:** Wallex exchange credit/prop trading account with a limit of 5 million Tomans.
- **evaluation criteria:**
  - **Actual financial performance (Net P&L):** Profitability after deducting Wallex exchange fee and accounting for actual slippage.
  - **Risk and Drawdown Control (Max Drawdown & Risk Control):** Capital management and preventing a sharp drop in capital.
  - **Technical quality and software architecture:** Separation of modules, testability, typehint, documentation and engineering structure.
  - **Significant use of artificial intelligence (Agentic AI):** Not being limited to a simple script and effective use of agents in the classification of the market situation (Market Regime), strategy selection and dynamic management of parameters.
  - **Ability to reproduce and clearly record decisions (Audit Trail & Reproducibility):** Complete JSONL log recording for each decision and the possibility of independent review by judges.

---

## 3. Multiple engineering team roles
The current system is the result of the coordination of the following specialized roles:
- **Quantitative Researcher:** Modeling of market behavior, analysis of microstructure and rate of return.
- **Algo Strategist:** Designing entry/exit logic based on momentum and return to the mean.
- Agent-oriented artificial intelligence architect (Agentic AI Architect): Designing Pydantic agents framework and structured outputs.
- **Python Backend Engineer:** Development of asynchronous core (Async Engine) and modular pipeline.
- **Exchange API integration engineer:** Implementation of Valax standard client and request rate management.
- **Risk Management Engineer:** Designing an independent engine and definitive loss prevention layers.
- Validation & Backtest Engineer: Accurate cost simulation and walkforward validation.
- **QA & Technical Documentation Engineer:** Compilation of documentation and automatic test codes.