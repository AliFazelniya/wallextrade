"""Agentic Trading Brain (Autonomous ReAct Trading Agent).

Integrates Wallex MCP Tools, Deep Reasoning, Risk Gatekeeping, and
Structured Decision Logging. Evaluates market conditions through an iterative
Tool-Use and Reasoning loop (Observation -> Thought -> Action -> Verification).
"""

from __future__ import annotations

import datetime
import json
import logging
import os
from typing import Any, Dict, List, Optional
import httpx

from src.agents.schemas import ActionType, MarketRegime
from src.mcp.tools import WallexMCPToolSet
from src.monitoring.logger import DecisionLogger

logger = logging.getLogger("AgenticTrader")


class AgenticTrader:
    """Autonomous ReAct AI Agent for Wallex Algorithmic Trading."""

    def __init__(
        self,
        toolset: WallexMCPToolSet,
        decision_logger: Optional[DecisionLogger] = None,
        api_key: Optional[str] = None,
        model_name: str = "gemini-2.5-flash",
        max_order_toman: float = 500_000.0,
    ):
        self.tools = toolset
        self.logger = decision_logger or DecisionLogger(log_path="logs/trading_decisions.jsonl")
        self.api_key = api_key or os.getenv("GEMINI_API_KEY") or os.getenv("OPENAI_API_KEY")
        self.model_name = model_name
        self.max_order_toman = max_order_toman

    async def run_cycle(self, candidate_symbols: Optional[List[str]] = None) -> Dict[str, Any]:
        """Executes a full autonomous ReAct decision cycle across candidate symbols.
        
        Steps:
        1. Observation (Tools): Fetch market overview, orderbook depth, and technicals.
        2. Portfolio Inspection: Check available cash, crypto exposure, and drawdown.
        3. Thought & Reasoning: Synthesize regime, momentum, orderbook imbalance, and risk.
        4. Action: Formulate trade intent or pass, route through independent risk engine.
        5. Audit: Log complete reasoning rationale for hackathon judges.
        """
        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
        cycle_summary: Dict[str, Any] = {
            "timestamp": now_iso,
            "observations": {},
            "decisions": [],
            "actions_taken": [],
        }

        # Step 1: Observation via MCP Tools
        overview = await self.tools.get_market_overview(candidate_symbols)
        portfolio = self.tools.get_portfolio_status()
        cycle_summary["observations"]["market_overview"] = overview
        cycle_summary["observations"]["portfolio"] = portfolio

        symbols_to_evaluate = [s for s in overview if not s.startswith("error")]

        for sym in symbols_to_evaluate:
            market_data = overview[sym]
            last_price = market_data["last_price_toman"]
            spread_pct = market_data["spread_pct"]

            # Filter unviable spreads (> 0.25%)
            if spread_pct > 0.25:
                logger.info("[%s] Spread too wide (%.3f%% > 0.25%%). Skipping.", sym, spread_pct)
                continue

            # Fetch deep features
            technicals = await self.tools.get_technical_features(sym, "15")
            orderbook = await self.tools.get_orderbook_depth(sym)

            # Step 2: Reasoning Engine (LLM or High-Grade Local Cognitive Engine)
            reasoning = await self._analyze_and_reason(
                symbol=sym,
                market_data=market_data,
                technicals=technicals,
                orderbook=orderbook,
                portfolio=portfolio,
            )

            cycle_summary["decisions"].append({
                "symbol": sym,
                "regime": reasoning["regime"],
                "confidence": reasoning["confidence"],
                "recommended_action": reasoning["action"],
                "thought_process": reasoning["thought_process"],
                "rationale": reasoning["rationale"],
            })

            # Step 3: Action Execution if BUY or SELL recommended
            action_str = reasoning.get("action", "HOLD")
            exec_result = None
            target_amount = 0.0
            if action_str in ("BUY", "SELL"):
                # Size calculation: 10% of portfolio or capped at max_order_toman (500k)
                target_amount = min(
                    self.max_order_toman,
                    portfolio["total_equity_toman"] * (reasoning["suggested_allocation_pct"] / 100.0)
                ) if action_str == "BUY" else 0.0

                exec_result = await self.tools.execute_guarded_order(
                    symbol=sym,
                    action=action_str,
                    target_price=last_price,
                    amount_toman=target_amount,
                    rationale=reasoning["rationale"],
                )
                cycle_summary["actions_taken"].append(exec_result)

            # Step 4: Full Audit Trail Logging (BUY, SELL, and reasoned HOLD)
            self.logger.log_decision(
                timestamp=now_iso,
                symbol=sym,
                event_type=f"AGENT_DECISION_{action_str}",
                market_observations={
                    "price": last_price,
                    "spread_pct": spread_pct,
                    "orderbook_imbalance": orderbook.get("orderbook_imbalance"),
                    "rsi": technicals.get("rsi_14"),
                    "ema_spread": technicals.get("ema_spread_pct"),
                },
                regime_classification={
                    "regime": reasoning["regime"],
                    "confidence": reasoning["confidence"],
                    "reasoning": reasoning["rationale"],
                },
                proposed_signal={
                    "action": action_str,
                    "price": last_price,
                    "amount": target_amount,
                    "thought_process": reasoning["thought_process"],
                },
                risk_evaluation=exec_result.get("risk_evaluation") if exec_result else None,
                execution_result=exec_result.get("execution") if exec_result else None,
                portfolio_summary=portfolio,
                notes=f"Agentic AI autonomous decision: {reasoning['rationale']}",
            )

        return cycle_summary

    async def _analyze_and_reason(
        self,
        symbol: str,
        market_data: Dict[str, Any],
        technicals: Dict[str, Any],
        orderbook: Dict[str, Any],
        portfolio: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Generates deep reasoning incorporating technicals, orderbook pressure, and portfolio risk."""
        if self.api_key:
            try:
                return await self._call_llm_reasoner(symbol, market_data, technicals, orderbook, portfolio)
            except Exception as e:
                logger.warning("LLM reasoning failed (%s). Using Cognitive Semantic Engine.", e)

        return self._cognitive_semantic_reasoning(symbol, market_data, technicals, orderbook, portfolio)

    def _cognitive_semantic_reasoning(
        self,
        symbol: str,
        market_data: Dict[str, Any],
        technicals: Dict[str, Any],
        orderbook: Dict[str, Any],
        portfolio: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Deterministic Cognitive Semantic Reasoning Engine."""
        rsi = technicals.get("rsi_14", 50.0) or 50.0
        ema_spread = technicals.get("ema_spread_pct", 0.0) or 0.0
        atr_pct = technicals.get("atr_pct", 1.5) or 1.5
        vol_ratio = technicals.get("vol_ratio", 1.0) or 1.0
        imbalance = orderbook.get("orderbook_imbalance", 0.0) or 0.0
        spread_pct = market_data.get("spread_pct", 0.15)
        has_pos = symbol in portfolio.get("open_positions", {})

        # 1. Panic / Extreme Volatility check
        if atr_pct > 5.0 or spread_pct > 0.30:
            return {
                "regime": MarketRegime.VOLATILE_PANIC.value,
                "confidence": 0.90,
                "action": "HOLD",
                "suggested_allocation_pct": 0.0,
                "thought_process": f"High market turbulence (ATR={atr_pct:.2f}%, spread={spread_pct:.3f}%). Capital preservation mandates zero exposure.",
                "rationale": "Extreme volatility detected. Capital preservation priority.",
            }

        # 2. Strong Bullish Trend + Buying Orderbook Pressure
        if ema_spread > 0.25 and 50.0 <= rsi <= 68.0 and imbalance > 0.05 and vol_ratio >= 1.05:
            return {
                "regime": MarketRegime.BULLISH_TREND.value,
                "confidence": 0.88,
                "action": "HOLD" if has_pos else "BUY",
                "suggested_allocation_pct": 10.0,
                "thought_process": (
                    f"Positive EMA divergence (+{ema_spread:.2f}%) aligned with constructive RSI ({rsi:.1f}) "
                    f"and orderbook bid support (imbalance {imbalance:+.2f}). High-probability trend continuation."
                ),
                "rationale": f"Bullish momentum confirmed across trend, volume ({vol_ratio:.2f}x) and orderbook pressure.",
            }

        # 3. Bearish Trend / Reversal Danger
        if (ema_spread < -0.25 and rsi < 48.0) or (has_pos and rsi < 42.0):
            return {
                "regime": MarketRegime.BEARISH_TREND.value,
                "confidence": 0.85,
                "action": "SELL" if has_pos else "HOLD",
                "suggested_allocation_pct": 0.0,
                "thought_process": f"Bearish EMA cross ({ema_spread:.2f}%) and deteriorating momentum (RSI={rsi:.1f}). De-risking position.",
                "rationale": "Bearish trend structure detected. Exit to protect Toman capital.",
            }

        # 4. Range / Neutral Market
        return {
            "regime": MarketRegime.CALM_RANGE.value,
            "confidence": 0.75,
            "action": "HOLD",
            "suggested_allocation_pct": 0.0,
            "thought_process": f"Market within flat oscillation range (EMA spread={ema_spread:.2f}%, RSI={rsi:.1f}). No clear directional edge.",
            "rationale": "Calm range regime. Avoiding unnecessary fee friction.",
        }

    async def _call_llm_reasoner(
        self,
        symbol: str,
        market_data: Dict[str, Any],
        technicals: Dict[str, Any],
        orderbook: Dict[str, Any],
        portfolio: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Calls Gemini API for Deep Structured Trading Reasoning."""
        system_prompt = (
            "You are an expert quantitative hedge-fund agent for a 3-day competition with 5,000,000 TMN. "
            "Analyze market technicals, orderbook depth, and portfolio state to classify regime and decide BUY/SELL/HOLD. "
            "Return strict JSON with keys: regime, confidence, action, suggested_allocation_pct, thought_process, rationale."
        )

        user_content = json.dumps({
            "symbol": symbol,
            "market_data": market_data,
            "technicals": technicals,
            "orderbook": orderbook,
            "portfolio": portfolio,
        }, ensure_ascii=False)

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent?key={self.api_key}"
        payload = {
            "contents": [{"parts": [{"text": f"{system_prompt}\n\nContext:\n{user_content}"}]}],
            "generationConfig": {"response_mime_type": "application/json", "temperature": 0.1},
        }

        async with httpx.AsyncClient(timeout=6.0) as client:
            resp = await client.post(url, json=payload)
            if resp.status_code != 200:
                raise ValueError(f"Gemini API returned {resp.status_code}")
            data = resp.json()
            text = data["candidates"][0]["content"]["parts"][0]["text"]
            return json.loads(text)
