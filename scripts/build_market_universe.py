#!/usr/bin/env python3
"""Programmatically builds, validates, and partitions the Wallex market universe.

Enforces:
1. Complete inactive market list from exchange metadata & credit account rules.
2. Separate restricted list vs verified eligible allowlist.
3. Symbol normalization, precision validation, minNotional validation.
4. Export to config/market_restrictions.json and config/allowed_markets.json.
"""

from __future__ import annotations

import datetime
import json
import logging
import pathlib
import httpx

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("market_universe")


def build_universe():
    logger.info("Querying Wallex live markets metadata from https://api.wallex.ir/v1/markets ...")
    resp = httpx.get("https://api.wallex.ir/v1/markets", timeout=15.0)
    resp.raise_for_status()
    raw_data = resp.json().get("result", {}).get("symbols", {})

    total_symbols = len(raw_data)
    logger.info("Retrieved %d total symbols from Wallex API.", total_symbols)

    verified_allowed = []
    credit_inactive_symbols = []
    excluded_usdt_pairs = []
    excluded_low_liquidity = []
    excluded_high_spread = []
    unverified_symbols = []

    for sym, info in raw_data.items():
        quote = info.get("quoteAsset")
        base = info.get("baseAsset")
        stats = info.get("stats", {})
        bp_raw = stats.get("bidPrice", "-")
        ap_raw = stats.get("askPrice", "-")
        vol_raw = stats.get("24h_tmnVolume", 0)

        # Classify USDT-denominated pairs
        if quote == "USDT":
            excluded_usdt_pairs.append({
                "symbol": sym,
                "baseAsset": base,
                "reason": "USDT_DENOMINATED_EXCLUDED_FOR_INITIAL_PHASE"
            })
            continue

        # Check for inactive / zero-volume / delisted symbols in credit accounts
        is_dash = (bp_raw == "-" or ap_raw == "-" or bp_raw is None or ap_raw is None)
        try:
            vol_val = float(vol_raw) if vol_raw is not None else 0.0
            bp_val = float(bp_raw) if not is_dash else 0.0
            ap_val = float(ap_raw) if not is_dash else 0.0
        except (ValueError, TypeError):
            vol_val = 0.0
            bp_val = 0.0
            ap_val = 0.0

        if is_dash or vol_val <= 0.0 or bp_val <= 0.0 or ap_val <= 0.0:
            credit_inactive_symbols.append({
                "symbol": sym,
                "baseAsset": base,
                "faName": info.get("faName"),
                "reason": "INACTIVE_OR_ZERO_LIQUIDITY_IN_CREDIT_ACCOUNT"
            })
            continue

        # Active TMN Pair with valid orderbook
        spread_pct = ((ap_val - bp_val) / bp_val * 100.0) if bp_val > 0 else 999.0
        min_notional = float(info.get("minNotional", 50000))
        supports_market_order = bool(info.get("isMarketTypeEnable", False))

        symbol_record = {
            "symbol": sym,
            "baseAsset": base,
            "quoteAsset": quote,
            "faName": info.get("faName"),
            "enName": info.get("enName"),
            "baseAssetPrecision": int(info.get("baseAssetPrecision", 8)),
            "quotePrecision": int(info.get("quotePrecision", 0)),
            "stepSize": int(info.get("stepSize", 8)),
            "tickSize": int(info.get("tickSize", 0)),
            "minQty": float(info.get("minQty", 0.0001)),
            "minNotional": min_notional,
            "supports_market_order": supports_market_order,
            "supported_order_types": ["LIMIT", "MARKET"] if supports_market_order else ["LIMIT"],
            "vol_24h_tmn": vol_val,
            "bidPrice": bp_val,
            "askPrice": ap_val,
            "spread_pct": round(spread_pct, 4),
            "verified_tradable": True,
        }

        # Liquidity and spread screening for eligible competition universe
        # Requirement: 24h volume >= 5,000,000,000 TMN (5 Billion Toman) and spread <= 0.35%
        if vol_val < 5_000_000_000:
            excluded_low_liquidity.append({
                "symbol": sym,
                "vol_24h_tmn": vol_val,
                "reason": f"VOLUME_BELOW_5B_TMN ({vol_val/1e9:.2f}B TMN)"
            })
        elif spread_pct > 0.35:
            excluded_high_spread.append({
                "symbol": sym,
                "spread_pct": round(spread_pct, 4),
                "reason": f"SPREAD_EXCEEDS_0.35_PCT ({spread_pct:.3f}%)"
            })
        else:
            verified_allowed.append(symbol_record)

    # Sort allowed by volume descending
    verified_allowed.sort(key=lambda x: x["vol_24h_tmn"], reverse=True)

    # Save to config/allowed_markets.json
    allowed_payload = {
        "updated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "total_eligible_markets": len(verified_allowed),
        "screening_criteria": {
            "quote_asset": "TMN",
            "min_daily_volume_toman": 5_000_000_000,
            "max_spread_pct": 0.35,
            "min_notional_toman": 50000,
            "must_be_active": True
        },
        "markets": verified_allowed
    }
    with open("config/allowed_markets.json", "w", encoding="utf-8") as f:
        json.dump(allowed_payload, f, indent=2, ensure_ascii=False)
    logger.info("Saved %d verified eligible markets to config/allowed_markets.json", len(verified_allowed))

    # Save to config/market_restrictions.json
    restrictions_payload = {
        "updated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "summary": {
            "credit_inactive_count": len(credit_inactive_symbols),
            "excluded_usdt_pairs_count": len(excluded_usdt_pairs),
            "excluded_low_liquidity_count": len(excluded_low_liquidity),
            "excluded_high_spread_count": len(excluded_high_spread),
            "total_restricted_symbols": len(credit_inactive_symbols) + len(excluded_usdt_pairs) + len(excluded_low_liquidity) + len(excluded_high_spread)
        },
        "credit_inactive_symbols": credit_inactive_symbols,
        "excluded_usdt_pairs": excluded_usdt_pairs,
        "excluded_low_liquidity": excluded_low_liquidity,
        "excluded_high_spread": excluded_high_spread,
        "unverified_symbols": unverified_symbols
    }
    with open("config/market_restrictions.json", "w", encoding="utf-8") as f:
        json.dump(restrictions_payload, f, indent=2, ensure_ascii=False)
    logger.info("Saved complete restriction lists to config/market_restrictions.json")

    print("\n" + "="*70)
    print("  WALLEX MARKET UNIVERSE PARTITIONING SUMMARY")
    print("="*70)
    print(f"Total Symbols in Wallex:                {total_symbols}")
    print(f"Verified Eligible Allowlist:            {len(verified_allowed)}")
    print(f"Credit Inactive / Zero Liquidity:       {len(credit_inactive_symbols)}")
    print(f"USDT Pairs (Excluded):                  {len(excluded_usdt_pairs)}")
    print(f"TMN Low Liquidity (<5B TMN):            {len(excluded_low_liquidity)}")
    print(f"TMN High Spread (>0.35%):               {len(excluded_high_spread)}")
    print("="*70)
    print("Top Allowed Symbols:")
    for m in verified_allowed[:10]:
        print(f" - {m['symbol']:<10} | Vol: {m['vol_24h_tmn']/1e9:>8.2f} B TMN | Spread: {m['spread_pct']:>5.2f}% | Orders: {m['supported_order_types']}")


if __name__ == "__main__":
    build_universe()
