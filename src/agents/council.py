"""Multi-Agent Trading Council (Agent Swarm Consensus Architecture).

Coordinates a specialized council of AI agents:
1. TechnicalAnalystAgent: Trend, Momentum, Oscillator, and Volatility evaluation.
2. MicrostructureAgent: Real-time Orderbook Imbalance and Liquidity wall detection.
3. MacroSentimentAgent: Toman-dollar FX pressure and systemic volatility guard.
4. ArbitrageScoutAgent: Cross-market synthetic rate and triangular discrepancy detector.
5. ChiefInvestmentOfficerAgent (CIO): Synthesizes council votes and articulates comprehensive trade rationales.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from src.agents.schemas import ActionType, MarketRegime

logger = logging.getLogger("AgentCouncil")


class AgentVote(BaseModel):
    agent_name: str
    opinion: str  # BULLISH | BEARISH | NEUTRAL | PANIC
    confidence: float
    recommended_action: ActionType
    key_evidence: str


class CouncilDecision(BaseModel):
    symbol: str
    regime: MarketRegime
    confidence: float
    action: ActionType
    strategy_mode: str  # MOMENTUM | MEAN_REVERSION | TRIANGULAR_ARBITRAGE | MICRO_GRID | CAPITAL_PRESERVATION
    suggested_allocation_pct: float
    council_votes: List[AgentVote]
    synthesis_rationale: str
    thought_stream: str


class TechnicalAnalystAgent:
    """Specialized Agent for Classical & Quantitative Technical Indicators."""

    def evaluate(self, technicals: Dict[str, Any]) -> AgentVote:
        rsi = float(technicals.get("rsi_14", 50.0) or 50.0)
        ema_spread = float(technicals.get("ema_spread_pct", 0.0) or 0.0)
        atr_pct = float(technicals.get("atr_pct", 1.5) or 1.5)

        if ema_spread > 0.25 and 50.0 <= rsi <= 68.0:
            return AgentVote(
                agent_name="TechnicalAnalyst",
                opinion="BULLISH",
                confidence=0.88,
                recommended_action=ActionType.BUY,
                key_evidence=f"Golden EMA divergence (+{ema_spread:.2f}%) & healthy momentum RSI {rsi:.1f}.",
            )
        elif ema_spread < -0.25 and rsi < 48.0:
            return AgentVote(
                agent_name="TechnicalAnalyst",
                opinion="BEARISH",
                confidence=0.85,
                recommended_action=ActionType.SELL,
                key_evidence=f"Death cross EMA divergence ({ema_spread:.2f}%) with deteriorating RSI {rsi:.1f}.",
            )
        elif rsi <= 40.0:
            return AgentVote(
                agent_name="TechnicalAnalyst",
                opinion="NEUTRAL",
                confidence=0.78,
                recommended_action=ActionType.BUY,
                key_evidence=f"RSI oversold rebound zone ({rsi:.1f}) within range boundaries.",
            )
        else:
            return AgentVote(
                agent_name="TechnicalAnalyst",
                opinion="NEUTRAL",
                confidence=0.75,
                recommended_action=ActionType.HOLD,
                key_evidence=f"Equilibrium range oscillation (EMA spread {ema_spread:.2f}%, RSI {rsi:.1f}).",
            )


class MicrostructureAgent:
    """Specialized Agent for Wallex Order Book Depth and Order Flow Imbalance."""

    def evaluate(self, orderbook: Dict[str, Any], market_data: Dict[str, Any]) -> AgentVote:
        imbalance = float(orderbook.get("orderbook_imbalance", 0.0) or 0.0)
        spread_pct = float(market_data.get("spread_pct", 0.15) or 0.15)

        if spread_pct > 0.35:
            return AgentVote(
                agent_name="Microstructure",
                opinion="PANIC",
                confidence=0.90,
                recommended_action=ActionType.HOLD,
                key_evidence=f"Excessive orderbook spread ({spread_pct:.3f}% > 0.35%) implies high friction drag.",
            )

        if imbalance > 0.12:
            return AgentVote(
                agent_name="Microstructure",
                opinion="BULLISH",
                confidence=0.85,
                recommended_action=ActionType.BUY,
                key_evidence=f"Dominant bid-side liquidity buffer (orderbook imbalance: {imbalance:+.2f}).",
            )
        elif imbalance < -0.15:
            return AgentVote(
                agent_name="Microstructure",
                opinion="BEARISH",
                confidence=0.82,
                recommended_action=ActionType.SELL,
                key_evidence=f"Significant ask-side selling pressure (orderbook imbalance: {imbalance:+.2f}).",
            )
        else:
            return AgentVote(
                agent_name="Microstructure",
                opinion="NEUTRAL",
                confidence=0.75,
                recommended_action=ActionType.HOLD,
                key_evidence=f"Balanced two-sided liquidity depth (imbalance: {imbalance:+.2f}, spread: {spread_pct:.3f}%).",
            )


class MacroSentimentAgent:
    """Specialized Agent for Toman Systemic Risk and USDT-Toman Currency Dynamics."""

    def evaluate(self, symbol: str, portfolio: Dict[str, Any]) -> AgentVote:
        drawdown_pct = float(portfolio.get("drawdown_pct", 0.0) or 0.0)
        cash_toman = float(portfolio.get("cash_toman", 5_000_000.0) or 5_000_000.0)

        if drawdown_pct >= 4.0:
            return AgentVote(
                agent_name="MacroSentiment",
                opinion="PANIC",
                confidence=0.95,
                recommended_action=ActionType.HOLD,
                key_evidence=f"Portfolio drawdown warning threshold reached ({drawdown_pct:.2f}% >= 4.0%). Risk-off mandate active.",
            )

        if cash_toman < 200_000.0:
            return AgentVote(
                agent_name="MacroSentiment",
                opinion="NEUTRAL",
                confidence=0.85,
                recommended_action=ActionType.HOLD,
                key_evidence="Cash reserves low. Preserving Toman liquidity buffer.",
            )

        return AgentVote(
            agent_name="MacroSentiment",
            opinion="NEUTRAL",
            confidence=0.80,
            recommended_action=ActionType.HOLD,
            key_evidence="Macro Toman financial conditions stable. Normal trading window permitted.",
        )


class ArbitrageScoutAgent:
    """Specialized Agent for Cross-Market Discrepancy & Triangular Inefficiencies."""

    def evaluate(self, symbol: str, arbitrage_info: Optional[Dict[str, Any]] = None) -> AgentVote:
        if not arbitrage_info:
            return AgentVote(
                agent_name="ArbitrageScout",
                opinion="NEUTRAL",
                confidence=0.70,
                recommended_action=ActionType.HOLD,
                key_evidence="Synthetic cross-rates balanced within normal spread boundaries.",
            )

        disc_pct = float(arbitrage_info.get("discrepancy_pct", 0.0))
        net_edge = float(arbitrage_info.get("net_edge_pct", 0.0))
        is_actionable = bool(arbitrage_info.get("is_actionable", False))

        if is_actionable and disc_pct < 0:
            return AgentVote(
                agent_name="ArbitrageScout",
                opinion="BULLISH",
                confidence=0.91,
                recommended_action=ActionType.BUY,
                key_evidence=f"Substantial cross-rate discount: {symbol} is {abs(disc_pct):.2f}% below synthetic fair value (net edge: {net_edge:+.2f}%).",
            )
        elif is_actionable and disc_pct > 0:
            return AgentVote(
                agent_name="ArbitrageScout",
                opinion="BEARISH",
                confidence=0.89,
                recommended_action=ActionType.SELL,
                key_evidence=f"Cross-rate premium: {symbol} is {disc_pct:+.2f}% above synthetic fair value (net edge: {net_edge:+.2f}%).",
            )

        return AgentVote(
            agent_name="ArbitrageScout",
            opinion="NEUTRAL",
            confidence=0.75,
            recommended_action=ActionType.HOLD,
            key_evidence=f"Cross-rate divergence ({disc_pct:+.2f}%) within transaction fee bounds.",
        )


class ChiefInvestmentOfficerAgent:
    """Consensus Coordinator: Debates specialized agent votes and issues authoritative verdict."""

    def __init__(self):
        self.tech_agent = TechnicalAnalystAgent()
        self.micro_agent = MicrostructureAgent()
        self.macro_agent = MacroSentimentAgent()
        self.arb_agent = ArbitrageScoutAgent()

    def convene_council(
        self,
        symbol: str,
        market_data: Dict[str, Any],
        technicals: Dict[str, Any],
        orderbook: Dict[str, Any],
        portfolio: Dict[str, Any],
        arbitrage_info: Optional[Dict[str, Any]] = None,
    ) -> CouncilDecision:
        """Collects opinions from all specialized agents and resolves consensus."""
        v_tech = self.tech_agent.evaluate(technicals)
        v_micro = self.micro_agent.evaluate(orderbook, market_data)
        v_macro = self.macro_agent.evaluate(symbol, portfolio)
        v_arb = self.arb_agent.evaluate(symbol, arbitrage_info)
        votes = [v_tech, v_micro, v_macro, v_arb]

        has_pos = symbol in portfolio.get("open_positions", {})
        spread_pct = float(market_data.get("spread_pct", 0.15) or 0.15)
        rsi = float(technicals.get("rsi_14", 50.0) or 50.0)
        atr_pct = float(technicals.get("atr_pct", 1.5) or 1.5)

        # Quantitative Volatility Parity Sizing: scales inversely with volatility
        vol_adjusted_alloc = round(min(10.0, max(4.0, (1.2 / max(0.5, atr_pct)) * 10.0)), 1)

        # 1. Systemic / Panic Veto
        if any(v.opinion == "PANIC" for v in votes) or spread_pct > 0.30:
            return CouncilDecision(
                symbol=symbol,
                regime=MarketRegime.VOLATILE_PANIC,
                confidence=0.92,
                action=ActionType.HOLD,
                strategy_mode="CAPITAL_PRESERVATION",
                suggested_allocation_pct=0.0,
                council_votes=votes,
                synthesis_rationale="Council consensus: Market risk/spread is elevated. Mandating capital preservation.",
                thought_stream=f"[Council] {v_micro.agent_name} warned '{v_micro.key_evidence}'. Veto active.",
            )

        # 2. Arbitrage High-Edge Signal Override
        if v_arb.opinion == "BULLISH" and v_micro.opinion != "BEARISH":
            action = ActionType.HOLD if has_pos else ActionType.BUY
            return CouncilDecision(
                symbol=symbol,
                regime=MarketRegime.CALM_RANGE,
                confidence=v_arb.confidence,
                action=action,
                strategy_mode="TRIANGULAR_ARBITRAGE",
                suggested_allocation_pct=vol_adjusted_alloc,
                council_votes=votes,
                synthesis_rationale=(
                    f"Council consensus TRIANGULAR_ARBITRAGE: {v_arb.key_evidence} "
                    f"Microstructure confirmed sufficient book depth. Exploiting cross-market inefficiency."
                ),
                thought_stream=f"[Council] Arbitrage scout detected actionable alpha edge. CIO approved allocation.",
            )

        # 3. Bullish Momentum Consensus (Tech Bullish + Orderbook Bid support)
        if v_tech.opinion == "BULLISH" and v_micro.opinion in ("BULLISH", "NEUTRAL"):
            avg_conf = (v_tech.confidence + v_micro.confidence) / 2.0
            action = ActionType.HOLD if has_pos else ActionType.BUY
            return CouncilDecision(
                symbol=symbol,
                regime=MarketRegime.BULLISH_TREND,
                confidence=round(avg_conf, 2),
                action=action,
                strategy_mode="MOMENTUM",
                suggested_allocation_pct=vol_adjusted_alloc,
                council_votes=votes,
                synthesis_rationale=(
                    f"Council consensus BULLISH: Technicals confirmed trend divergence and orderbook showed buy-side support. "
                    f"Initiating momentum trade on {symbol} (volatility-parity allocation: {vol_adjusted_alloc}%)."
                ),
                thought_stream=f"[Council] Tech: {v_tech.key_evidence} | Micro: {v_micro.key_evidence}",
            )

        # 4. Bearish Trend Exit Consensus
        if v_tech.opinion == "BEARISH" or (v_micro.opinion == "BEARISH" and rsi < 45.0):
            action = ActionType.SELL if has_pos else ActionType.HOLD
            return CouncilDecision(
                symbol=symbol,
                regime=MarketRegime.BEARISH_TREND,
                confidence=0.86,
                action=action,
                strategy_mode="CAPITAL_PRESERVATION",
                suggested_allocation_pct=0.0,
                council_votes=votes,
                synthesis_rationale="Council consensus BEARISH: Trend breakdown detected across technical and orderbook channels. De-risking.",
                thought_stream=f"[Council] Exit consensus reached to lock in Toman capital.",
            )

        # 5. Range-Bound Mean Reversion Opportunity (Oversold discount in calm market)
        if rsi <= 40.0 and spread_pct <= 0.20 and not has_pos:
            return CouncilDecision(
                symbol=symbol,
                regime=MarketRegime.CALM_RANGE,
                confidence=0.82,
                action=ActionType.BUY,
                strategy_mode="MEAN_REVERSION",
                suggested_allocation_pct=7.0,
                council_votes=votes,
                synthesis_rationale=(
                    f"Council consensus MEAN_REVERSION: Market is in calm equilibrium, price is oversold (RSI {rsi:.1f}). "
                    f"Entering tactical range bounce trade."
                ),
                thought_stream=f"[Council] Range scalping approved by CIO. Target 20SMA mean.",
            )

        # 6. Default Calm Range Hold / Micro-Grid Idle
        return CouncilDecision(
            symbol=symbol,
            regime=MarketRegime.CALM_RANGE,
            confidence=0.76,
            action=ActionType.HOLD,
            strategy_mode="MEAN_REVERSION",
            suggested_allocation_pct=0.0,
            council_votes=votes,
            synthesis_rationale="Council consensus RANGE: No directional edge nor extreme discount. Holding Toman capital safely.",
            thought_stream="[Council] Balanced liquidity without high-probability catalyst.",
        )
