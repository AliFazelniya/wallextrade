"""Wallex MCP Tools Implementation.

Provides structured tools conforming to the Model Context Protocol (MCP)
for Agentic AI to inspect market depth, trades, technical features,
portfolio state, and submit guarded orders.
"""

from __future__ import annotations

import datetime
from typing import Any, Dict, List, Optional
import pandas as pd

from src.data.client import WallexClient
from src.data.fetcher import MarketDataFetcher
from src.features.indicators import extract_features, get_latest_feature_snapshot
from src.portfolio.accounting import PortfolioEngine
from src.risk.engine import RiskEngine
from src.exchange.adapter import ExchangeAdapter
from src.agents.schemas import ActionType, ProposedTradeSignal, MarketRegime


class WallexMCPToolSet:
    """Core toolset exposed to AI Agents through Model Context Protocol (MCP)."""

    def __init__(
        self,
        client: WallexClient,
        portfolio: PortfolioEngine,
        risk_engine: RiskEngine,
        adapter: ExchangeAdapter,
    ):
        self.client = client
        self.fetcher = MarketDataFetcher(client)
        self.portfolio = portfolio
        self.risk_engine = risk_engine
        self.adapter = adapter

    async def get_market_overview(self, symbols: Optional[List[str]] = None) -> Dict[str, Any]:
        """Tool: Fetches real-time price, best bid, best ask, and spread for allowed symbols."""
        target_symbols = symbols or list(self.risk_engine.allowed_symbols) or ["BTCTMN", "USDTTMN", "ETHTMN", "SOLTMN"]
        overview: Dict[str, Any] = {}
        
        try:
            markets_resp = await self.client.get_markets()
            symbols_data = markets_resp.get("result", {}).get("symbols", {})
            for sym in target_symbols:
                if sym in symbols_data:
                    stats = symbols_data[sym].get("stats", {})
                    def _safe_f(v, d=0.0):
                        try:
                            return float(v) if v and v != "-" else d
                        except (ValueError, TypeError):
                            return d
                    last_price = _safe_f(stats.get("lastPrice"), 0.0)
                    bid_price = _safe_f(stats.get("bidPrice"), last_price * 0.999)
                    ask_price = _safe_f(stats.get("askPrice"), last_price * 1.001)
                    spread_pct = ((ask_price - bid_price) / last_price * 100.0) if last_price > 0 else 0.15
                    overview[sym] = {
                        "last_price_toman": last_price,
                        "best_bid_toman": bid_price,
                        "best_ask_toman": ask_price,
                        "spread_pct": round(spread_pct, 4),
                        "24h_volume": _safe_f(stats.get("24h_volume"), 0.0),
                    }
        except Exception as exc:
            overview["error"] = str(exc)

        return overview

    async def get_orderbook_depth(self, symbol: str) -> Dict[str, Any]:
        """Tool: Inspects top order book depth to evaluate bid/ask imbalance and liquidity."""
        try:
            depth = await self.client.get_depth(symbol)
            result = depth.get("result", {})
            bids = result.get("bid", [])[:5]
            asks = result.get("ask", [])[:5]
            
            total_bid_vol = sum(float(b.get("quantity", 0)) for b in bids)
            total_ask_vol = sum(float(a.get("quantity", 0)) for a in asks)
            imbalance = (total_bid_vol - total_ask_vol) / (total_bid_vol + total_ask_vol + 1e-9)

            # Multi-level exponential decay weighting (Cartea-Jaimungal microstructure model)
            import math
            w_bid = sum(float(b.get("quantity", 0)) * math.exp(-0.35 * i) for i, b in enumerate(bids))
            w_ask = sum(float(a.get("quantity", 0)) * math.exp(-0.35 * i) for i, a in enumerate(asks))
            weighted_imbalance = (w_bid - w_ask) / (w_bid + w_ask + 1e-9)
            
            return {
                "symbol": symbol,
                "top_5_bids": bids,
                "top_5_asks": asks,
                "bid_volume": total_bid_vol,
                "ask_volume": total_ask_vol,
                "orderbook_imbalance": round(imbalance, 3),  # >0: buying pressure, <0: selling pressure
                "weighted_depth_imbalance": round(weighted_imbalance, 3),
            }
        except Exception as exc:
            return {"symbol": symbol, "error": str(exc)}

    async def get_technical_features(self, symbol: str, resolution: str = "15") -> Dict[str, Any]:
        """Tool: Computes deterministic quantitative indicators (EMA 20/50, RSI 14, ATR, Vol Ratio)."""
        now_ts = int(datetime.datetime.now(datetime.timezone.utc).timestamp())
        from_ts = now_ts - (7 * 86400)  # 7 days of candles
        
        try:
            df, audit = await self.fetcher.fetch_ohlcv_dataframe(symbol, resolution, from_ts, now_ts)
            if df.empty or len(df) < 30:
                return {"symbol": symbol, "status": "INSUFFICIENT_DATA", "count": len(df)}
            
            df_feat = extract_features(df)
            snapshot = get_latest_feature_snapshot(df_feat)
            cur_price = float(df_feat.iloc[-1]["close"])
            
            return {
                "symbol": symbol,
                "timestamp": snapshot.get("timestamp"),
                "current_price_toman": cur_price,
                "ema_20": snapshot.get("ema_20"),
                "ema_50": snapshot.get("ema_50"),
                "ema_spread_pct": snapshot.get("ema_spread_pct"),
                "rsi_14": snapshot.get("rsi_14"),
                "atr_pct": snapshot.get("atr_pct"),
                "vol_ratio": snapshot.get("vol_ratio"),
                "trend_direction": snapshot.get("trend_direction"),
            }
        except Exception as exc:
            return {"symbol": symbol, "error": str(exc)}

    def get_portfolio_status(self) -> Dict[str, Any]:
        """Tool: Retrieves Toman cash balance, open positions, unrealized P&L and drawdown."""
        equity = self.portfolio.get_total_equity()
        crypto_val = sum(p.market_value_toman for p in self.portfolio.positions.values())
        return {
            "cash_toman": round(self.portfolio.cash_toman, 0),
            "crypto_value_toman": round(crypto_val, 0),
            "total_equity_toman": round(equity, 0),
            "net_realized_pnl_toman": round(self.portfolio.net_realized_pnl_toman, 0),
            "gross_realized_pnl_toman": round(self.portfolio.gross_realized_pnl_toman, 0),
            "total_fees_paid_toman": round(self.portfolio.total_fees_paid_toman, 0),
            "drawdown_pct": round(self.portfolio.get_drawdown_pct(), 2),
            "open_positions": {
                s: {
                    "quantity": p.quantity,
                    "avg_entry_price": p.avg_entry_price,
                    "current_price": p.current_price,
                    "unrealized_pnl_toman": round(p.unrealized_pnl_toman, 0),
                    "unrealized_pnl_pct": round(p.unrealized_pnl_pct, 2),
                }
                for s, p in self.portfolio.positions.items()
            },
        }

    async def execute_guarded_order(
        self,
        symbol: str,
        action: str,
        target_price: float,
        amount_toman: float,
        rationale: str,
    ) -> Dict[str, Any]:
        """Tool: Submits an order through the independent deterministic risk engine."""
        act_enum = ActionType(action.upper())
        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
        
        signal = ProposedTradeSignal(
            symbol=symbol,
            action=act_enum,
            target_price_toman=target_price,
            order_value_toman=amount_toman,
            regime=MarketRegime.BULLISH_TREND if act_enum == ActionType.BUY else MarketRegime.BEARISH_TREND,
            ai_confidence=0.85,
            rationale=rationale,
            timestamp=now_iso,
        )

        current_equity = self.portfolio.get_total_equity()
        crypto_exp = sum(p.market_value_toman for p in self.portfolio.positions.values())
        
        # Risk Evaluation
        risk_res = self.risk_engine.evaluate_signal(
            signal=signal,
            current_portfolio_value_toman=current_equity,
            current_cash_toman=self.portfolio.cash_toman,
            current_crypto_exposure_toman=crypto_exp,
            active_positions=self.portfolio.positions,
            current_market_spread_pct=0.15,
        )

        if not risk_res.approved:
            return {
                "status": "VETOED_BY_RISK_ENGINE",
                "symbol": symbol,
                "reasons": risk_res.veto_reasons,
                "warnings": risk_res.risk_warnings,
            }

        # Execution via adapter
        exec_res = await self.adapter.execute_order(
            symbol=symbol,
            action=act_enum,
            target_price=target_price,
            approved_value_toman=risk_res.approved_value_toman,
        )

        return {
            "status": "APPROVED_AND_EXECUTED",
            "symbol": symbol,
            "action": action,
            "risk_evaluation": risk_res.model_dump(),
            "execution": exec_res,
            "rationale": rationale,
        }

    async def get_triangular_arbitrage_scan(self) -> List[Dict[str, Any]]:
        """Tool: Scans Wallex markets for triangular arbitrage discrepancies against USDT."""
        from src.strategy.triangular_arbitrage import TriangularArbitrageStrategy
        strat = TriangularArbitrageStrategy()
        try:
            markets_resp = await self.client.get_markets()
            symbols_data = markets_resp.get("result", {}).get("symbols", {})
            discrepancies = strat.scan_all_supported(symbols_data)
            return [d.model_dump() for d in discrepancies]
        except Exception as exc:
            return []

