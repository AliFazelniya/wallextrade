"""Live-Market Shadow Testing Session for Wallex Agentic AI Competition (Phase 23).

Connects to live Wallex REST endpoints in read-only mode to evaluate:
- Live market data fetching (BTCTMN, ETHTMN, SOLTMN)
- Cross-sectional momentum scoring
- AI Regime Agent classification
- Pre-trade risk approval
- Simulated order execution in SHADOW mode (zero exchange orders)
"""

from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path
import sys

REPO_ROOT = Path("/root/starcoach-hack/wallex")
sys.path.insert(0, str(REPO_ROOT))

from src.execution.shadow_runner import ShadowExecutionRunner

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("Phase23ShadowSession")


async def main():
    print("=" * 80)
    print("PHASE 23: LIVE-MARKET SHADOW EXECUTION TEST")
    print("Venue: Wallex Exchange (Live Read-Only REST Endpoints)")
    print("Trading Mode: SHADOW | Live Execution: FALSE (Protected)")
    print("=" * 80)

    runner = ShadowExecutionRunner()
    
    # Run 3 live shadow cycles
    results = []
    for cycle_num in range(1, 4):
        print(f"\n--- Running Live Shadow Cycle #{cycle_num} ---")
        res = await runner.run_live_shadow_cycle()
        results.append(res)
        print(f"Snapshot Symbols: {res['snapshot_symbols']}")
        for sym, snap in res["market_snapshot"].items():
            print(f"  {sym:<8} | Price: {snap['last_price']:>16,.1f} TMN | Spread: {snap['spread_pct']:>5.3f}%")
        
        ranked = res.get("ranked_candidates", [])
        if ranked:
            print("  Top Ranked Candidate:")
            for c in ranked:
                print(f"    Symbol: {c['symbol']} | Score: {c['score']:.2f} | Regime: {c['regime']} (Conf: {c['confidence']:.2f})")
        else:
            print("  Technical / AI Filter Status: No candidate exceeded eligibility threshold (All Cash / Safe)")

        print(f"  Signals Generated: {len(res['signals'])}")
        print(f"  Risk Verdicts: {len(res['risk_verdicts'])}")
        print(f"  Simulated Fills: {len(res['executions'])}")
        if cycle_num < 3:
            await asyncio.sleep(2.0)

    # Save session summary to JSON
    log_file = runner.log_dir / "shadow_session_phase23.json"
    with open(log_file, "w") as f:
        json.dump(runner.shadow_events, f, indent=2)
    print(f"\nShadow session events successfully logged to: {log_file}")
    print(f"Total Shadow Events Recorded: {len(runner.shadow_events)}")
    print(f"Portfolio Total Equity: {runner.portfolio.get_total_equity():,.0f} TMN")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
