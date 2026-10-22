#!/usr/bin/env python3
"""Programmatic Market Restrictions & Set-Difference Audit Script."""

from __future__ import annotations

import json
import logging
import pathlib
import sys
import httpx

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("market_audit")


def run_market_restrictions_audit() -> dict:
    repo_root = pathlib.Path(__file__).resolve().parent.parent
    allowed_path = repo_root / "config" / "allowed_markets.json"
    restricted_path = repo_root / "config" / "market_restrictions.json"

    with open(allowed_path, "r", encoding="utf-8") as f:
        allowed_data = json.load(f)
    with open(restricted_path, "r", encoding="utf-8") as f:
        restricted_data = json.load(f)

    allowed_list = [m["symbol"].strip().upper() for m in allowed_data.get("markets", [])]
    allowed_set = set(allowed_list)

    # Collect all restricted symbols across categories
    credit_inactive = [s["symbol"].strip().upper() for s in restricted_data.get("credit_inactive_symbols", [])]
    usdt_pairs = [s["symbol"].strip().upper() for s in restricted_data.get("excluded_usdt_pairs", [])]
    low_liq = [s["symbol"].strip().upper() for s in restricted_data.get("excluded_low_liquidity", [])]
    high_spread = [s["symbol"].strip().upper() for s in restricted_data.get("excluded_high_spread", [])]
    unverified = [s["symbol"].strip().upper() for s in restricted_data.get("unverified_symbols", [])]

    all_restricted_list = credit_inactive + usdt_pairs + low_liq + high_spread + unverified
    all_restricted_set = set(all_restricted_list)

    # Fetch live exchange metadata from Wallex
    resp = httpx.get("https://api.wallex.ir/v1/markets", timeout=15.0)
    resp.raise_for_status()
    wallex_symbols = set(resp.json().get("result", {}).get("symbols", {}).keys())

    # 1. Duplicates check
    allowed_duplicates = [s for s in allowed_set if allowed_list.count(s) > 1]
    restricted_duplicates = [s for s in all_restricted_set if all_restricted_list.count(s) > 1]

    # 2. Accidental inclusion: allowed INTERSECT restricted
    intersection = allowed_set.intersection(all_restricted_set)

    # 3. Missing symbols: Symbols on Wallex not accounted for in either allowed or restricted
    all_accounted = allowed_set.union(all_restricted_set)
    missing_from_system = wallex_symbols.difference(all_accounted)

    # 4. Unknown symbols: Symbols in allowed or restricted that do not exist on Wallex API
    non_existent_symbols = all_accounted.difference(wallex_symbols)

    # 5. Malformed symbols (symbols that contain lowercase, whitespace, or invalid length)
    malformed = [s for s in all_accounted if not s.isalnum() or not s.isupper() or len(s) < 4]

    report = {
        "wallex_total_symbols_count": len(wallex_symbols),
        "allowed_symbols_count": len(allowed_set),
        "total_restricted_symbols_count": len(all_restricted_set),
        "credit_inactive_count": len(credit_inactive),
        "excluded_usdt_pairs_count": len(usdt_pairs),
        "excluded_low_liquidity_count": len(low_liq),
        "excluded_high_spread_count": len(high_spread),
        "unverified_count": len(unverified),
        "allowed_duplicates": allowed_duplicates,
        "restricted_duplicates": restricted_duplicates,
        "accidental_allowlist_inclusions": list(intersection),
        "symbols_missing_from_system": list(missing_from_system),
        "non_existent_symbols_on_exchange": list(non_existent_symbols),
        "malformed_symbols": malformed,
        "set_partition_valid": (
            len(intersection) == 0
            and len(missing_from_system) == 0
            and len(non_existent_symbols) == 0
            and len(allowed_duplicates) == 0
            and len(restricted_duplicates) == 0
            and len(malformed) == 0
        )
    }

    print("="*75)
    print("  MARKET RESTRICTIONS & SET-DIFFERENCE AUDIT")
    print("="*75)
    print(f"Total Symbols in Wallex:                {report['wallex_total_symbols_count']}")
    print(f"Verified Allowed Symbols:               {report['allowed_symbols_count']}")
    print(f"Total Restricted Symbols:               {report['total_restricted_symbols_count']}")
    print(f"  - Credit Inactive / Zero Liquidity:   {report['credit_inactive_count']}")
    print(f"  - Excluded USDT Pairs:                {report['excluded_usdt_pairs_count']}")
    print(f"  - Excluded Low Liquidity (<5B TMN):   {report['excluded_low_liquidity_count']}")
    print(f"  - Excluded High Spread (>0.35%):      {report['excluded_high_spread_count']}")
    print(f"Duplicates in Allowlist:                {len(allowed_duplicates)}")
    print(f"Duplicates in Restricted List:          {len(restricted_duplicates)}")
    print(f"Accidental Allowlist Inclusions:        {len(intersection)} {list(intersection)}")
    print(f"Missing Symbols from System:            {len(missing_from_system)} {list(missing_from_system)}")
    print(f"Non-existent Symbols in System:         {len(non_existent_symbols)} {list(non_existent_symbols)}")
    print(f"Malformed Symbols:                      {len(malformed)} {malformed}")
    print(f"Mathematical Partition Integrity:       {'VERIFIED (Disjoint & Complete)' if report['set_partition_valid'] else 'FAILED'}")
    print("="*75)

    return report


if __name__ == "__main__":
    run_market_restrictions_audit()
