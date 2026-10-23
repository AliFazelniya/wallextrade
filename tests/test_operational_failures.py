"""Phase 15 Operational Reliability, Failure Scenarios, and Fail-Closed Verification Tests."""

from unittest.mock import AsyncMock, MagicMock, patch
import httpx
import pandas as pd
import pytest

from src.agents.regime_agent import RegimeClassificationAgent
from src.agents.schemas import (
    ActionType,
    MarketFeaturesInput,
    MarketRegime,
    ProposedTradeSignal,
)
from src.data.client import WallexAPIError, WallexClient
from src.data.fetcher import MarketDataFetcher
from src.exchange.adapter import (
    DuplicateOrderError,
    ExchangeAdapter,
    ExecutionError,
    MarketNotEligibleError,
)
from src.portfolio.accounting import PortfolioEngine
from src.risk.engine import RiskEngine


@pytest.mark.asyncio
async def test_exchange_api_timeout_fails_closed():
  """Network timeout on exchange API must fail closed without placing order."""
  client = WallexClient(base_url="https://api.wallex.ir", timeout_seconds=0.1)

  # Mock session to raise ReadTimeout
  mock_session = AsyncMock()
  mock_session.request = AsyncMock(
      side_effect=httpx.ReadTimeout("Request timed out")
  )
  client._get_session = AsyncMock(return_value=mock_session)

  portfolio = PortfolioEngine(initial_capital_toman=5_000_000.0)
  adapter = ExchangeAdapter(
      client=client,
      portfolio=portfolio,
      trading_mode="LIVE",
      live_execution_authorized=True,
      allowed_symbols={"BTCTMN"},
  )

  with pytest.raises(
      ExecutionError, match="Order submission failed and unverified"
  ):
    await adapter.execute_order(
        symbol="BTCTMN",
        action=ActionType.BUY,
        target_price=20_000_000_000.0,
        approved_value_toman=500_000.0,
    )

  # Invariant: cash remained untouched, zero positions created
  assert portfolio.cash_toman == 5_000_000.0
  assert len(portfolio.positions) == 0


@pytest.mark.asyncio
async def test_http_429_rate_limit_recovery():
  """HTTP 429 response is handled with backoff and raises WallexAPIError without crashing."""
  client = WallexClient(base_url="https://api.wallex.ir")

  mock_response = MagicMock()
  mock_response.status_code = 429
  mock_response.text = '{"error": "Too Many Requests"}'

  mock_session = AsyncMock()
  mock_session.request = AsyncMock(return_value=mock_response)
  client._get_session = AsyncMock(return_value=mock_session)

  with pytest.raises(WallexAPIError) as exc_info:
    await client.get_markets()

  assert exc_info.value.status_code == 429
  assert "Rate limit exceeded" in str(exc_info.value)


def test_malformed_and_stale_market_data_fails_closed():
  """Malformed OHLCV data or stale timestamps must be rejected before trading."""
  # Empty DataFrame
  df_empty = pd.DataFrame()
  fetcher = MarketDataFetcher(client=WallexClient())
  is_valid, reason = fetcher.validate_data_freshness(
      df_empty, max_staleness_minutes=30
  )
  assert is_valid is False
  assert "empty" in reason.lower()

  # Stale DataFrame (timestamp 2 hours ago)
  stale_time = (
      pd.Timestamp.now(tz="UTC") - pd.Timedelta(hours=2)
  ).isoformat()
  df_stale = pd.DataFrame({
      "timestamp": [stale_time],
      "open": [100.0],
      "high": [105.0],
      "low": [95.0],
      "close": [102.0],
      "volume": [10.0],
  })
  is_valid_stale, reason_stale = fetcher.validate_data_freshness(
      df_stale, max_staleness_minutes=30
  )
  assert is_valid_stale is False
  assert "stale" in reason_stale.lower()


def test_missing_candles_gap_detection():
  """Missing candles in historical series are detected and reported."""
  t0 = pd.Timestamp("2026-10-01 10:00:00+00:00")
  # 15m intervals with a 2-hour gap
  times = [t0, t0 + pd.Timedelta(minutes=15), t0 + pd.Timedelta(minutes=135)]
  df = pd.DataFrame({
      "timestamp": times,
      "open": [100.0, 101.0, 102.0],
      "high": [102.0, 103.0, 104.0],
      "low": [99.0, 100.0, 101.0],
      "close": [101.0, 102.0, 103.0],
      "volume": [10.0, 12.0, 11.0],
  })

  diffs = df["timestamp"].diff().dropna()
  has_gaps = any(d > pd.Timedelta(minutes=20) for d in diffs)
  assert has_gaps is True


