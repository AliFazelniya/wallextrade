"""Decision Logger & Audit Trail.

Records every trading decision, regime classification, risk check, and fill in
an append-only, machine-readable JSONL audit trail.
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class DecisionLogger:
  """Append-only structured JSONL logger for auditing algorithmic decisions."""

  def __init__(self, log_path: str = "logs/trading_decisions.jsonl"):
    self.log_path = log_path
    os.makedirs(os.path.dirname(self.log_path), exist_ok=True)

  def log_decision(
      self,
      timestamp: str,
      symbol: str,
      event_type: str,
      market_observations: Dict[str, Any],
      regime_classification: Optional[Dict[str, Any]],
      proposed_signal: Optional[Dict[str, Any]],
      risk_evaluation: Optional[Dict[str, Any]],
      execution_result: Optional[Dict[str, Any]],
      portfolio_summary: Optional[Dict[str, Any]],
      notes: str = "",
  ) -> None:
    """Appends an immutable audit record to the JSONL log file."""
    record = {
        "timestamp": timestamp,
        "symbol": symbol,
        "event_type": event_type,
        "market_observations": market_observations,
        "regime_classification": regime_classification,
        "proposed_signal": proposed_signal,
        "risk_evaluation": risk_evaluation,
        "execution_result": execution_result,
        "portfolio_summary": portfolio_summary,
        "notes": notes,
    }

    try:
      with open(self.log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
    except Exception as exc:
      logger.error("Failed to write to decision log %s: %s", self.log_path, exc)
