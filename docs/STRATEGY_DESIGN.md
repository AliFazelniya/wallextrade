# Quantitative strategy architecture design and agent-based artificial intelligence model (Quantitative Strategy Design)

This document defines the technical details, mathematical formulation, agent architecture and definitive rules of entry and exit of the trading strategy.

---

## 1. Core Hypothesis of Strategy

In digital currency markets, price momentum (Momentum) overcomes exchange fees in sustained bullish conditions. However, in choppy/ranging or falling markets, trend-following signals suffer losses due to to-and-fro fluctuations.

The solution of this system is **Two-Tier Hybrid Architecture**:
1. **Intelligent decision-making layer (AI Regime Agent):** Analyzing the macro situation and determining the market regime based on statistical characteristics.
2. **Deterministic Quantitative Engine:** Accurate generation of entry/exit signals based on clear and tested mathematical rules.
3. **Risk monitoring and veto layer (Independent Risk Engine):** Complete inhibition of any signal in case of violation of capital limits.

---

## 2. Quantitative indicators and extracted features (Feature Engineering)

The input data is extracted from 15-minute candles (`resolution="15"`):
- **Trend direction:** $EMA_{fast}(20)$ and $EMA_{slow}(50)$.
  $$\Delta EMA = \frac{EMA_{20} - EMA_{50}}{EMA_{50}} \times 100$$
- **Momentum strength:** 14 period relative strength index ($RSI_{14}$).
- **Normalized volatility:** The ratio of the average real range to the closing price:
  $$ATR\% = \frac{ATR_{14}}{Close} \times 100$$
- **Trading volume coefficient:** The ratio of the current candle volume to the average volume of the last 20 candles ($Volume / SMA(Volume, 20)$).
- **Order Book Imbalance:**
  $$OBI = \frac{BidVolume - AskVolume}{BidVolume + AskVolume}$$

---

## 3. The role of an artificial intelligence agent (Agentic AI Market-Regime Classifier)

Instead of blindly predicting the price, the artificial intelligence agent analyzes the above quantitative characteristics and responds in the form of Pydantic's structured schema:

```python
class MarketRegime(str, Enum):
  BULLISH_TREND = "BULLISH_TREND"
  BEARISH_TREND = "BEARISH_TREND"
  CALM_RANGE = "CALM_RANGE"
  VOLATILE_PANIC = "VOLATILE_PANIC"


class RegimeAnalysisOutput(BaseModel):
  regime: MarketRegime
  confidence: float = Field(ge=0.0, le=1.0)
  volatility_assessment: str
  strategy_permitted: bool
  target_symbols: list[str]
  reasoning: str
```

### Appropriate behaviors for each situation:
- **`BULLISH_TREND`:** Trend acceleration strategy is activated. Entering buy positions on high-volume symbols is allowed.
- **`BEARISH_TREND`:** Opening any new buy positions is **prohibited**. Assets are kept in cash in the form of Tomans.
- **`CALM_RANGE`:** Mean Reversion sub-strategy is activated with a smaller volume (maximum 250,000 Tomans).
- **`VOLATILE_PANIC`:** All transactions are suspended as an emergency and the risk engine is activated.

---

## 4. Rules of entry and exit of the main strategy (Regime-Momentum Strategy)

### 4.1. Entry Rules:
A valid buy signal is issued when **all the following conditions are met simultaneously**:
1. The market regime confirmed by AI equals `BULLISH_TREND` with confidence above 70% (`confidence >= 0.70`).
2. The trend line is $EMA_{20} > EMA_{50}$.
3. $RSI_{14}$ index should be between 50 and 68 (confirmation of bullishness without entering extreme oversaturation).
4. The volume of the last candle should be at least 1.2 times the moving average of the volume ($VolumeRatio \ge 1.2$).
5. The order book spread of the symbol should be less than 0.35%.

### 4.2. Exit conditions and position management (Exit Rules):
- **Dynamic profit limit (Take Profit):** 3.5% higher than the average purchase price.
- **Stop Loss:** 2.0% lower than the average purchase price (guaranteeing capital preservation).
- **Trend Based Exit:** If $EMA_{20}$ breaks below $EMA_{50}$ or the market regime changes to `BEARISH_TREND', the position is immediately sold with a limit order.

---

## 5. Safe Fallback Engine (Safe Fallback Engine)

If at the moment of decision:
- Calling artificial intelligence has a time delay (Timeout more than 5 seconds),
- The artificial intelligence answer does not pass the validation of the Pydantic model,
- or a network error occurs,

The system immediately goes to **Safe Fallback**:
- No new position is opened (`Action = HOLD`).
- The existing positions are monitored only on the basis of the loss limit and the definite profit limit.
- The occurrence of an error is recorded with a code and details in the decision log file.