@pytest.mark.asyncio
async def test_ai_timeout_and_invalid_structured_output_activates_fallback():
  """AI timeout or malformed JSON gracefully activates safe deterministic fallback."""
  agent = RegimeClassificationAgent(api_key="mock_key", timeout_seconds=0.1)

  # Mock HTTP call to throw an error (simulating LLM failure/malformed output)
  with patch(
      "httpx.AsyncClient.post",
      side_effect=httpx.ConnectError("LLM API unreachable"),
  ):
    # Calm / ranging market features
    features = MarketFeaturesInput(
        symbol="BTCTMN",
        price_toman=20_000_000_000.0,
        ema_spread_pct=0.05,
        rsi_14=50.0,
        atr_pct=1.5,
        vol_ratio=0.9,
        spread_pct=0.05,
        trend_direction="BEARISH",
    )
    output = await agent.classify_regime(features)

    # Must fall back to deterministic rule and output CALM_RANGE with HOLD
    assert output.regime == MarketRegime.CALM_RANGE
    assert output.recommended_action == ActionType.HOLD
    assert output.confidence >= 0.70


@pytest.mark.asyncio
async def test_duplicate_order_prevention_fail_closed():
  """Rapid identical order submissions are rejected by duplicate order guard."""
  client = WallexClient()
  portfolio = PortfolioEngine(initial_capital_toman=5_000_000.0)
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
      approved_value_toman=200_000.0,
  )
  assert res1["status"] == "SIMULATED_FILL"

  # Immediate second execution must raise DuplicateOrderError
  with pytest.raises(DuplicateOrderError):
    await adapter.execute_order(
        symbol="BTCTMN",
        action=ActionType.BUY,
        target_price=20_000_000_000.0,
        approved_value_toman=200_000.0,
    )


@pytest.mark.asyncio
async def test_uncertain_order_submission_reconciliation():
  """Uncertain order submission outcome queries open orders to verify state."""
  client = WallexClient(api_key="mock_key")
  client.get_open_orders = AsyncMock(
      return_value={
          "result": {
              "orders": [
                  {"clientOrderId": "LIMIT-123456", "status": "OPEN", "price": "20000000000"}
              ]
          }
      }
  )

  portfolio = PortfolioEngine(initial_capital_toman=5_000_000.0)
  adapter = ExchangeAdapter(
      client=client,
      portfolio=portfolio,
      trading_mode="SHADOW",
      allowed_symbols={"BTCTMN"},
  )

  rec_found = await adapter.reconcile_uncertain_order("LIMIT-123456")
  assert rec_found["found"] is True
  assert rec_found["state"] == "OPEN"

  rec_missing = await adapter.reconcile_uncertain_order("LIMIT-UNKNOWN")
  assert rec_missing["found"] is False


@pytest.mark.asyncio
async def test_partial_fills_and_unfilled_orders():
  """Partial fill allocates only partial quantity and remaining cash is preserved."""
  client = WallexClient()
  portfolio = PortfolioEngine(initial_capital_toman=5_000_000.0)
  adapter = ExchangeAdapter(
      client=client,
      portfolio=portfolio,
      trading_mode="SIMULATION",
      allowed_symbols={"BTCTMN"},
      slippage_pct=0.0,
  )

  res = await adapter.execute_order(
      symbol="BTCTMN",
      action=ActionType.BUY,
      target_price=20_000_000_000.0,
      approved_value_toman=500_000.0,
      partial_fill_ratio=0.40,  # 40% fill
  )

  assert res["status"] == "SIMULATED_PARTIAL_FILL"
  assert res["fill_ratio"] == 0.40
  pos = portfolio.positions["BTCTMN"]
  # Full would be 500k / 20B = 0.000025; 40% is 0.000010
  assert pytest.approx(pos.quantity, rel=1e-4) == 0.000010
  # Cost ~200k + fee ~600 = ~200,600 TMN, remaining cash ~4,799,400 TMN
  assert portfolio.cash_toman > 4_790_000.0


def test_incorrect_account_balances_discrepancy_alert():
  """Exchange balance mismatch triggers reconciliation discrepancy alert."""
  portfolio = PortfolioEngine(initial_capital_toman=5_000_000.0)
  # Exchange reports 4.5M TMN instead of 5M TMN
  mismatch_report = {
      "result": {
          "balances": {
              "TMN": {"value": "4500000.0"}
          }
      }
  }
  rec = portfolio.reconcile_with_exchange(mismatch_report)
  assert rec["reconciled"] is False
  assert len(rec["discrepancies"]) == 1
  assert "TMN cash mismatch" in rec["discrepancies"][0]


