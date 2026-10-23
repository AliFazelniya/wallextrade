"""Wallex Live System & AI Agent Terminal Dashboard.

Renders an interactive, visually stunning ASCII/ANSI live terminal view
of portfolio balances, market spreads, AI regime classifications,
risk gate checks, and audit trails for competition monitoring and demo pitches.
"""

from __future__ import annotations

import datetime
import os
import time
from typing import Any, Dict, List, Optional


class LiveTerminalDashboard:
    """Renders formatted operational telemetry to stdout."""

    @staticmethod
    def clear_screen():
        os.system("clear" if os.name == "posix" else "cls")

    @classmethod
    def render(
        cls,
        mode: str,
        portfolio_status: Dict[str, Any],
        markets_overview: Dict[str, Any],
        recent_decisions: List[Dict[str, Any]],
        cycle: int,
        max_cycles: Optional[int] = None,
    ):
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cash = portfolio_status.get("cash_toman", 5_000_000.0)
        crypto = portfolio_status.get("crypto_value_toman", 0.0)
        equity = portfolio_status.get("total_equity_toman", 5_000_000.0)
        pnl = portfolio_status.get("net_realized_pnl_toman", 0.0)
        fees = portfolio_status.get("total_fees_paid_toman", 0.0)
        drawdown = portfolio_status.get("drawdown_pct", 0.0)
        open_pos = portfolio_status.get("open_positions", {})
        ret_pct = ((equity - 5_000_000.0) / 5_000_000.0) * 100.0

        pnl_color = "\033[92m" if pnl >= 0 else "\033[91m"
        ret_color = "\033[92m" if ret_pct >= 0 else "\033[91m"
        reset = "\033[0m"
        bold = "\033[1m"
        cyan = "\033[96m"
        yellow = "\033[93m"

        cycle_str = f"Cycle #{cycle}" + (f" / {max_cycles}" if max_cycles else "")
        mode_badge = f"\033[42m\033[30m LIVE \033[0m" if mode.upper() == "LIVE" else f"\033[44m\033[37m SHADOW \033[0m"

        print(f"\n{bold}{cyan}╔══════════════════════════════════════════════════════════════════════════════════════════════╗{reset}")
        print(f"{bold}{cyan}║   WALLEX AGENTIC AI ALGORITHMIC TRADING SYSTEM  |  {mode_badge}  |  {cycle_str:<12} {now_str}   ║{reset}")
        print(f"{bold}{cyan}╚══════════════════════════════════════════════════════════════════════════════════════════════╝{reset}")

        # Portfolio Summary Box
        print(f"\n{bold}┌── [۱. وضعیت پورتفولیو و حسابرسی سرمایه (Portfolio & Capital)] ─────────────────────────────┐{reset}")
        print(f"│  سرمایه اولیه:        5,000,000 TMN      │  سود خالص محقق‌شده: {pnl_color}{pnl:+12,.0f} TMN{reset} ({ret_color}{ret_pct:+.2f}%{reset}) │")
        print(f"│  مانده نقد (تومان):  {cash:>13,.0f} TMN      │  کارمزد پرداخت‌شده:   {fees:>10,.0f} TMN        │")
        print(f"│  ارزش ریالی کریپتو:  {crypto:>13,.0f} TMN      │  حداکثر افت (Drawdown): {drawdown:>9.2f}%        │")
        print(f"│  ارزش کل دارایی:     {bold}{equity:>13,.0f} TMN{reset}      │  پوزیشن‌های فعال:       {len(open_pos):>10}        │")
        print(f"{bold}└──────────────────────────────────────────────────────────────────────────────────────────────┘{reset}")

        # Active Positions Details
        if open_pos:
            print(f"\n{bold}┌── [۲. موقعیت‌های باز رمزارزی (Open Positions)] ───────────────────────────────────────────┐{reset}")
            print(f"│  {'نماد':<10} │ {'حجم':<12} │ {'قیمت ورود (TMN)':<18} │ {'ارزش فعلی (TMN)':<18} │ {'سود/زیان':<12} │")
            print(f"├─────────────┼──────────────┼────────────────────┼────────────────────┼──────────────┤")
            for sym, pos in open_pos.items():
                upnl = pos.get("unrealized_pnl_toman", 0.0)
                upnl_p = pos.get("unrealized_pnl_pct", 0.0)
                c = "\033[92m" if upnl >= 0 else "\033[91m"
                print(f"│  {sym:<10} │ {pos['quantity']:<12.6f} │ {pos['avg_entry_price']:<18,.0f} │ {pos['current_price']:<18,.0f} │ {c}{upnl_p:+6.2f}%{reset}      │")
            print(f"{bold}└──────────────────────────────────────────────────────────────────────────────────────────────┘{reset}")

        # Live Market Overview
        print(f"\n{bold}┌── [۳. پایش زنده بازار و ریزساختار والکس (Live Market Universe)] ───────────────────────────┐{reset}")
        print(f"│  {'نماد':<10} │ {'آخرین قیمت (تومان)':<20} │ {'بهترین خرید (Bid)':<18} │ {'بهترین فروش (Ask)':<18} │ {'اسپرد':<8} │")
        print(f"├─────────────┼──────────────────────┼────────────────────┼────────────────────┼──────────┤")
        for sym, d in markets_overview.items():
            if not isinstance(d, dict) or "last_price_toman" not in d:
                continue
            spr = d.get("spread_pct", 0.0)
            spr_color = "\033[92m" if spr <= 0.20 else ("\033[93m" if spr <= 0.35 else "\033[91m")
            print(f"│  {sym:<10} │ {d['last_price_toman']:>18,.0f} TMN │ {d['best_bid_toman']:>16,.0f} TMN │ {d['best_ask_toman']:>16,.0f} TMN │ {spr_color}{spr:>6.3f}%{reset} │")
        print(f"{bold}└──────────────────────────────────────────────────────────────────────────────────────────────┘{reset}")

        # Agentic AI Decisions & Reasoning Rationale
        print(f"\n{bold}┌── [۴. استدلال و تصمیمات ایجنت هوش مصنوعی (Agentic AI Reasoning Trail)] ──────────────────┐{reset}")
        if not recent_decisions:
            print(f"│  در حال تحلیل و تجمیع داده‌های بازار و اردر بوک...                                          │")
        else:
            for dec in recent_decisions[-3:]:
                act = dec.get("recommended_action", "HOLD")
                act_badge = f"\033[42m\033[30m BUY \033[0m" if act == "BUY" else (f"\033[41m\033[37m SELL \033[0m" if act == "SELL" else f"\033[43m\033[30m HOLD \033[0m")
                regime = dec.get("regime", "N/A")
                conf = dec.get("confidence", 0.0) * 100.0
                rat = dec.get("rationale", "")
                sym = dec.get("symbol", "")
                print(f"│  • {bold}[{sym}]{reset} {act_badge} | رژیم: {cyan}{regime}{reset} (اطمینان: {conf:.0f}%)")
                print(f"│    استدلال: {yellow}{rat}{reset}")
        print(f"{bold}└──────────────────────────────────────────────────────────────────────────────────────────────┘{reset}\n")
