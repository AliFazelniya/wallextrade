"""Unit tests for Wallex MCP Tools, Server, and Agentic Trader."""

import pytest
from src.agents.agentic_trader import AgenticTrader
from src.data.client import WallexClient
from src.exchange.adapter import ExchangeAdapter
from src.mcp.server import WallexMCPServer
from src.mcp.tools import WallexMCPToolSet
from src.portfolio.accounting import PortfolioEngine
from src.risk.engine import RiskEngine


@pytest.fixture
def mock_system():
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
    toolset = WallexMCPToolSet(client, portfolio, risk, adapter)
    trader = AgenticTrader(toolset=toolset)
    server = WallexMCPServer(toolset=toolset)
    return client, portfolio, risk, adapter, toolset, trader, server


@pytest.mark.asyncio
async def test_mcp_tools_portfolio_status(mock_system):
    _, portfolio, _, _, toolset, _, _ = mock_system
    status = toolset.get_portfolio_status()
    assert status["cash_toman"] == 5_000_000.0
    assert status["total_equity_toman"] == 5_000_000.0
    assert status["drawdown_pct"] == 0.0


@pytest.mark.asyncio
async def test_mcp_server_tools_list(mock_system):
    _, _, _, _, _, _, server = mock_system
    req = {"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}
    resp = await server.handle_rpc_request(req)
    assert resp["id"] == 1
    assert "tools" in resp["result"]
    tool_names = [t["name"] for t in resp["result"]["tools"]]
    assert "wallex_get_market_overview" in tool_names
    assert "wallex_get_orderbook_depth" in tool_names
    assert "wallex_get_portfolio_status" in tool_names
    assert "wallex_execute_guarded_order" in tool_names
    assert "wallex_get_triangular_arbitrage_scan" in tool_names


@pytest.mark.asyncio
async def test_agentic_trader_reasoning_cycle(mock_system):
    _, _, _, _, _, trader, _ = mock_system
    # Test cognitive semantic reasoning directly
    res = trader._cognitive_semantic_reasoning(
        symbol="BTCTMN",
        market_data={"spread_pct": 0.10},
        technicals={"rsi_14": 58.0, "ema_spread_pct": 0.35, "atr_pct": 1.8, "vol_ratio": 1.2},
        orderbook={"orderbook_imbalance": 0.15},
        portfolio={"total_equity_toman": 5_000_000.0, "open_positions": {}},
    )
    assert res["regime"] == "BULLISH_TREND"
    assert res["action"] == "BUY"
    assert res["confidence"] >= 0.85
    assert len(res["thought_process"]) > 10
