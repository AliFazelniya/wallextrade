# Auditing the account structure and microstructure of Wallex Exchange (Phase 26 Wallex Exchange Mechanics)
## Wallex Competition Account Architecture, Order Types & Microstructure Audit

> **Repository:** [`wallex`](file:///root/starcoach-hack/wallex)  
> **Research branch:** `research/phase26-forensic-validation`  
> **Frozen base commit:** [`b494d60e211497f47ef3b79d6ae79a0726471172`](file:///root/starcoach-hack/wallex)  
> **Official documentation reference:** Public endpoints and documentation of Wallex developers (`api.wallex.ir`)  
> **Status:** ✅ **Complete transparency of server capabilities against client implementation**

---

## 1. Evaluation of the ordering capabilities in the official Valax API (Server-Side Capabilities)

A careful examination of the official documentation and the response schema of the Wallex API (`https://api.wallex.ir`) shows:

### a) Types of orders supported in Spot Orders:
Contrary to the simplistic assumptions in early reports that claimed there were no conditional orders on Wallex, the Wallex server supports the following types of spot transactions:
1. **`LIMIT`**: A regular order of a certain price enters the order book.
2. **`MARKET`**: The order is filled at the best current market price (allowed only on some symbols).
3. **`STOP_LIMIT'**: conditional order that is activated when the price of the last market transaction reaches the **`stopPrice'** parameter and registers a limit order.
4. **`STOP_MARKET'**: A conditional order that immediately turns into a Market order upon reaching `stopPrice'.
5. **Condition Specific Fields:** The `stopPriceCondition' parameter determines the activation condition (price is higher or lower than the trigger level).

### b) Capabilities of accrual/margin transactions (Margin Services):
In the Margin section and Wallex credit contracts, special fields **`"stop_loss"`** and **`"take_profit"`** are embedded at the server level for automatic closing of positions.

---

## 2. Reasons for maintaining client-side stop loss triggers in the trading robot (Client-Side Stop Logic)

If Wallex supports `STOP_LIMIT`, why does our trading system still use **client triggers**?
1. **Not implementing ``stopPrice'' field in the existing client:** In the class [`WallexClient.place_order'](file:///root/starcoach-hack/wallex/src/data/client.py#L160), the request body only contains `symbol, type, side, price, quantity' and the `stopPrice' field is not sent to the server.
2. **Liquidity risk in extreme fluctuations of the Iranian market:** In ``STOP_LIMIT'' orders on the server side, in case of a sudden price drop, the price may cross the limit level and the order will remain in the queue without being filled (Slippage Slip-through).
3. **Limitation of allowed race symbols:** In key symbol **`SOLTMN`**, Market order is disabled (`supports_market_order = false`), so server `STOP_MARKET` orders on this symbol will be rejected.
4. **Technical Conclusion:** Using real-time monitoring and client-side fast exit order registration with slip buffer is the most reliable and robust approach in the race.

---

## 3. Table of restrictions and specifications of the microstructure of allowed competition symbols

Based on a direct extraction from [`config/allowed_markets.json`](file:///root/starcoach-hack/wallex/config/allowed_markets.json):

| Trading symbol | The Persian name of the market Minimum order value (TMN) | Price step (Tick Size) | Decimal accuracy of volume Market order support Maker's fee | Taker fee |
|---|---|:---:|:---:|:---:|:---:|:---:|:---:|
| **BTCTMN** | Bitcoin - Toman | 50,000 | 1 TMN 8 decimal places **Yes (Active)** | 0.25% 0.30%
| **ETHTMN** | Ethereum - Toman | 50,000 | 1 TMN 5 decimal places **Yes (Active)** | 0.25% 0.30%
| **SOLTMN** | Solana - Toman 50,000 | 1 TMN 5 decimal places ❌ **No (Limit only)** | 0.25% 0.30%

> [!WARNING]
> **Critical note for the competition:** In the `SOLTMN' symbol, because the Market order is inactive, the bot should not use the `MARKET' type in emergency exits; Rather, he should use ``LIMIT'' order with a deviation price below the best bid (Aggressive Limit / Taker).

---

## 4. Competitive account status and official questions require approval by the organizers

Currently based on the competition structure:
- **Type of account:** Tomani spot account with a balance of 5,000,000 Tomans in cash.
- **Trading validity:** Not using margin accrual leverage and adherence to cash spot transactions.
- **Lack of native Post-Only support:** No official flag for `POST_ONLY' is documented in SpotWallx API; Order formation is ensured exclusively by setting the price below the best ask (in buying) or above the best bid (in selling).

### List of official questions for hackathon organizers:
1. During the 72 hours of the match, is it allowed to use conditional ``STOP_LIMIT'' spot orders and is it valid in referee monitoring?
2. If the internet of the team's server is down, is it possible to register the limit on the server side as crash insurance?
3. Is the competition account fee rate calculated exactly according to the level 1 user (0.25% / 0.30%) or is the special competition discount applied?