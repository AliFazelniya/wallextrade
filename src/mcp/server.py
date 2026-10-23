"""Wallex MCP Server.

Implements the standard Model Context Protocol (MCP) server for Wallex Exchange,
exposing tools for:
- querying market data and orderbook depth
- reading technical features
- inspecting portfolio status
- executing risk-governed trades

Usage:
    python -m src.mcp.server
"""

from __future__ import annotations

import asyncio
import json
import logging
import sys
from typing import Any, Dict, List, Optional

from src.data.client import WallexClient
from src.exchange.adapter import ExchangeAdapter
from src.mcp.tools import WallexMCPToolSet
from src.portfolio.accounting import PortfolioEngine
from src.risk.engine import RiskEngine

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] [MCP] %(message)s")
logger = logging.getLogger("WallexMCPServer")


class WallexMCPServer:
    """Standard Model Context Protocol (MCP) Server for Wallex Exchange."""

    def __init__(self, toolset: Optional[WallexMCPToolSet] = None):
        if toolset is None:
            client = WallexClient()
            portfolio = PortfolioEngine(initial_capital_toman=5_000_000.0)
            allowed = {"BTCTMN", "USDTTMN", "ETHTMN", "SOLTMN"}
            risk = RiskEngine(
                max_single_order_toman=500_000.0,
                max_portfolio_exposure_pct=60.0,
                max_drawdown_pct=5.0,
                allowed_symbols=allowed,
            )
            adapter = ExchangeAdapter(
                client=client,
                portfolio=portfolio,
                trading_mode="SHADOW",
                live_execution_authorized=False,
                allowed_symbols=allowed,
            )
            self.toolset = WallexMCPToolSet(client, portfolio, risk, adapter)
        else:
            self.toolset = toolset

        self.tools_schema = [
            {
                "name": "wallex_get_market_overview",
                "description": "Fetch real-time price, best bid/ask, and spread across Wallex markets.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "symbols": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of market symbols, e.g. ['BTCTMN', 'ETHTMN']",
                        }
                    },
                },
            },
            {
                "name": "wallex_get_orderbook_depth",
                "description": "Inspect top 5 order book levels and bid/ask volume imbalance.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "symbol": {"type": "string", "description": "Market symbol, e.g. 'BTCTMN'"}
                    },
                    "required": ["symbol"],
                },
            },
            {
                "name": "wallex_get_technical_features",
                "description": "Calculate quantitative indicators (EMA 20/50, RSI 14, ATR, Volume Ratio).",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "symbol": {"type": "string", "description": "Market symbol, e.g. 'BTCTMN'"},
                        "resolution": {"type": "string", "description": "Candle timeframe, e.g. '15'"}
                    },
                    "required": ["symbol"],
                },
            },
            {
                "name": "wallex_get_portfolio_status",
                "description": "Get current Toman cash balance, open positions, unrealized P&L and drawdown.",
                "parameters": {"type": "object", "properties": {}},
            },
            {
                "name": "wallex_execute_guarded_order",
                "description": "Execute a BUY or SELL order subjected to the strict deterministic Risk Engine.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "symbol": {"type": "string", "description": "Market symbol, e.g. 'BTCTMN'"},
                        "action": {"type": "string", "enum": ["BUY", "SELL"], "description": "Order action"},
                        "target_price": {"type": "number", "description": "Price in TMN"},
                        "amount_toman": {"type": "number", "description": "Total value in TMN (max 500,000)"},
                        "rationale": {"type": "string", "description": "Reasoning rationale for the decision"},
                    },
                    "required": ["symbol", "action", "target_price", "amount_toman", "rationale"],
                },
            },
            {
                "name": "wallex_get_triangular_arbitrage_scan",
                "description": "Scan cross-market synthetic rates between COIN/TMN, COIN/USDT, and USDT/TMN for triangular arbitrage inefficiencies.",
                "parameters": {
                    "type": "object",
                    "properties": {},
                },
            },
        ]

    async def dispatch_tool_call(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Dispatches an MCP tool call to the corresponding implementation."""
        if tool_name == "wallex_get_market_overview":
            return await self.toolset.get_market_overview(arguments.get("symbols"))
        elif tool_name == "wallex_get_orderbook_depth":
            return await self.toolset.get_orderbook_depth(arguments.get("symbol", "BTCTMN"))
        elif tool_name == "wallex_get_technical_features":
            return await self.toolset.get_technical_features(
                arguments.get("symbol", "BTCTMN"),
                arguments.get("resolution", "15")
            )
        elif tool_name == "wallex_get_portfolio_status":
            return self.toolset.get_portfolio_status()
        elif tool_name == "wallex_get_triangular_arbitrage_scan":
            return await self.toolset.get_triangular_arbitrage_scan()
        elif tool_name == "wallex_execute_guarded_order":
            return await self.toolset.execute_guarded_order(
                symbol=arguments["symbol"],
                action=arguments["action"],
                target_price=float(arguments["target_price"]),
                amount_toman=float(arguments["amount_toman"]),
                rationale=arguments.get("rationale", "AI Agent decision via MCP"),
            )
        else:
            raise ValueError(f"Unknown MCP tool: {tool_name}")


    async def handle_rpc_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handles standard JSON-RPC request for MCP protocol."""
        req_id = request.get("id")
        method = request.get("method")
        params = request.get("params", {})

        if method == "tools/list":
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {"tools": self.tools_schema},
            }
        elif method == "tools/call":
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            try:
                res = await self.dispatch_tool_call(tool_name, arguments)
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {"content": [{"type": "text", "text": json.dumps(res, ensure_ascii=False)}]},
                }
            except Exception as e:
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {"code": -32603, "message": str(e)},
                }
        else:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32601, "message": f"Method {method} not found"},
            }

    async def run_stdio_server(self):
        """Runs the MCP server reading from stdin and writing to stdout."""
        logger.info("Wallex MCP Server initialized and listening on stdio...")
        loop = asyncio.get_running_loop()
        reader = asyncio.StreamReader()
        protocol = asyncio.StreamReaderProtocol(reader)
        await loop.connect_read_pipe(lambda: protocol, sys.stdin)

        while True:
            line = await reader.readline()
            if not line:
                break
            try:
                req = json.loads(line.decode().strip())
                resp = await self.handle_rpc_request(req)
                sys.stdout.write(json.dumps(resp) + "\n")
                sys.stdout.flush()
            except Exception as exc:
                logger.error("Error processing MCP frame: %s", exc)


if __name__ == "__main__":
    server = WallexMCPServer()
    asyncio.run(server.run_stdio_server())
