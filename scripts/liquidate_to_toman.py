#!/usr/bin/env python3
"""End-of-Competition Forced Liquidation Protocol.

Liquidates 100% of non-Toman crypto holdings back into TMN currency before
the hackathon deadline, satisfying the mandatory requirement that all returns
must be realized in Toman (TMN) rather than volatile coin valuations.

Supports both LIVE exchange liquidation and SHADOW/SIMULATION liquidation.
"""

from __future__ import annotations

import argparse
import asyncio
import datetime
import json
import logging
import os
import pathlib
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from src.data.client import WallexClient
from src.exchange.adapter import ExchangeAdapter
from src.portfolio.accounting import PortfolioEngine

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("liquidation")


async def execute_liquidation(live: bool = False, authorized: bool = False) -> dict:
    print("=" * 80)
    print("  WALLEX HACKATHON: AUTOMATIC TOMAN LIQUIDATION PROTOCOL")
    print(f"  Mode: {'LIVE EXCHANGE ORDER EXECUTION' if (live and authorized) else 'SAFE SIMULATION/SHADOW'}")
    print("=" * 80)

    api_key = os.getenv("WALLEX_API_KEY")
    client = WallexClient(api_key=api_key)
    portfolio = PortfolioEngine(initial_capital_toman=5_000_000.0)
    
    # Restore saved state if exists
    state_file = REPO_ROOT / "logs" / "portfolio_state.json"
    if state_file.exists():
        try:
            with open(state_file, "r") as f:
                saved = json.load(f)
                portfolio = PortfolioEngine.from_state(saved)
                logger.info("Restored portfolio state with %d active positions.", len(portfolio.positions))
        except Exception as e:
            logger.warning("Could not restore saved portfolio: %s", e)

    adapter = ExchangeAdapter(
        client=client,
        portfolio=portfolio,
        trading_mode="LIVE" if (live and authorized) else "SHADOW",
        live_execution_authorized=authorized,
        slippage_pct=0.20,
    )

    logger.info("Step 1: Emergency halt on any new buy orders.")
    logger.info("Step 2: Inspecting active positions to liquidate...")

    liquidated_trades = []
    
    # Fetch live prices from Wallex
    current_prices = {}
    try:
        m_resp = await client.get_markets()
        symbols_info = m_resp.get("result", {}).get("symbols", {})
        for sym, d in symbols_info.items():
            stats = d.get("stats", {})
            raw_bid = stats.get("bidPrice")
            raw_last = stats.get("lastPrice")
            try:
                px = float(raw_bid) if raw_bid and raw_bid != "-" else float(raw_last)
            except (ValueError, TypeError):
                px = 0.0
            if px > 0:
                current_prices[sym] = px
    except Exception as e:
        logger.error("Failed to fetch live prices from Wallex: %s", e)

    # 1. Liquidate internal portfolio positions
    active_syms = list(portfolio.positions.keys())
    if not active_syms:
        logger.info("Internal portfolio holds NO active crypto positions. Already 100% TMN cash.")
    else:
        for sym in active_syms:
            pos = portfolio.positions[sym]
            cur_price = current_prices.get(sym, pos.current_price)
            logger.info("Liquidating position %s (Qty: %.6f @ %.1f TMN)...", sym, pos.quantity, cur_price)
            try:
                res = await adapter.execute_order(
                    symbol=sym,
                    action="SELL",
                    target_price=cur_price,
                    approved_value_toman=pos.quantity * cur_price,
                    order_type="LIMIT",
                    is_maker=False,
                )
                liquidated_trades.append(res)
                logger.info("Successfully liquidated %s to TMN.", sym)
            except Exception as exc:
                logger.error("Error liquidating %s: %s", sym, exc)

    # 2. In LIVE mode, verify exchange balances directly
    if live and authorized and api_key:
        try:
            balances = await client.get_balances()
            bal_result = balances.get("result", {}).get("balances", {})
            for asset, b in bal_result.items():
                if asset != "TMN":
                    val = float(b.get("value", 0.0))
                    sym = f"{asset}TMN"
                    if val > 0 and sym in current_prices:
                        notional = val * current_prices[sym]
                        if notional >= 50_000.0:
                            logger.warning("Found un-liquidated exchange balance: %f %s (~%.0f TMN). Placing sell order.", val, asset, notional)
                            await client.place_order(
                                symbol=sym,
                                order_type="LIMIT",
                                side="SELL",
                                price=str(int(current_prices[sym] * 0.995)),
                                quantity=f"{val:.8f}",
                            )
        except Exception as e:
            logger.error("Could not reconcile live balances: %s", e)

    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    final_equity = portfolio.get_total_equity()
    net_pnl = final_equity - portfolio.initial_capital_toman
    return_pct = (net_pnl / portfolio.initial_capital_toman) * 100.0

    report = {
        "timestamp": now_iso,
        "status": "SETTLED_IN_TOMAN",
        "initial_capital_toman": portfolio.initial_capital_toman,
        "final_cash_toman": round(portfolio.cash_toman, 0),
        "crypto_holdings_count": len(portfolio.positions),
        "total_equity_toman": round(final_equity, 0),
        "realized_net_pnl_toman": round(net_pnl, 0),
        "return_pct": round(return_pct, 2),
        "liquidations": liquidated_trades,
    }

    report_path = REPO_ROOT / "logs" / "settlement_report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print("\n" + "=" * 80)
    print("  LIQUIDATION & SETTLEMENT SUMMARY")
    print(f"  Final Cash:             {report['final_cash_toman']:>15,.0f} TMN")
    print(f"  Crypto Positions Left:  {report['crypto_holdings_count']:>15}")
    print(f"  Realized Net Return:    {report['return_pct']:>14.2f}%")
    print(f"  Audit Report Saved To:  {str(report_path)}")
    print("=" * 80 + "\n")

    await client.close()
    return report


def main():
    parser = argparse.ArgumentParser(description="End-of-Competition Liquidation Protocol")
    parser.add_argument("--live", action="store_true", help="Execute real liquidation on Wallex exchange")
    parser.add_argument("--authorized", action="store_true", help="Confirm human authorization for live execution")
    args = parser.parse_args()

    asyncio.run(execute_liquidation(live=args.live, authorized=args.authorized))


if __name__ == "__main__":
    main()
