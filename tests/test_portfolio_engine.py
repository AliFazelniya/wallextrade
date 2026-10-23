"""Unit tests for Unified Multi-Symbol Portfolio Backtest Engine."""

import pandas as pd
import pytest
from src.agents.regime_agent import RegimeClassificationAgent
from src.backtest.portfolio_engine import PortfolioBacktestEngine
from src.risk.engine import RiskEngine
from src.strategy.regime_momentum import RegimeMomentumStrategy


def test_portfolio_backtest_shared_capital():
  dates = pd.date_range("2026-10-01", periods=100, freq="15min")

  # Symbol 1: BTCTMN trending upward
  df_btc = pd.DataFrame({
      "timestamp": dates,
      "open": [20_000_000_000.0 + i * 10_000_000.0 for i in range(100)],
      "high": [20_000_000_000.0 + i * 10_000_000.0 + 50_000_000.0 for i in range(100)],
      "low": [20_000_000_000.0 + i * 10_000_000.0 - 20_000_000.0 for i in range(100)],
      "close": [20_000_000_000.0 + i * 10_000_000.0 + 10_000_000.0 for i in range(100)],
      "volume": [10.0 + (50.0 if i > 55 else 0.0) for i in range(100)],
  })

  # Symbol 2: ETHTMN
  df_eth = pd.DataFrame({
      "timestamp": dates,
      "open": [1_500_000_000.0 + i * 1_000_000.0 for i in range(100)],
      "high": [1_500_000_000.0 + i * 1_000_000.0 + 5_000_000.0 for i in range(100)],
      "low": [1_500_000_000.0 + i * 1_000_000.0 - 2_000_000.0 for i in range(100)],
      "close": [1_500_000_000.0 + i * 1_000_000.0 + 1_000_000.0 for i in range(100)],
      "volume": [20.0 + (100.0 if i > 60 else 0.0) for i in range(100)],
  })

  symbols_data = {"BTCTMN": df_btc, "ETHTMN": df_eth}
  strategy = RegimeMomentumStrategy(min_confidence=0.70)
  risk_engine = RiskEngine(
      max_single_order_toman=500_000.0,
      max_portfolio_exposure_pct=60.0,
      max_drawdown_pct=5.0,
      max_open_positions=3,
      allowed_symbols={"BTCTMN", "ETHTMN"},
  )
  agent = RegimeClassificationAgent()
  engine = PortfolioBacktestEngine(initial_capital_toman=5_000_000.0)

  res = engine.run_portfolio_backtest(
      symbols_data=symbols_data,
      strategy=strategy,
      risk_engine=risk_engine,
      agent=agent,
      use_ai=True,
  )

  assert res["initial_capital_toman"] == 5_000_000.0
  assert res["all_holdings_liquidated_to_toman"] is True
  assert res["final_crypto_holdings"] == {}
  assert "final_equity_toman" in res
  assert "net_return_pct" in res
  assert "turnover" in res
  assert "counterfactual_logs" in res
