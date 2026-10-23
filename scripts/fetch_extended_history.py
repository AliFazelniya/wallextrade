#!/usr/bin/env python3
"""Fetches and audits 90 days of continuous 15-minute market data from Wallex UDF API."""

from __future__ import annotations

import asyncio
import datetime
import hashlib
import json
import logging
import pathlib
import sys
import pandas as pd

repo_root = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(repo_root))

from src.data.client import WallexClient
from src.data.fetcher import MarketDataFetcher

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("fetch_extended_history")


async def main():
    client = WallexClient()
    fetcher = MarketDataFetcher(client)

    symbols = ["BTCTMN", "ETHTMN", "SOLTMN"]
    now_ts = int(datetime.datetime.now(datetime.timezone.utc).timestamp())
    # 90 days span (5 chunks of 18 days)
    total_days = 90
    from_ts = now_ts - (total_days * 86400)

    cache_dir = repo_root / "data" / "cache"
    cache_dir.mkdir(parents=True, exist_ok=True)

    dataset_summary = {}

    for sym in symbols:
        cache_file = cache_dir / f"{sym}_15m_90d.csv"
        if cache_file.exists():
            logger.info("Found cached 90d data for %s at %s", sym, cache_file.name)
            df = pd.read_csv(cache_file, parse_dates=["timestamp"])
            content = cache_file.read_bytes()
            sha256 = hashlib.sha256(content).hexdigest()
            dataset_summary[sym] = {
                "file": cache_file.name,
                "sha256": sha256,
                "candles_15m": len(df),
                "first_timestamp": str(df.iloc[0]["timestamp"]),
                "last_timestamp": str(df.iloc[-1]["timestamp"]),
            }
        else:
            logger.info("Fetching %d days of data for %s from Wallex UDF API...", total_days, sym)
            df, audit = await fetcher.fetch_ohlcv_dataframe(
                symbol=sym,
                resolution="15",
                from_ts=from_ts,
                to_ts=now_ts,
                auto_resample_to_true_timeframe=True,
            )
            df.to_csv(cache_file, index=False)
            content = cache_file.read_bytes()
            sha256 = hashlib.sha256(content).hexdigest()
            dataset_summary[sym] = {
                "file": cache_file.name,
                "sha256": sha256,
                "candles_15m": len(df),
                "raw_records": audit.get("raw_record_count", 0),
                "first_timestamp": str(df.iloc[0]["timestamp"]),
                "last_timestamp": str(df.iloc[-1]["timestamp"]),
                "duplicates": audit.get("duplicate_count", 0),
                "missing": audit.get("missing_count", 0),
            }
            logger.info("Successfully fetched and cached %s: %d candles (SHA256: %s...)", sym, len(df), sha256[:12])

    out_meta = repo_root / "research" / "extended_90d_dataset_metadata.json"
    with open(out_meta, "w", encoding="utf-8") as f:
        json.dump(dataset_summary, f, indent=2)
    logger.info("Dataset metadata saved to %s", out_meta)
    print(json.dumps(dataset_summary, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
