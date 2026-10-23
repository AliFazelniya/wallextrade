"""Unit tests for Triangular Arbitrage, Micro-Grid Maker, and 5-Agent Council."""

import pytest
from src.agents.council import (
    ArbitrageScoutAgent,
    ChiefInvestmentOfficerAgent,
    CouncilDecision,
)
from src.agents.schemas import ActionType, MarketRegime, RegimeAnalysisOutput
from src.strategy.micro_grid_maker import MicroGridMakerStrategy
from src.strategy.triangular_arbitrage import TriangularArbitrageStrategy


class TestTriangularArbitrage:
    def test_scan_pair_balanced_within_friction(self):
        strat = TriangularArbitrageStrategy(min_net_edge_pct=0.15, fee_friction_pct=0.55)
        # 1 BTC = 80,000 USDT, 1 USDT = 270,000 TMN => Synthetic = 21,600,000,000 TMN
        # Actual BTCTMN = 21,620,000,000 (+0.09% discrepancy, below 0.55% fee friction)
        markets = {
            "BTCTMN": {"stats": {"lastPrice": "21620000000"}},
            "BTCUSDT": {"stats": {"lastPrice": "80000"}},
            "USDTTMN": {"stats": {"lastPrice": "270000"}},
        }
        res = strat.scan_pair("BTC", markets)
        assert res is not None
        assert res.base_coin == "BTC"
        assert res.synthetic_tmn_price == 21_600_000_000.0
        assert abs(res.discrepancy_pct - 0.093) < 0.02
        assert not res.is_actionable
        assert res.recommended_action == ActionType.HOLD

    def test_scan_pair_actionable_discount(self):
        strat = TriangularArbitrageStrategy(min_net_edge_pct=0.15, fee_friction_pct=0.55)
        # Synthetic = 80,000 * 270,000 = 21,600,000,000 TMN
        # Actual BTCTMN = 21,400,000,000 TMN (Discount of -0.925%, net edge > 0.15%)
        markets = {
            "BTCTMN": {"stats": {"lastPrice": "21400000000"}},
            "BTCUSDT": {"stats": {"lastPrice": "80000"}},
            "USDTTMN": {"stats": {"lastPrice": "270000"}},
        }
        res = strat.scan_pair("BTC", markets)
        assert res is not None
        assert res.is_actionable
        assert res.recommended_action == ActionType.BUY
        assert res.net_edge_pct > 0.15

        sig = strat.generate_arbitrage_signal("BTC", markets)
        assert sig is not None
        assert sig.action == ActionType.BUY
        assert sig.symbol == "BTCTMN"
        assert sig.take_profit_toman == 21_600_000_000.0

    def test_scan_all_supported(self):
        strat = TriangularArbitrageStrategy()
        markets = {
            "BTCTMN": {"stats": {"lastPrice": "21600000000"}},
            "BTCUSDT": {"stats": {"lastPrice": "80000"}},
            "ETHTMN": {"stats": {"lastPrice": "648000000"}},
            "ETHUSDT": {"stats": {"lastPrice": "2400"}},
            "USDTTMN": {"stats": {"lastPrice": "270000"}},
        }
        res = strat.scan_all_supported(markets)
        assert len(res) >= 2
        coins = [r.base_coin for r in res]
        assert "BTC" in coins
        assert "ETH" in coins


class TestMicroGridMaker:
    def test_grid_passive_buy_in_calm_range(self):
        strat = MicroGridMakerStrategy(
            grid_step_pct=0.35,
            max_order_toman=250_000.0,
            max_spread_pct=0.18,
            max_imbalance_skew=0.20,
        )
        regime = RegimeAnalysisOutput(
            symbol="USDTTMN",
            regime=MarketRegime.CALM_RANGE,
            confidence=0.85,
            volatility_state="LOW",
            recommended_action=ActionType.HOLD,
            max_suggested_allocation_pct=5.0,
            reasoning="Range bound market equilibrium",
        )
        market_data = {
            "last_price_toman": 269_200.0,
            "best_bid_toman": 269_195.0,
            "best_ask_toman": 269_205.0,
            "spread_pct": 0.004,
        }
        orderbook = {"orderbook_imbalance": 0.02}

        sig = strat.evaluate_market_making("USDTTMN", orderbook, market_data, regime, current_inventory_toman=0.0)
        assert sig is not None
        assert sig.action == ActionType.BUY
        assert sig.target_price_toman == 269_195.0
        assert sig.order_value_toman == 250_000.0

    def test_grid_adverse_selection_veto(self):
        strat = MicroGridMakerStrategy(max_imbalance_skew=0.20)
        regime = RegimeAnalysisOutput(
            symbol="USDTTMN",
            regime=MarketRegime.CALM_RANGE,
            confidence=0.85,
            volatility_state="LOW",
            recommended_action=ActionType.HOLD,
            max_suggested_allocation_pct=5.0,
            reasoning="Range bound market equilibrium",
        )
        market_data = {
            "last_price_toman": 269_200.0,
            "best_bid_toman": 269_195.0,
            "best_ask_toman": 269_205.0,
            "spread_pct": 0.004,
        }
        # Toxic sell wave detected in orderbook:
        orderbook = {"orderbook_imbalance": -0.35}

        sig = strat.evaluate_market_making("USDTTMN", orderbook, market_data, regime, current_inventory_toman=0.0)
        assert sig is None


class TestFiveAgentCouncil:
    def test_arbitrage_scout_agent(self):
        scout = ArbitrageScoutAgent()
        # Normal
        v_norm = scout.evaluate("BTCTMN", None)
        assert v_norm.opinion == "NEUTRAL"
        assert v_norm.recommended_action == ActionType.HOLD

        # Discount opportunity
        arb_info = {"discrepancy_pct": -0.85, "net_edge_pct": 0.30, "is_actionable": True}
        v_disc = scout.evaluate("BTCTMN", arb_info)
        assert v_disc.opinion == "BULLISH"
        assert v_disc.recommended_action == ActionType.BUY

    def test_cio_prioritizes_arbitrage_edge(self):
        cio = ChiefInvestmentOfficerAgent()
        market_data = {
            "last_price_toman": 21_400_000_000.0,
            "best_bid_toman": 21_390_000_000.0,
            "best_ask_toman": 21_410_000_000.0,
            "spread_pct": 0.09,
        }
        technicals = {"rsi_14": 48.0, "ema_spread_pct": 0.05, "atr_pct": 1.2}
        orderbook = {"orderbook_imbalance": 0.05}
        portfolio = {"cash_toman": 4_000_000.0, "total_equity_toman": 5_000_000.0, "drawdown_pct": 0.0}
        arb_info = {"discrepancy_pct": -0.88, "net_edge_pct": 0.33, "is_actionable": True}

        decision: CouncilDecision = cio.convene_council(
            symbol="BTCTMN",
            market_data=market_data,
            technicals=technicals,
            orderbook=orderbook,
            portfolio=portfolio,
            arbitrage_info=arb_info,
        )

        assert decision.strategy_mode == "TRIANGULAR_ARBITRAGE"
        assert decision.action == ActionType.BUY
        assert len(decision.council_votes) == 4
        scout_vote = next(v for v in decision.council_votes if v.agent_name == "ArbitrageScout")
        assert scout_vote.opinion == "BULLISH"
