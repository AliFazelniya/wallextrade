"""Comprehensive Unit Tests for Exchange Adapter and Safety Gateways."""

from unittest.mock import AsyncMock
import pytest
from src.agents.schemas import ActionType
from src.data.client import WallexAPIError, WallexClient
from src.exchange.adapter import (
    DuplicateOrderError,
    ExchangeAdapter,
    ExecutionError,
    MarketNotEligibleError,
)
from src.portfolio.accounting import PortfolioEngine


@pytest.mark.asyncio
async def test_live_trading_is_strictly_blocked_without_authorization():
  client = WallexClient()
  portfolio = PortfolioEngine()
  adapter = ExchangeAdapter(
      client=client,
      portfolio=portfolio,
      trading_mode="LIVE",
      live_execution_authorized=False,  # Blocked!
      allowed_symbols={"BTCTMN"},
  )

  with pytest.raises(ExecutionError, match="Live trading blocked"):
    await adapter.execute_order(
        symbol="BTCTMN",
        action=ActionType.BUY,
        target_price=22_000_000_000.0,
        approved_value_toman=500_000.0,
    )


@pytest.mark.asyncio
async def test_allowlist_enforcement_immediately_before_submission():
  client = WallexClient()
  portfolio = PortfolioEngine()
  adapter = ExchangeAdapter(
      client=client,
      portfolio=portfolio,
      trading_mode="SIMULATION",
      allowed_symbols={"BTCTMN"},  # Only BTCTMN is allowed
  )

  with pytest.raises(MarketNotEligibleError, match="NOT in verified ALLOWLIST"):
    await adapter.execute_order(
        symbol="ETHTMN",
        action=ActionType.BUY,
        target_price=3_500_000_000.0,
        approved_value_toman=100_000.0,
    )


@pytest.mark.asyncio
async def test_blocklist_enforcement_immediately_before_submission():
  client = WallexClient()
  portfolio = PortfolioEngine()
  adapter = ExchangeAdapter(
      client=client,
      portfolio=portfolio,
      trading_mode="SIMULATION",
      allowed_symbols={"BTCTMN", "DOGETMN"},
      restricted_symbols={"DOGETMN"},  # DOGETMN explicitly restricted
  )

  with pytest.raises(MarketNotEligibleError, match="RESTRICTED"):
    await adapter.execute_order(
        symbol="DOGETMN",
        action=ActionType.BUY,
        target_price=20000.0,
        approved_value_toman=100_000.0,
    )


@pytest.mark.asyncio
async def test_duplicate_order_prevention():
  client = WallexClient()
  portfolio = PortfolioEngine()
  adapter = ExchangeAdapter(
      client=client,
      portfolio=portfolio,
      trading_mode="SIMULATION",
      allowed_symbols={"BTCTMN"},
      duplicate_window_seconds=10.0,
  )

  # First execution succeeds
  res1 = await adapter.execute_order(
      symbol="BTCTMN",
      action=ActionType.BUY,
      target_price=20_000_000_000.0,
      approved_value_toman=100_000.0,
  )
  assert res1["status"] == "SIMULATED_FILL"

  # Immediate second execution for same symbol and side must be rejected as duplicate
  with pytest.raises(DuplicateOrderError, match="Duplicate order submission"):
    await adapter.execute_order(
        symbol="BTCTMN",
        action=ActionType.BUY,
        target_price=20_000_000_000.0,
        approved_value_toman=100_000.0,
    )


@pytest.mark.asyncio
async def test_partial_fill_execution():
  client = WallexClient()
  portfolio = PortfolioEngine(initial_capital_toman=5_000_000.0)
  adapter = ExchangeAdapter(
      client=client,
      portfolio=portfolio,
      trading_mode="SIMULATION",
      allowed_symbols={"BTCTMN"},
  )

  res = await adapter.execute_order(
      symbol="BTCTMN",
      action=ActionType.BUY,
      target_price=20_000_000_000.0,
      approved_value_toman=200_000.0,
      partial_fill_ratio=0.50,  # 50% partial fill
  )

  assert res["status"] == "SIMULATED_PARTIAL_FILL"
  assert res["fill_ratio"] == 0.50
  assert "BTCTMN" in portfolio.positions
  # Fill cost should be approximately 100k TMN (half of 200k)
  assert 4_890_000 <= portfolio.cash_toman <= 4_901_000


@pytest.mark.asyncio
async def test_uncertain_order_reconciliation():
  client = WallexClient()
  # Mock get_open_orders to return an open order
  client.get_open_orders = AsyncMock(
      return_value={
          "success": True,
          "result": {
              "orders": [{
                  "clientOrderId": "LIMIT-test-123",
                  "symbol": "BTCTMN",
                  "status": "OPEN",
                  "price": "22000000000",
              }]
          },
      }
  )

  portfolio = PortfolioEngine()
  adapter = ExchangeAdapter(
      client=client,
      portfolio=portfolio,
      trading_mode="LIVE",
      allowed_symbols={"BTCTMN"},
  )

  reconciled = await adapter.reconcile_uncertain_order("LIMIT-test-123")
  assert reconciled["found"] is True
  assert reconciled["state"] == "OPEN"
  assert reconciled["order"]["symbol"] == "BTCTMN"


@pytest.mark.asyncio
async def test_every_credit_inactive_symbol_rejected_immediately_by_adapter():
  import json, pathlib

  repo_root = pathlib.Path(__file__).resolve().parent.parent
  with open(repo_root / "config" / "market_restrictions.json", "r") as f:
    data = json.load(f)

  inactive_symbols = {
      s["symbol"] for s in data.get("credit_inactive_symbols", [])
  }
  adapter = ExchangeAdapter(
      client=WallexClient(),
      portfolio=PortfolioEngine(),
      trading_mode="SIMULATION",
      allowed_symbols={"BTCTMN"},
      restricted_symbols=inactive_symbols,
  )

  for sym in inactive_symbols:
    with pytest.raises(MarketNotEligibleError):
      adapter.validate_market_eligibility(sym)


@pytest.mark.asyncio
async def test_api_rate_limit_and_timeout_error_handling():
  from unittest.mock import AsyncMock
  import httpx
  from src.data.client import WallexAPIError

  client = WallexClient()
  # Mock _request to simulate rate limit (HTTP 429)
  client._request = AsyncMock(
      side_effect=WallexAPIError("Rate limit exceeded", status_code=429)
  )

  with pytest.raises(WallexAPIError) as exc_info:
    await client.get_markets()
  assert exc_info.value.status_code == 429

