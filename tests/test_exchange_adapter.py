"""Unit tests for Exchange Adapter safety mechanisms."""

import pytest
from src.agents.schemas import ActionType
from src.data.client import WallexClient
from src.exchange.adapter import ExchangeAdapter, ExecutionError
from src.portfolio.accounting import PortfolioEngine


@pytest.mark.asyncio
async def test_live_trading_is_blocked_without_authorization():
  client = WallexClient()
  portfolio = PortfolioEngine()
  adapter = ExchangeAdapter(
      client=client,
      portfolio=portfolio,
      trading_mode="LIVE",
      live_execution_authorized=False,  # Human authorization NOT granted
  )

  with pytest.raises(ExecutionError, match="Live trading blocked"):
    await adapter.execute_order(
        symbol="BTCTMN",
        action=ActionType.BUY,
        target_price=22_000_000_000.0,
        approved_value_toman=500_000.0,
    )


@pytest.mark.asyncio
async def test_simulation_mode_executes_safely_without_real_network_order():
  client = WallexClient()
  portfolio = PortfolioEngine(initial_capital_toman=5_000_000.0)
  adapter = ExchangeAdapter(
      client=client,
      portfolio=portfolio,
      trading_mode="SIMULATION",
      live_execution_authorized=False,
      slippage_pct=0.10,
  )

  result = await adapter.execute_order(
      symbol="BTCTMN",
      action=ActionType.BUY,
      target_price=20_000_000_000.0,
      approved_value_toman=500_000.0,
  )

  assert result["status"] == "SIMULATED_FILL"
  assert "fill" in result
  assert "BTCTMN" in portfolio.positions
  assert portfolio.cash_toman < 5_000_000.0
