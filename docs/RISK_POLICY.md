# Risk management policy and safety protocols (Risk Management Policy)

This document compiles the framework of governance and definitive rules for the Risk Management Engine (Independent Risk Engine). The rules of this document are inescapable and have absolute precedence over all artificial intelligence outputs and algorithmic signals.

---

## 1. Deterministic Risk Limits table

| Control parameter | Set value Computational basis Action in case of violation
|---|---|---|---|
| **Maximum value of one order** | 500,000 Tomans 10% of the initial capital of 5 million Veto order before sending
| **Maximum simultaneous positions** | 3 positions Diversifying the asset portfolio Refusal to reopen the fourth position
| **Maximum portfolio commitment** | 60% (3 million Tomans) | Maintaining at least 40% liquidity in Tomans Stopping new purchase orders
| **Maximum drawdown of the total account (Max Drawdown)** | 5.0% (250,000 Tomans) | Maintaining the principle of capital in the competition Complete stop of the trading system
| **Maximum daily loss (Daily Loss)** | 200,000 Tomans Prevent market movement damage Suspension of transactions until 00:00 am
| **Loss limit of each transaction (Stop Loss)** | 2.0% Early exit from unsuccessful trades Immediate dispatch of limited sales order
| ** Profit limit of each transaction (Take Profit)** | 3.5% Fixing the profit above the fee Send target sales order
| **Maximum price slippage** | 0.30% Avoiding bad performance in fluctuations Cancel the order if the quote changes
| **Maximum data staleness** | 60 seconds Ensuring decision making with live data Order rejection until data update
| **consecutive errors of the exchange (Consecutive Errors)** | 3 errors Dealing with network outage or API Entering the state of emergency stop (Emergency Halt).

---

## 2. Priority and Decision Hierarchy

```
[ Wallex market data ]
          │
          ▼
[ Quantitative feature extraction ]
          │
          ▼
[ Artificial intelligence agent (Identify the market regime) ]
          │
          ▼
[ Strategy engine (Suggested signal generation) ]
          │
          ▼
┌───────────────────────────────────────────┐
│     Independent risk management engine (Risk Gate)     │
│ 1. Do the order limit less than 500k Is it Toman?     │
│ 2. Is the portfolio less than 60% committed?     │
│ 3. Is the drawdown of the account less than 5%?       │
│ 4. Is the market allowed in the white list?        │
│ 5. Is the market spread less than 0.35%?       │
└───────────────────────────────────────────┘
          │
     ┌────┴────┐
   Confirm rejection (VETO)
     │         │
     ▼         ▼
[Send to the exchange] [Record in the log the reasons for rejecting the transaction]
```

---

## 3. End-of-Competition Protocol

According to Clause 10 of the competition goals, all crypto assets must be converted into **Tomans (TMN)** at the end of the competition. The definitive implementation steps of this protocol are as follows:

1. **Automatic stop of purchases (T - 3 Hours):** 3 hours before the end of the hackathon, the engine will block the sending of any new purchase orders.
2. **Cancellation of open orders:** All open buy and sell orders pending in the exchange are canceled and balances are released.
3. **Wallet balance adjustment:** Query the actual balance of currencies from `/v1/account/balances`.
4. **Staircase sales in Tomans:** 
   - For each asset in the basket, the available amount is checked.
   - Selling using limit orders on the highest purchase price (`Bid Price') is done intelligently and without sudden dumping to minimize slippage.
5. Final audit of profit and loss (Final P&L Reconciliation): The final report of Tomani cash balance, the amount of definite realized profit or loss, and deducted fees is extracted and stored.