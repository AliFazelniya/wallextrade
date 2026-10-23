# Comprehensive and audited guide for interacting with the Wallex programming interface (Wallex API Audit & Reference)

This document is the definitive, audited and tested technical reference for stable communication, public data query and secure order submission to Wallex Exchange.

---

## 1. Public profile and authentication protocol
- **Base URL:** `https://api.wallex.ir`
- **Data exchange format:** JSON (`Content-Type: application/json`)
- **Private endpoint authentication method:** header `x-api-key: YOUR_API_KEY` (checked: sending invalid key leads to error `{"code":1201,"message":"invalid API key format"}`).
- **Server time zone:** `Asia/Tehran`

---

## 2. Fee structure (Wallex level 1 official audit)

According to the official documents of the SpotWallex market fees for the volume of level one transactions (transactions below 10 million Tomans in the last 30 days):

| The market Maker's fee | Taker fee | Description
|---|---|---|---|
| **Toman-based markets (`*TMN`)** | **0.25%** (0.0025) | **0.30%** (0.0030) | Limit orders as Maker and market/emergency orders as Taker
| **Markets based on Tether (`*USDT`)** | **0.10%** (0.0010) | **0.13%** (0.0013) | Due to the addition of friction, the conversion of Toman to Tether is currently blocked
| **Instant transaction (OTC Easy Trade)** | 0.00% | 0.00% | Direct commission is zero, but there is a high implied spread in the bid/ask rate

---

## 3. Public Endpoints

### 3.1. List of markets and metadata (Markets Metadata)
- **Path:** `GET /v1/markets`
- **Authentication:** No token required (public)
- **Audit findings:**
  - 373 active markets are reported (187 Toman symbols and 186 Tetri symbols).
  - `isMarketTypeEnable` field: it is equal to `true` only for **4 symbols** (`USDTTMN`, `BTCTMN`, `ETHTMN`, `XAUTTMN`) (that is, it is possible to send an order with market price `MARKET`). All other symbols (`SOLTMN`, `DOGETMN`, `PEPETMN`, ...) **only support `LIMIT` limit order**.
  - The minimum order value (`minNotional') in all Toman currency pairs is equivalent to **50,000 Tomans**.

### 3.2. Order book and market depth (Order Book Depth)
- **Path:** `GET /v1/depth?symbol={symbol}`
- **parameters:** `symbol` (example: `BTCTMN`)
- **Response speed:** The average is below 200 milliseconds. The output structure consists of `bid` and `ask` arrays sorted by best price.

### 3.3. Get historic candlestick data (TradingView UDF History)
- **Path:** `GET /v1/udf/history?symbol={symbol}&resolution={res}&from={from_ts}&to={to_ts}`
- **Key finding of phase 4 audit:**
  - Sending `resolution=1` results in an empty response.
  - Sending `resolution=15` returns raw data with a time step of **60 seconds (1 minute)** up to 27,345 candles. The system client is responsible for resampling to 15-minute candles automatically.
  - sending `resolution=60` will return 1 hour real data (719 candelas in 30 days).

---

## 4. Private endpoints and order management (Private Endpoints)

### 4.1. Balance inquiry
- **Path:** `GET /v1/account/balances`
- **Header:** `x-api-key: YOUR_KEY`
- **Structure of the answer:** Separation of assets into two parts: free balance (`value') and locked balance in open orders (`locked').

### 4.2. Place Order
- **Path:** `POST /v1/account/orders`
- **Header:** `x-api-key: YOUR_KEY`
- **JSON body:**```json
{
  "symbol": "BTCTMN",
  "type": "LIMIT",
  "side": "BUY",
  "price": "22200000000",
  "quantity": "0.00002250",
  "clientOrderId": "LIMIT-a1b2c3d4e5f6"
}
```

### 4.3. Inquiring about open orders (Open Orders) and canceling orders (Cancel Order)
- **Request open orders:** `GET /v1/account/open-orders`
- **Order cancellation:** `DELETE /v1/account/orders?clientOrderId={clientOrderId}` or `orderId={orderId}`.