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
from src.agents.council import ChiefInvestmentOfficerAgent, CouncilDecision
from src.mcp.tools import WallexMCPToolSet
from src.monitoring.logger import DecisionLogger

logger = logging.getLogger("AgenticTrader")


class AgenticTrader:
    """Autonomous ReAct AI Agent for Wallex Algorithmic Trading with Multi-Agent Swarm."""

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
        self.cio = ChiefInvestmentOfficerAgent()

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
        triangular_scans = await self.tools.get_triangular_arbitrage_scan()
        cycle_summary["observations"]["market_overview"] = overview
        cycle_summary["observations"]["portfolio"] = portfolio
        cycle_summary["observations"]["triangular_arbitrage"] = triangular_scans

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

            # Match potential triangular arbitrage information
            base_coin = sym.replace("TMN", "")
            arb_info = next((d for d in triangular_scans if d.get("base_coin") == base_coin), None)

            # Step 2: Reasoning Engine (LLM or High-Grade Local Cognitive Engine)
            reasoning = await self._analyze_and_reason(
                symbol=sym,
                market_data=market_data,
                technicals=technicals,
                orderbook=orderbook,
                portfolio=portfolio,
                arbitrage_info=arb_info,
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
                    "strategy_mode": reasoning.get("strategy_mode", "ADAPTIVE"),
                    "council_votes": reasoning.get("council_votes", []),
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
        arbitrage_info: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Generates deep reasoning incorporating technicals, orderbook pressure, and portfolio risk."""
        # Convene specialized AI agents
        council_res: CouncilDecision = self.cio.convene_council(
            symbol=symbol,
            market_data=market_data,
            technicals=technicals,
            orderbook=orderbook,
            portfolio=portfolio,
            arbitrage_info=arbitrage_info,
        )

        if self.api_key:
            try:
                llm_res = await self._call_llm_reasoner(symbol, market_data, technicals, orderbook, portfolio, council_res)
                llm_res["council_votes"] = [v.model_dump() for v in council_res.council_votes]
                return llm_res
            except Exception as e:
                logger.warning("LLM reasoning failed (%s). Using Multi-Agent Council verdict.", e)

        return {
            "regime": council_res.regime.value,
            "confidence": council_res.confidence,
            "action": council_res.action.value,
            "strategy_mode": council_res.strategy_mode,
            "suggested_allocation_pct": council_res.suggested_allocation_pct,
            "thought_process": council_res.thought_stream,
            "rationale": council_res.synthesis_rationale,
            "council_votes": [v.model_dump() for v in council_res.council_votes],
        }
    def _cognitive_semantic_reasoning(
        self,
        symbol: str,
        market_data: Dict[str, Any],
        technicals: Dict[str, Any],
        orderbook: Dict[str, Any],
        portfolio: Dict[str, Any],
        arbitrage_info: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Deterministic Cognitive Multi-Agent Council Reasoning Engine."""
        council_res = self.cio.convene_council(
            symbol=symbol,
            market_data=market_data,
            technicals=technicals,
            orderbook=orderbook,
            portfolio=portfolio,
            arbitrage_info=arbitrage_info,
        )
        return {
            "regime": council_res.regime.value,
            "confidence": council_res.confidence,
            "action": council_res.action.value,
            "strategy_mode": council_res.strategy_mode,
            "suggested_allocation_pct": council_res.suggested_allocation_pct,
            "thought_process": council_res.thought_stream,
            "rationale": council_res.synthesis_rationale,
            "council_votes": [v.model_dump() for v in council_res.council_votes],
        }


    async def _call_llm_reasoner(
        self,
        symbol: str,
        market_data: Dict[str, Any],
        technicals: Dict[str, Any],
        orderbook: Dict[str, Any],
        portfolio: Dict[str, Any],
        council_res: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """Calls Gemini API for Deep Structured Trading Reasoning."""
        system_prompt = (
            "You are the Chief Investment Officer (CIO) of an Agentic AI quantitative fund in a 3-day competition with 5,000,000 TMN. "
            "Review specialized agent votes (Technical Analyst, Microstructure, Macro Sentiment) along with orderbook depth and technicals. "
            "Synthesize the debate and decide BUY/SELL/HOLD. Return strict JSON with keys: regime, confidence, action, strategy_mode, suggested_allocation_pct, thought_process, rationale."
        )

        user_content = json.dumps({
            "symbol": symbol,
            "market_data": market_data,
            "technicals": technicals,
            "orderbook": orderbook,
            "portfolio": portfolio,
            "specialized_council_votes": [v.model_dump() for v in council_res.council_votes] if council_res else [],
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
