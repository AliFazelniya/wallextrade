"""Unit and integration tests for Multi-Agent Council, Mean Reversion Scalper, and Report Generator."""

import pathlib
import pytest
import pandas as pd

from src.agents.council import (
    ChiefInvestmentOfficerAgent,
    MacroSentimentAgent,
    MicrostructureAgent,
    TechnicalAnalystAgent,
)
from src.agents.schemas import ActionType, MarketRegime, RegimeAnalysisOutput
from src.monitoring.report_generator import JudgeReportGenerator
from src.strategy.mean_reversion_scalper import MeanReversionScalperStrategy


def test_technical_analyst_agent_bullish():
    agent = TechnicalAnalystAgent()
    vote = agent.evaluate({"rsi_14": 58.0, "ema_spread_pct": 0.40, "atr_pct": 1.5})
    assert vote.opinion == "BULLISH"
    assert vote.recommended_action == ActionType.BUY
    assert vote.confidence >= 0.85


def test_microstructure_agent_orderbook_imbalance():
    agent = MicrostructureAgent()
    vote = agent.evaluate(
        orderbook={"orderbook_imbalance": 0.20},
        market_data={"spread_pct": 0.08},
    )
    assert vote.opinion == "BULLISH"
    assert vote.recommended_action == ActionType.BUY
    assert "bid-side" in vote.key_evidence


def test_cio_council_consensus_formation():
    cio = ChiefInvestmentOfficerAgent()
    decision = cio.convene_council(
        symbol="BTCTMN",
        market_data={"spread_pct": 0.05},
        technicals={"rsi_14": 60.0, "ema_spread_pct": 0.35, "atr_pct": 1.2},
        orderbook={"orderbook_imbalance": 0.15},
        portfolio={"total_equity_toman": 5_000_000.0, "cash_toman": 5_000_000.0, "open_positions": {}},
    )
    assert decision.regime == MarketRegime.BULLISH_TREND
    assert decision.action == ActionType.BUY
    assert len(decision.council_votes) == 4
    assert len(decision.synthesis_rationale) > 10


def test_mean_reversion_scalper_signals():
    strat = MeanReversionScalperStrategy(target_profit_pct=1.0, max_spread_pct=0.20)
    reg_out = RegimeAnalysisOutput(
        symbol="BTCTMN",
        regime=MarketRegime.CALM_RANGE,
        confidence=0.80,
        volatility_state="LOW",
        recommended_action=ActionType.HOLD,
        max_suggested_allocation_pct=5.0,
        reasoning="Range bound",
    )

    # DataFrame with simulated Bollinger Bands and oversold RSI
    df = pd.DataFrame({
        "close": [100.0] * 35,
        "bb_upper": [110.0] * 35,
        "bb_middle": [100.0] * 35,
        "bb_lower": [90.0] * 35,
        "rsi_14": [40.0] * 35,
    })

    # Test buy signal near lower band
    sig = strat.generate_signal(
        symbol="BTCTMN",
        df_features=df,
        regime_output=reg_out,
        current_price_toman=90.1,  # near lower band 90.0
        spread_pct=0.10,
    )
    assert sig is not None
    assert sig.action == ActionType.BUY
    assert sig.order_value_toman > 0
    assert sig.take_profit_toman == 100.0  # target middle band


def test_judge_report_generator(tmp_path):
    repo_root = pathlib.Path(__file__).resolve().parents[1]
    gen = JudgeReportGenerator(repo_root)
    out_file = gen.generate_html_report()
    assert out_file.exists()
    content = out_file.read_text(encoding="utf-8")
    assert "گزارش ممیزی و حسابرسی سامانه معاملاتی الگوریتمی والکس" in content
    assert "Technical Analyst Agent" in content
