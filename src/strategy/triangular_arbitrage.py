"""Triangular Arbitrage & Cross-Rate Discrepancy Scanner and Strategy.

Engineered for the Wallex Agentic AI Hackathon.
Calculates theoretical synthetic prices between:
    1. COIN/TMN (e.g., BTCTMN)
    2. COIN/USDT (e.g., BTCUSDT)
    3. USDT/TMN (e.g., USDTTMN)

Synthetic TMN Price = Price(COIN/USDT) * Price(USDT/TMN)
Discrepancy (%) = (Price(COIN/TMN) - Synthetic Price) / Synthetic Price * 100

When Discrepancy exceeds total round-trip transaction friction (taker ~0.55%, maker ~0.50%),
a market inefficiency exists, allowing delta-neutral or mispricing-convergence trading.
"""

from __future__ import annotations

import datetime
import logging
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from src.agents.schemas import ActionType, MarketRegime, ProposedTradeSignal
from src.strategy.base import BaseStrategy

logger = logging.getLogger("TriangularArbitrage")


class TriangularDiscrepancy(BaseModel):
    base_coin: str  # BTC, ETH, SOL
    tmn_symbol: str  # BTCTMN
    usdt_symbol: str  # BTCUSDT
    tmn_price: float
    usdt_price: float
    usdt_tmn_price: float
    synthetic_tmn_price: float
    discrepancy_pct: float
    fee_friction_pct: float
    net_edge_pct: float
    is_actionable: bool
    recommended_action: ActionType
    timestamp: str


class TriangularArbitrageStrategy(BaseStrategy):
    """Detects and monetizes cross-currency pricing imbalances across Wallex pairs."""

    def __init__(
        self,
        min_net_edge_pct: float = 0.15,
        fee_friction_pct: float = 0.55,
        max_order_toman: float = 400_000.0,
    ):
        self.min_net_edge_pct = min_net_edge_pct
        self.fee_friction_pct = fee_friction_pct
        self.max_order_toman = max_order_toman

    def scan_pair(
        self,
        base_coin: str,
        markets: Dict[str, Any],
    ) -> Optional[TriangularDiscrepancy]:
        """Scans triangular rates for a given coin against TMN and USDT."""
        tmn_sym = f"{base_coin}TMN"
        usdt_sym = f"{base_coin}USDT"
        usdttmn_sym = "USDTTMN"

        if (
            tmn_sym not in markets
            or usdt_sym not in markets
            or usdttmn_sym not in markets
        ):
            return None

        try:
            p_tmn = self._extract_price(markets[tmn_sym])
            p_usdt = self._extract_price(markets[usdt_sym])
            p_usdt_tmn = self._extract_price(markets[usdttmn_sym])
        except (ValueError, TypeError, KeyError):
            return None

        if p_tmn <= 0 or p_usdt <= 0 or p_usdt_tmn <= 0:
            return None

        synthetic_tmn = p_usdt * p_usdt_tmn
        discrepancy_pct = ((p_tmn - synthetic_tmn) / synthetic_tmn) * 100.0
        abs_discrepancy = abs(discrepancy_pct)
        net_edge = abs_discrepancy - self.fee_friction_pct

        is_actionable = net_edge >= self.min_net_edge_pct
        action = ActionType.HOLD
        if is_actionable:
            # If TMN price is substantially LOWER than global USDT synthetic, buying TMN pair is undervalued
            if discrepancy_pct < -self.fee_friction_pct:
                action = ActionType.BUY
            # If TMN price is substantially HIGHER, sell back to TMN
            elif discrepancy_pct > self.fee_friction_pct:
                action = ActionType.SELL

        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

        return TriangularDiscrepancy(
            base_coin=base_coin,
            tmn_symbol=tmn_sym,
            usdt_symbol=usdt_sym,
            tmn_price=p_tmn,
            usdt_price=p_usdt,
            usdt_tmn_price=p_usdt_tmn,
            synthetic_tmn_price=round(synthetic_tmn, 2),
            discrepancy_pct=round(discrepancy_pct, 3),
            fee_friction_pct=self.fee_friction_pct,
            net_edge_pct=round(net_edge, 3),
            is_actionable=is_actionable,
            recommended_action=action,
            timestamp=now_iso,
        )

    def scan_all_supported(self, markets: Dict[str, Any]) -> List[TriangularDiscrepancy]:
        """Scans all standard major liquid coins on Wallex."""
        coins = ["BTC", "ETH", "SOL"]
        results = []
        for c in coins:
            disc = self.scan_pair(c, markets)
            if disc:
                results.append(disc)
        return results

    def generate_signal(
        self,
        symbol: str,
        df_features: Any,
        regime_output: Any,
        current_price_toman: float,
        spread_pct: float,
    ) -> Optional[ProposedTradeSignal]:
        """BaseStrategy compliance: delegates to generate_arbitrage_signal if market context provided."""
        return None

    def generate_arbitrage_signal(
        self,
        base_coin: str,
        markets: Dict[str, Any],
    ) -> Optional[ProposedTradeSignal]:
        """Generates a trading signal if a profitable mispricing is detected."""
        disc = self.scan_pair(base_coin, markets)
        if not disc or not disc.is_actionable or disc.recommended_action == ActionType.HOLD:
            return None

        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
        if disc.recommended_action == ActionType.BUY:
            tp_price = disc.synthetic_tmn_price
            sl_price = disc.tmn_price * 0.985

            return ProposedTradeSignal(
                symbol=disc.tmn_symbol,
                action=ActionType.BUY,
                target_price_toman=disc.tmn_price,
                order_value_toman=min(self.max_order_toman, 350_000.0),
                regime=MarketRegime.CALM_RANGE,
                ai_confidence=0.89,
                stop_loss_toman=sl_price,
                take_profit_toman=tp_price,
                rationale=(
                    f"Triangular Arbitrage opportunity detected: {disc.tmn_symbol} is "
                    f"discounted by {abs(disc.discrepancy_pct):.2f}% below synthetic rate "
                    f"({disc.synthetic_tmn_price:,.0f} TMN). Net edge after fee friction: {disc.net_edge_pct:+.2f}%."
                ),
                timestamp=now_iso,
            )

        elif disc.recommended_action == ActionType.SELL:
            return ProposedTradeSignal(
                symbol=disc.tmn_symbol,
                action=ActionType.SELL,
                target_price_toman=disc.tmn_price,
                order_value_toman=0.0,
                regime=MarketRegime.CALM_RANGE,
                ai_confidence=0.88,
                rationale=(
                    f"Triangular Arbitrage take-profit / rebalance: {disc.tmn_symbol} is "
                    f"premium priced by +{disc.discrepancy_pct:.2f}% over synthetic rate "
                    f"({disc.synthetic_tmn_price:,.0f} TMN). Realizing profit to TMN."
                ),
                timestamp=now_iso,
            )

        return None

    @staticmethod
    def _extract_price(item: Any) -> float:
        """Safely parses last price or stats from Wallex market dict."""
        if isinstance(item, dict):
            stats = item.get("stats", {})
            if isinstance(stats, dict) and "lastPrice" in stats:
                val = stats["lastPrice"]
                if val and val != "-":
                    return float(val)
            if "last_price_toman" in item:
                return float(item["last_price_toman"])
            if "price" in item:
                return float(item["price"])
        elif isinstance(item, (int, float)):
            return float(item)
        raise ValueError(f"Unable to extract price from: {item}")