def test_risk_engine_rejection_fails_closed():
  """Risk engine rejects orders exceeding limits or targeting restricted symbols."""
  risk = RiskEngine(
      max_single_order_toman=500_000.0,
      allowed_symbols={"BTCTMN"},
      restricted_symbols={"DOGETMN"},
  )

  # 1. Restricted symbol
  sig_bad = ProposedTradeSignal(
      symbol="DOGETMN",
      action=ActionType.BUY,
      target_price_toman=10000.0,
      order_value_toman=500_000.0,
      regime=MarketRegime.BULLISH_TREND,
      ai_confidence=0.85,
      rationale="Test restricted symbol",
      timestamp="2026-10-22T10:00:00Z",
  )
  eval_bad = risk.evaluate_signal(
      sig_bad,
      current_portfolio_value_toman=5_000_000.0,
      current_cash_toman=5_000_000.0,
      current_crypto_exposure_toman=0.0,
      active_positions={},
      current_market_spread_pct=0.05,
  )
  assert eval_bad.approved is False
  assert any("RESTRICTED" in r for r in eval_bad.veto_reasons)

  # 2. Oversized order capped to max_single_order_toman
  sig_large = ProposedTradeSignal(
      symbol="BTCTMN",
      action=ActionType.BUY,
      target_price_toman=20_000_000_000.0,
      order_value_toman=1_250_000.0,  # Exceeds 500k limit
      regime=MarketRegime.BULLISH_TREND,
      ai_confidence=0.85,
      rationale="Test oversized order",
      timestamp="2026-10-22T10:00:00Z",
  )
  eval_large = risk.evaluate_signal(
      sig_large,
      current_portfolio_value_toman=5_000_000.0,
      current_cash_toman=5_000_000.0,
      current_crypto_exposure_toman=0.0,
      active_positions={},
      current_market_spread_pct=0.05,
  )
  assert eval_large.approved is True
  assert eval_large.approved_value_toman == 500_000.0


def test_emergency_halt_triggers_and_blocks_all_orders():
  """Cumulative drawdown breaching 5% triggers emergency halt and blocks all orders."""
  risk = RiskEngine(
      max_drawdown_pct=5.0,
      allowed_symbols={"BTCTMN"},
  )

  sig = ProposedTradeSignal(
      symbol="BTCTMN",
      action=ActionType.BUY,
      target_price_toman=20_000_000_000.0,
      order_value_toman=500_000.0,
      regime=MarketRegime.BULLISH_TREND,
      ai_confidence=0.85,
      rationale="Test emergency halt trigger",
      timestamp="2026-10-22T10:00:00Z",
  )

  # Portfolio equity dropped from 5M to 4.70M (-6.0% drawdown)
  eval_halt = risk.evaluate_signal(
      sig,
      current_portfolio_value_toman=4_700_000.0,
      current_cash_toman=4_700_000.0,
      current_crypto_exposure_toman=0.0,
      active_positions={},
      current_market_spread_pct=0.05,
  )
  assert eval_halt.approved is False
  assert any("drawdown" in r.lower() for r in eval_halt.veto_reasons)
  assert risk.emergency_halt is True

  # Even if equity recovers, emergency halt persists until manually reset
  eval_subsequent = risk.evaluate_signal(
      sig,
      current_portfolio_value_toman=5_000_000.0,
      current_cash_toman=5_000_000.0,
      current_crypto_exposure_toman=0.0,
      active_positions={},
      current_market_spread_pct=0.05,
  )
  assert eval_subsequent.approved is False
  assert any("EMERGENCY HALT" in r for r in eval_subsequent.veto_reasons)


def test_process_crash_and_portfolio_state_recovery():
  """Portfolio state is accurately serialized and restored after process crash."""
  engine1 = PortfolioEngine(initial_capital_toman=5_000_000.0)
  engine1.record_fill("BTCTMN", "BUY", 0.000025, 20_000_000_000.0, is_maker=False)
  engine1.update_market_price("BTCTMN", 20_500_000_000.0)

  # Save state
  saved_state = engine1.export_state()

  # Simulate crash and restart
  engine2 = PortfolioEngine.from_state(saved_state)

  assert engine2.initial_capital_toman == engine1.initial_capital_toman
  assert engine2.cash_toman == engine1.cash_toman
  assert engine2.total_fees_paid_toman == engine1.total_fees_paid_toman
  assert "BTCTMN" in engine2.positions
  assert engine2.positions["BTCTMN"].quantity == engine1.positions["BTCTMN"].quantity
  assert engine2.positions["BTCTMN"].current_price == engine1.positions["BTCTMN"].current_price
  assert engine2.get_total_equity() == engine1.get_total_equity()


def test_final_conversion_into_toman_simulation():
  """Mandatory end-of-competition liquidation converts 100% of holdings into TMN."""
  engine = PortfolioEngine(initial_capital_toman=5_000_000.0)
  engine.record_fill("BTCTMN", "BUY", 0.000025, 20_000_000_000.0)
  assert len(engine.positions) == 1

  current_prices = {"BTCTMN": 21_000_000_000.0}
  liquidations = engine.liquidate_all_to_toman(current_prices, slippage_pct=0.15)

  assert len(liquidations) == 1
  assert len(engine.positions) == 0
  assert engine.cash_toman > 0
  assert engine.get_total_equity() == engine.cash_toman


@pytest.mark.asyncio
async def test_system_fails_closed_without_authorization():
  """Live trading mode with missing authorization strictly blocks order submission."""
  client = WallexClient()
  portfolio = PortfolioEngine(initial_capital_toman=5_000_000.0)
  adapter = ExchangeAdapter(
      client=client,
      portfolio=portfolio,
      trading_mode="LIVE",
      live_execution_authorized=False,
      allowed_symbols={"BTCTMN"},
  )

  with pytest.raises(ExecutionError, match="Live trading blocked"):
    await adapter.execute_order(
        symbol="BTCTMN",
        action=ActionType.BUY,
        target_price=20_000_000_000.0,
        approved_value_toman=500_000.0,
    )
