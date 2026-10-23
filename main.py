#!/usr/bin/env python3
"""Wallex Agentic AI Trading System - Main Unified CLI Entrypoint.

Starcoach x Wallex Agentic AI Hackathon
Official Repository Entrypoint.

Modes:
  --mode backtest   : Run walk-forward backtest over historical Wallex candles
  --mode shadow     : Run live-market shadow trading with Agentic AI and live dashboard
  --mode live       : Run real order execution on Wallex (requires --authorized)
  --mode liquidate  : Convert 100% of crypto holdings into Toman before deadline
  --mode mcp        : Launch Wallex Model Context Protocol (MCP) Server for LLM agents
  --mode test       : Run test suite to verify mathematical and governance integrity

Usage:
  python main.py --mode shadow
  python main.py --mode backtest --symbols BTCTMN ETHTMN
  python main.py --mode liquidate
"""

from __future__ import annotations

import argparse
import asyncio
import os
import subprocess
import sys
from pathlib import Path
from typing import List

REPO_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO_ROOT))

from src.agents.agentic_trader import AgenticTrader
from src.data.client import WallexClient
from src.exchange.adapter import ExchangeAdapter
from src.mcp.server import WallexMCPServer
from src.mcp.tools import WallexMCPToolSet
from src.monitoring.dashboard import LiveTerminalDashboard
from src.monitoring.logger import DecisionLogger
from src.portfolio.accounting import PortfolioEngine
from src.risk.engine import RiskEngine


async def run_shadow_or_live_session(
    mode: str = "SHADOW",
    authorized: bool = False,
    symbols: List[str] = None,
    cycles: int = 5,
    interval_seconds: int = 5,
):
    target_symbols = symbols or ["BTCTMN", "USDTTMN", "ETHTMN", "SOLTMN"]
    api_key = os.getenv("WALLEX_API_KEY")
    client = WallexClient(api_key=api_key)
    portfolio = PortfolioEngine(initial_capital_toman=5_000_000.0)

    # Restore saved state if exists
    state_file = REPO_ROOT / "logs" / "portfolio_state.json"
    if state_file.exists():
        try:
            import json
            with open(state_file, "r") as f:
                portfolio = PortfolioEngine.from_state(json.load(f))
        except Exception:
            pass

    risk = RiskEngine(
        max_single_order_toman=500_000.0,
        max_portfolio_exposure_pct=60.0,
        max_drawdown_pct=5.0,
        allowed_symbols=set(target_symbols),
    )
    adapter = ExchangeAdapter(
        client=client,
        portfolio=portfolio,
        trading_mode=mode.upper(),
        live_execution_authorized=authorized,
        allowed_symbols=set(target_symbols),
    )
    toolset = WallexMCPToolSet(client, portfolio, risk, adapter)
    logger = DecisionLogger(log_path="logs/trading_decisions.jsonl")
    trader = AgenticTrader(toolset=toolset, decision_logger=logger)

    print(f"\nStarting {mode.upper()} session for {cycles} cycles across {target_symbols}...\n")

    for cycle in range(1, cycles + 1):
        res = await trader.run_cycle(target_symbols)
        overview = res["observations"].get("market_overview", {})
        port_status = res["observations"].get("portfolio", {})
        decisions = res.get("decisions", [])

        # Render Live Terminal Dashboard
        LiveTerminalDashboard.render(
            mode=mode,
            portfolio_status=port_status,
            markets_overview=overview,
            recent_decisions=decisions,
            cycle=cycle,
            max_cycles=cycles,
            triangular_arbitrage=res["observations"].get("triangular_arbitrage"),
        )

        # Save portfolio state periodically
        try:
            import json
            with open(state_file, "w") as f:
                json.dump(portfolio.export_state(), f, indent=2)
        except Exception:
            pass

        if cycle < cycles:
            await asyncio.sleep(interval_seconds)

    await client.close()
    print(f"\n{mode.upper()} session complete. Decision audit trail recorded to logs/trading_decisions.jsonl\n")


