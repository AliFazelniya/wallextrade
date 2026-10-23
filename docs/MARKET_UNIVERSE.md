# Defining and refining the valid trading universe (Market Universe & Eligibility)

This document describes the engineering process, criteria and results of refining active symbols on the Wallex exchange.

---

## 1. Filtering Methodology

From a total of **373 active markets** in the Wallex exchange, in order to comply with the hackathon rules, control slippage and reduce liquidity risk, the following hierarchical filters have been applied:

```
[ All Wallex symbols: 373 ]
       │
       ▼  Filter 1: Toman-based currency pairs (Quote Asset == 'TMN')
[ Toman symbols: 187 ]   ── (186 Tetri symbols have been temporarily removed)
       │
       ▼  Filter 2: Active order book depth and valid quote price (Bid > 0, Ask > 0)
[ Icons with live order book: 166 ]
       │
       ▼  Filter 3: The volume of 24-hour transactions is more than 5 billion tomans
[ Symbols with high liquidity: 24 ]
       │
       ▼  Filter 4: The maximum allowed spread of supply and demand is less than 0.35%.
[ The final authorized trading world: 13 symbols ]
```

---

## 2. List of selected symbols in the allowed world (`allowed_markets.json`)

The following symbols have been selected as prime candidates for monitoring and executing trades:

| Symbol | Persian name 24-hour volume (tomans) | Spread | Market order support Validation status
|---|---|---|---|---|---|
| **USDTTMN** | Tether - Toman | 235.78 billion 0.02% | Yes Confirmed
| **BTCTMN** | Bitcoin - Toman | 113.81 billion 0.00% | Yes Confirmed
| **ETHTMN** | Ethereum - Toman | 76.93 billion 0.00% | Yes Confirmed
| **XAUTTMN** | Tether gold - Toman | 33.51 billion 0.03% | Yes Confirmed
| **PEPETMN** | Pepe - Toman 123.49 billion 0.04% | No (Limit only) | Confirmed
| **PUMPTMN** | Pump - toman | 90.34 billion 0.08% | No (Limit only) | Confirmed
| **USOONTMN** | Yusun - Toman | 71.91 billion 0.21% | No (Limit only) | Confirmed
| **BNBTMN** | Binance Coin - Toman | 55.17 billion 0.31% | No (Limit only) | Confirmed
| **DOGETMN** | Dogecoin - Toman 40.51 billion 0.15% No (Limit only) | Confirmed
| **XRPTMN** | Ripple - Toman | 36.90 billion 0.00% | No (Limit only) | Confirmed
| **SOLTMN** | Solana - Toman 29.06 billion 0.19% No (Limit only) | Confirmed
| **TRXTMN** | Tron - Toman 12.64 billion 0.16% | No (Limit only) | Confirmed
| **SUITMN** | Sui - Toman 8.36 billion 0.24% | No (Limit only) | Confirmed

---

## 3. Excluded Markets and Exceptions (`market_restrictions.json`)

1. **Tether currency pairs (`*USDT'):** All 186 symbols have been excluded from the trading world for the time being due to the added exchange rate risk and the double fee of buying Tether.
2. **Markets with wide spreads (`Spread > 0.35%'):** Symbols such as `ZECTMN' (spread 0.95%), `DASHTMN' (spread 0.36%), `STMN' (spread 0.64%) and `XMRTMN' (spread 0.63%) were filtered out due to high probability of price slippage.
3. **Inactive markets in Hackathon credit account:** This list will be loaded and blocked as soon as the user provides the full text of the brief in the `credit_account_inactive_symbols' array.

No symbol will be tradable until it conforms to the latest list of restrictions.