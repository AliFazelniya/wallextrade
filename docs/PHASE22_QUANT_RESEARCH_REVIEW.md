# Review of quantitative research, trading algorithms and competitive artificial intelligence architecture (Phase 22)
## Quantitative Research Review, Literature Matrix & Strategy Foundations

> **Project:** Wallex Agentic AI Hackathon  
> **Research branch:** `research/phase22-discovery`  
> **Frozen base commit:** [`b494d60e211497f47ef3b79d6ae79a0726471172`](file:///root/starcoach-hack/wallex)  
> **Target trading horizon:** 72 hours of continuous competition  
> **Initial capital:** 5,000,000 Tomans  
> **Status of live transactions:** `live_execution_authorized = False' (exact research and simulation only)

---

## 1. Introduction and statement of the research problem (Problem Statement)

The documentary findings of phase 21 showed that the frozen trend strategy (`RegimeMomentumStrategy') was profitable in the continuous 90-day backtest (+31,555 Tomans / +0.63%), but in **29 independent 72-hour competition windows**, it had a negative performance (**-28,871 Tomans loss**) and a negative average return (**-0.0199%**).

### Finding the root causes of strategy failure in the horizon of the 3-day competition:
1. **Mismatch between the time horizon of the strategy and the competition horizon (Horizon Mismatch):**  
   A trend strategy with a profit limit of 4.0% and a loss limit of 2.0% requires the position to be open within 24 to 72 hours; While the match ends at the end of 72 hours.
2. **Boundary Liquidation Drag:**  
   In 11 windows out of 29 windows, the open position was liquidated in the last second with the Market Taker order (fee 0.30% + slippage 0.15%) and incurred **-11,075 Tomans loss** alone.
3. **Fee-to-Payoff Friction in crypto exchanges:**  
   Wallex's level one fee (0.25% maker and 0.30% taker) along with 0.15% slippage brings the round-trip friction per trade to **0.70% to 0.90%**. On short-term timeframes (15 minutes), price volatility averages only 1.0% to 2.0%, and exchange friction eats up more than 50% of gross profit.
4. **Inactivity in 34.5% of the time (Zero-Trade Inactivity):**  
   The conservative veto of the market regime caused the robot not to make a single trade in 10 competition windows, which will be penalized with algorithmic activity points in the arbitration competition.

The purpose of this document is to provide an academic and industrial research review to discover proven solutions, select strategy candidates, and compile a research evidence matrix.

---

## 2. Academic & Industry Literature Review

### 2.1. Meta-tagging and the triple barrier method in high-fee markets
* **Main reference:** Marcos López de Prado, *Advances in Financial Machine Learning*, Wiley (2018), Chapters 3 & 4.
* **Key findings of the research:**  
  Lopez de Prado shows that Directional ML models fail when faced with exchange fees. The proposed solution is Meta-Labeling:
  - **Primary Model:** A technical rule or simple process that determines the direction of entry (Long / Short).
  - **Secondary Meta-Model:** A machine learning model (such as XGBoost or Random Forest) that predicts: *"Given the current microstructure of the market and spread, is the probability of success of this transaction high enough that the gross return will pass the fee and slippage barrier?"*
  - **Cost-Aware Triple Barrier:** profit limit and loss limit should be set asymmetrically with respect to the fee; If the potential profit is less than the round trip cost, the trade tag is automatically zero (no entry).

### 2.2. Finite-Horizon Optimal Liquidation
* **Main reference:** Almgren, R., & Chriss, N. (2000), *Optimal execution of portfolio transactions*, Journal of Risk, 3(2), 5-39.  
* **Contemporary reference:** Guéant, O. (2016), *The Financial Mathematics of Market Liquidity: From optimal execution to market making*, CRC Press.
* **Key findings of the research:**  
  In problems with a definite deadline $T$ (such as a 72-hour race), the value function changes its behavior as $t \to T$ approaches. If the trader enters large orders in the closing hours, he has to settle with ticker orders and high slippage.  
  - **No-New-Entry Zone:** For the 72-hour horizon, no new position should be opened in the last 8 to 12 hours; Because there is not enough time for the trend to mature towards the profit margin.
  - **Gradual and passive withdrawal (Graceful Limit Wind-down):** From 64 hours onwards, open positions must be closed with passive limit (Maker) orders in the depth of the book so that the fee is reduced from 0.30% to 0.25% and the slippage reaches zero.

### 2.3. Volatility & Donchian Breakout in Crypto
* **Main reference:** Donchian, R. (1960), *High finance in copper*, Financial Analysts Journal.  
* **Crypto Research:** Fong, W. M., & Yong, L. H. (2005), *Chasing trends: Evidence from trend-following strategies in financial futures*.  
* **Key findings of the research:**  
  Breaking the ceiling of 20 candles (Donchian Channel) together with volume confirmation (Relative Volume $\ge 1.5$) and ADX trend indicator filter ($> 25$) is one of the strongest sources of profitability in sharp crypto moves. For a short horizon, using Time Stop after 16 candles (4 hours) prevents capital from sleeping in unsuccessful positions.

### 2.4. Return to the mean in range regimes (Range-Bound Mean Reversion & Bollinger Squeeze)
* **Main reference:** Bollinger, J. (2002), *Bollinger on Bollinger Bands*, McGraw-Hill.  
* **Key findings of the research:**  
  In no-trend regimes (Low ADX $< 20$) and Bollinger Bandwidth Squeeze, the price fluctuates between the outer bands. Entry at the break of the lower band with RSI oversold condition ($<30$) and targeting the retracement to the middle line (SMA 20) can make the range windows profitable; Provided that the distance to the center line is greater than the back and forth friction (at least 1.2%).

### 2.5. Cross-Sectional Momentum in Multi-Asset Portfolios
* **Main reference:** Jegadeesh, N., & Titman, S. (1993), *Returns to buying winners and selling losers*, Journal of Finance.  
* **Crypto Research:** Liu, Y., & Tsyvinski, A. (2021), *Risks and returns of cryptocurrency*, Review of Financial Studies, 34(6), 2689-2727.  
* **Key findings of the research:**  
  Being limited to one asset (BTC) results in a high rate of no-trade windows. By simultaneously evaluating BTC, ETH and SOL and dynamically selecting the token that has the highest short-term Sharpe ratio and the lowest spread, trading frequency is optimized and liquidity is allocated to the most potential currency.

---

## 3. Evidence matrix and evaluation of researched strategies (Research Evidence Matrix)

| The name of the algorithm / strategy Scientific and experimental resources Target market regime Appropriate time horizon Implementation complexity Sensitivity to fees Evidence in Wallex data Compatibility with the 72-hour race Priority rank
|---|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **1. Matching process with the final sail (Candidate A)** | De Prado (2018), Almgren (2000) | Stable upward trends 4 to 16 hours Average | Average | Reproduction in 90 days with high profitability Very high (fixing the loss of 11 thousand tomans) | **Priority 1** |
| **2. Danchian channel swing failure (Candidate B)** | Donchian (1960), Fong (2005) | Oscillating jumps and breakouts 2 to 8 hours down | Down (larger targets) | Hunting for extreme BTC/ETH momentum Very high (faster frequency) | **Priority 2** |
| **3. Back to the average in the range (Candidate C)** | Bollinger (2002), SmartMoney (2023) | Range, low volatility (ADX < 20) | 1 to 4 hours Average | Very high (requirement of 1.2% interest barrier) | Activation in 10 neutral windows Up (avoid passivity) | **Priority 3** |
| **4. Metamodel of machine learning and diet (Candidate D)** | De Prado (2018), Arxiv (2024) | Dynamic multimode 1 to 12 hours up | Average | The need for education without future leaks High (artificial intelligence arbitration value) | **Priority 4** |
| **5. Triple cross-sectional momentum (Candidate E)** | Liu & Tsyvinski (2021) | Multi-Asset (BTC/ETH/SOL) | 4 to 24 hours Average | Average | Solving the problem of 10 windows without transaction Very high (using all available data) | **Priority 1 Subscriber** |
| **6. Statistical co-accumulation arbitrage** | Vidyamurthy (2004) | Stacked pairs A few minutes to 2 hours Very high Super high There is no order for shorts in the spot account Inapplicable in the race **rejected** |
| **7. Active market making (Market Making)** | Avellaneda & Stoikov (2008) | Liquidity markets seconds to minutes up | The need for negative ribbit makes | Lack of data set in order book Level 2 historical | Cannot be tested on existing data **rejected** |
| **8. Deep Neural Networks LSTM/RL** | Goodfellow (2016) | General | complex nonlinear | Very high up | Extreme overfitting on 29 windows Very high stakes for the race **rejected** |

---

## 4. Rejected strategies and scientific reasons for rejecting them (Rejected Approaches)

1. **Statistical arbitrage of currency pairs (Pairs Trading / Cointegration):**  
   *Reason of rejection:* In the cash account of the Wallex competition, there is no possibility of a short selling position; Therefore, it is impossible to create a market-neutral portfolio.
2. **Market making algorithms with high spreads:**  
   *Reason of Rejection:* Accurate simulation requires quote depth data (L2/L3 Orderbook) and Wallex exchange does not pay negative rebate for maker (maker fee is 0.25%, not bonus).
3. ** Deep Reinforcement Learning (Deep Reinforcement Learning - DRL):**  
   *Reason for Rejection:* 90 days of data (8,636 candles) is too small to converge deep networks and will lead to statistical cheating and catastrophic overfitting on past history.

---

## 5. Conclusion and implementation roadmap of phase 22

Based on the matrix of research evidence, four high-priority selected strategies were identified for implementation and testing in the next steps:
- **Candidate A:** Optimized trend strategy with dynamic profit/loss limit and graceful wind-down.
- **Candidate B:** Danchian channel breakout strategy and ATR swing with short time limit.
- **Candidate C:** Mean reversion strategy in Bollinger channel for range windows.
- **Candidate E:** Multi-asset cross-sectional momentum strategy (BTC + ETH + SOL).
- **Candidate D (aggregate architecture):** Agentic Strategy Router.

The detailed document of the characteristics and mathematical formulation of these candidates will be compiled in the next document.