async def run_arbitrage_scanner():
    """Scans and renders real-time cross-market triangular discrepancies."""
    client = WallexClient()
    try:
        from src.strategy.triangular_arbitrage import TriangularArbitrageStrategy
        strat = TriangularArbitrageStrategy()
        markets = await client.get_markets()
        symbols_data = markets.get("result", {}).get("symbols", {})
        discrepancies = strat.scan_all_supported(symbols_data)
        print("\n" + "=" * 100)
        print("  WALLEX REAL-TIME TRIANGULAR ARBITRAGE & CROSS-RATE SCANNER")
        print("=" * 100)
        print(f"  {'Coin':<6} | {'TMN Price':<18} | {'USDT Price':<12} | {'Synthetic TMN':<18} | {'Discrepancy':<12} | {'Net Edge':<10} | {'Status'}")
        print("-" * 100)
        for d in discrepancies:
            status = "\033[92mACTIONABLE (" + d.recommended_action.value + ")\033[0m" if d.is_actionable else "Within Fee Friction"
            print(f"  {d.base_coin:<6} | {d.tmn_price:>14,.0f} TMN | {d.usdt_price:>10.2f} $ | {d.synthetic_tmn_price:>14,.0f} TMN | {d.discrepancy_pct:>+10.2f}% | {d.net_edge_pct:>+8.2f}% | {status}")
        print("=" * 100 + "\n")
    finally:
        await client.close()


def run_tests():
    print("Running automated test suite via Pytest...")
    ret = subprocess.run([sys.executable, "-m", "pytest", "tests/", "-v"])
    sys.exit(ret.returncode)


def main():
    parser = argparse.ArgumentParser(
        description="Wallex Agentic AI Algorithmic Trading System",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        "--mode",
        choices=["shadow", "live", "backtest", "liquidate", "mcp", "test", "web", "report", "arbitrage"],
        default="shadow",
        help=(
            "Operational mode:\n"
            "  shadow    : Real-time simulation on live Wallex market data\n"
            "  live      : Real order submission on Wallex (requires --authorized)\n"
            "  backtest  : Historical backtesting over TradingView UDF candles\n"
            "  liquidate : Convert all crypto holdings 100% to Toman\n"
            "  mcp       : Run the Wallex Model Context Protocol (MCP) Server\n"
            "  test      : Execute complete unit and integration test suite\n"
            "  web       : Launch interactive live local Web Dashboard\n"
            "  report    : Generate standalone HTML audit report for hackathon judges\n"
            "  arbitrage : Scan real-time cross-currency triangular mispricings\n"
        ),
    )
    parser.add_argument("--symbols", nargs="+", default=["BTCTMN", "USDTTMN", "ETHTMN", "SOLTMN"], help="Target symbols")
    parser.add_argument("--cycles", type=int, default=3, help="Number of operational cycles (for shadow/live)")
    parser.add_argument("--interval", type=int, default=4, help="Interval between cycles in seconds")
    parser.add_argument("--authorized", action="store_true", help="Authorize live order placement")
    parser.add_argument("--port", type=int, default=8080, help="Port for web dashboard server")

    args = parser.parse_args()

    if args.mode == "test":
        run_tests()
    elif args.mode == "report":
        from src.monitoring.report_generator import JudgeReportGenerator
        gen = JudgeReportGenerator(REPO_ROOT)
        out_p = gen.generate_html_report()
        print(f"\n[REPORT] Judge HTML audit report successfully generated at:\n  file://{out_p.resolve()}\n")
    elif args.mode == "web":
        from src.monitoring.web_dashboard import start_dashboard_server
        start_dashboard_server(port=args.port)
    elif args.mode == "arbitrage":
        asyncio.run(run_arbitrage_scanner())
    elif args.mode == "mcp":
        server = WallexMCPServer()
        asyncio.run(server.run_stdio_server())
    elif args.mode == "liquidate":
        from scripts.liquidate_to_toman import execute_liquidation
        asyncio.run(execute_liquidation(live=(args.mode == "live"), authorized=args.authorized))
    elif args.mode == "backtest":
        from scripts.run_backtest import main as backtest_main
        sys.argv = ["run_backtest.py"] + args.symbols
        asyncio.run(backtest_main())
    elif args.mode in ("shadow", "live"):
        if args.mode == "live" and not args.authorized:
            print("\n[SECURITY BLOCK] Live trading requires explicit flag: --authorized")
            print("System remaining safely in simulation.\n")
            sys.exit(1)
        asyncio.run(
            run_shadow_or_live_session(
                mode=args.mode,
                authorized=args.authorized,
                symbols=args.symbols,
                cycles=args.cycles,
                interval_seconds=args.interval,
            )
        )


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[INFO] Session interrupted by user. Shutting down cleanly.\n")
        sys.exit(0)
