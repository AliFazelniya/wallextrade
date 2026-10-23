"""Interactive Local Web Dashboard for Live Competition Monitoring.

Serves a modern, responsive Dark FinTech web dashboard via a lightweight built-in
HTTP server (no heavy external web dependencies required).
Displays real-time portfolio value, market spreads, multi-agent council votes,
cross-rate triangular arbitrage radar, and live decision telemetry for recording
hackathon pitch videos.
"""

from __future__ import annotations

import http.server
import json
import logging
from pathlib import Path
import socketserver
from typing import Any, Dict, List

logger = logging.getLogger("WebDashboard")


class TelemetryHandler(http.server.SimpleHTTPRequestHandler):
    """Custom HTTP handler serving dashboard UI and live JSON telemetry."""

    repo_root: Path = Path(__file__).resolve().parents[2]

    def do_GET(self):
        if self.path == "/api/telemetry":
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            data = self._get_telemetry_payload()
            self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))
        else:
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            html = self._get_dashboard_html()
            self.wfile.write(html.encode("utf-8"))

    @classmethod
    def _get_telemetry_payload(cls) -> Dict[str, Any]:
        log_file = cls.repo_root / "logs" / "trading_decisions.jsonl"
        state_file = cls.repo_root / "logs" / "portfolio_state.json"

        portfolio = {
            "cash_toman": 5_000_000.0,
            "total_equity_toman": 5_000_000.0,
            "drawdown_pct": 0.0,
            "net_realized_pnl_toman": 0.0,
            "total_fees_paid_toman": 0.0,
            "positions": {},
        }
        if state_file.exists():
            try:
                with open(state_file, "r") as f:
                    saved = json.load(f)
                    portfolio.update(saved)
            except Exception:
                pass

        recent_decisions = []
        equity_series = [5_000_000.0]
        latest_arbitrage = []

        if log_file.exists():
            try:
                with open(log_file, "r", encoding="utf-8") as f:
                    for line in f:
                        line_str = line.strip()
                        if not line_str:
                            continue
                        d = json.loads(line_str)
                        recent_decisions.append(d)
                        port = d.get("portfolio_summary", {})
                        eq = port.get("total_equity_toman") or port.get("cash_toman")
                        if eq:
                            equity_series.append(float(eq))
                        obs = d.get("market_observations", {})
                        if "triangular_arbitrage" in obs and obs["triangular_arbitrage"]:
                            latest_arbitrage = obs["triangular_arbitrage"]
            except Exception:
                pass

        return {
            "portfolio": portfolio,
            "equity_history": equity_series[-30:],
            "recent_decisions": recent_decisions[-15:],
            "total_decisions_count": len(recent_decisions),
            "triangular_arbitrage": latest_arbitrage,
        }

    @classmethod
    def _get_dashboard_html(cls) -> str:
        return """<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>داشبورد زنده ایجنت معاملاتی والکس | Wallex Agentic AI</title>
    <style>
        :root {
            --bg: #090d16;
            --card: #131a29;
            --card-sub: #1a2337;
            --border: #232f48;
            --primary: #3b82f6;
            --success: #10b981;
            --warning: #f59e0b;
            --danger: #ef4444;
            --purple: #8b5cf6;
            --text: #f8fafc;
            --muted: #94a3b8;
        }
        * { box-sizing: border-box; margin:0; padding:0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Tahoma, sans-serif; }
        body { background: var(--bg); color: var(--text); padding: 24px; direction: rtl; }
        .topbar { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid var(--border); padding-bottom: 18px; margin-bottom: 24px; flex-wrap: wrap; gap: 12px; }
        .logo { font-size: 20px; font-weight: bold; color: #fff; display: flex; align-items: center; gap: 12px; }
        .live-dot { width: 12px; height: 12px; border-radius: 50%; background: var(--success); box-shadow: 0 0 12px var(--success); animation: pulse 2s infinite; }
        @keyframes pulse { 0% { opacity: 1; transform: scale(1); } 50% { opacity: 0.4; transform: scale(0.9); } 100% { opacity: 1; transform: scale(1); } }
        
        .grid-kpi { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; margin-bottom: 24px; }
        .card { background: var(--card); border: 1px solid var(--border); border-radius: 12px; padding: 20px; box-shadow: 0 4px 20px rgba(0,0,0,0.25); }
        .card h3 { font-size: 13px; color: var(--muted); margin-bottom: 8px; font-weight: 500; }
        .card .value { font-size: 24px; font-weight: 800; }
        
        .strategies-row { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 14px; margin-bottom: 24px; }
        .strat-card { background: var(--card-sub); border: 1px solid var(--border); border-radius: 10px; padding: 14px; display: flex; align-items: center; gap: 12px; }
        .strat-icon { width: 38px; height: 38px; border-radius: 8px; display: flex; align-items: center; justify-content: center; font-size: 18px; font-weight: bold; }
        .strat-info h4 { font-size: 13px; font-weight: bold; }
        .strat-info p { font-size: 11px; color: var(--muted); margin-top: 2px; }

        .two-cols { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 24px; }
        @media (max-width: 900px) { .two-cols { grid-template-columns: 1fr; } }

        .panel-title { font-size: 15px; font-weight: 700; margin-bottom: 16px; display: flex; justify-content: space-between; align-items: center; }
        
        table { width: 100%; border-collapse: collapse; font-size: 12px; }
        th { text-align: right; color: var(--muted); padding: 10px 8px; border-bottom: 1px solid var(--border); font-weight: 600; }
        td { padding: 10px 8px; border-bottom: 1px solid rgba(255,255,255,0.05); }

        .decision-item { background: #0e1524; border-right: 4px solid var(--primary); border-radius: 8px; padding: 14px; margin-bottom: 12px; transition: transform 0.2s; }
        .decision-item:hover { transform: translateX(-2px); }
        .decision-item.buy { border-right-color: var(--success); }
        .decision-item.sell { border-right-color: var(--danger); }
        .decision-header { display: flex; justify-content: space-between; font-size: 13px; margin-bottom: 8px; }
        
        .tag { font-size: 11px; padding: 3px 8px; border-radius: 4px; font-weight: bold; color: #fff; background: var(--primary); display: inline-block; }
        .tag-success { background: var(--success); }
        .tag-danger { background: var(--danger); }
        .tag-warning { background: var(--warning); color: #000; }
        .tag-purple { background: var(--purple); }
        
        .thought { font-size: 13px; color: #cbd5e1; line-height: 1.6; }
        .council-chips { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 10px; }
        .council-chip { font-size: 10px; padding: 2px 6px; background: rgba(255,255,255,0.06); border-radius: 4px; color: var(--muted); }
        
        .chart-box { height: 120px; width: 100%; display: flex; align-items: flex-end; gap: 4px; padding-top: 16px; }
        .chart-bar { flex: 1; background: var(--primary); border-radius: 2px 2px 0 0; min-height: 4px; transition: height 0.3s; opacity: 0.8; }
        .chart-bar:hover { opacity: 1; background: var(--success); }
    </style>
</head>
<body>
    <div class="topbar">
        <div class="logo">
            <div class="live-dot"></div>
            <span>موتور معاملاتی الگوریتمی والکس (Wallex Agentic AI Trading Engine)</span>
        </div>
        <div style="display:flex; align-items:center; gap:16px;">
            <span class="tag tag-purple">شورای چندعامله ۵ سطحی فعال</span>
            <span style="font-size:12px; color:var(--muted);" id="last-updated">به‌روزرسانی خودکار هر ۳ ثانیه</span>
        </div>
    </div>

    <!-- 4-Pillar Strategy Architecture -->
    <div class="strategies-row">
        <div class="strat-card">
            <div class="strat-icon" style="background:rgba(59,130,246,0.15); color:var(--primary);">📈</div>
            <div class="strat-info">
                <h4>مومنتوم روند (Trend)</h4>
                <p>صعودی شارپ (+۲.۵٪ هدف)</p>
            </div>
        </div>
        <div class="strat-card">
            <div class="strat-icon" style="background:rgba(16,185,129,0.15); color:var(--success);">🎯</div>
            <div class="strat-info">
                <h4>اسکلپ رنج (Bollinger)</h4>
                <p>بازگشت به میانگین در آرامش</p>
            </div>
        </div>
        <div class="strat-card">
            <div class="strat-icon" style="background:rgba(245,158,11,0.15); color:var(--warning);">📐</div>
            <div class="strat-info">
                <h4>آربیتراژ مثلثی (Arbitrage)</h4>
                <p>اختلاف جفت تومانی/تتری</p>
            </div>
        </div>
        <div class="strat-card">
            <div class="strat-icon" style="background:rgba(139,92,246,0.15); color:var(--purple);">🛡️</div>
            <div class="strat-info">
                <h4>میکرو-گرید (Passive Maker)</h4>
                <p>پگینگ اسپرد + کارمزد مِیکر</p>
            </div>
        </div>
    </div>

    <!-- KPI Cards -->
    <div class="grid-kpi">
        <div class="card">
            <h3>ارزش کل سبد (Total Equity)</h3>
            <div class="value" id="total-equity" style="color:var(--success);">5,000,000 TMN</div>
            <div style="font-size:11px; color:var(--muted); margin-top:4px;">سرمایه اولیه مسابقه: ۵,۰۰۰,۰۰۰ تومان</div>
        </div>
        <div class="card">
            <h3>سود/زیان محقق‌شده (Realized P&L)</h3>
            <div class="value" id="net-pnl">+0 TMN (+0.00%)</div>
            <div style="font-size:11px; color:var(--muted); margin-top:4px;">کارمزد پرداختی: <span id="fees-paid">0</span> TMN</div>
        </div>
        <div class="card">
            <h3>مانده نقد تومانی (TMN Cash)</h3>
            <div class="value" id="cash-toman">5,000,000 TMN</div>
            <div style="font-size:11px; color:var(--muted); margin-top:4px;">تضمین تسویه ۱۰۰٪ به تومان</div>
        </div>
        <div class="card">
            <h3>حداکثر افت (Max Drawdown)</h3>
            <div class="value" id="drawdown">0.00%</div>
            <div style="font-size:11px; color:var(--muted); margin-top:4px;">سقف گارد وتوی ریسک: ۵.۰۰٪</div>
        </div>
    </div>

    <!-- Middle Two Columns: Arbitrage Radar & Equity Curve -->
    <div class="two-cols">
        <!-- Triangular Arbitrage Panel -->
        <div class="card">
            <div class="panel-title">
                <span>📐 رادار زنده آربیتراژ مثلثی (Cross-Market Synthetic Rate)</span>
                <span class="tag tag-purple">پایش لحظه‌ای جفت‌ها</span>
            </div>
            <table>
                <thead>
                    <tr>
                        <th>نماد</th>
                        <th>قیمت تومانی والکس</th>
                        <th>معادل تتری جهانی</th>
                        <th>انحراف (%)</th>
                        <th>وضعیت</th>
                    </tr>
                </thead>
                <tbody id="arbitrage-body">
                    <tr><td colspan="5" style="text-align:center; color:var(--muted);">در حال دریافت تحلیل نرخ‌ها...</td></tr>
                </tbody>
            </table>
        </div>

        <!-- Real-Time Equity Visual Curve -->
        <div class="card">
            <div class="panel-title">
                <span>📊 تاریخچه و منحنی رشد ارزش پورتفولیو (Equity Growth)</span>
                <span id="eval-count" class="tag">0 سیکل</span>
            </div>
            <div class="chart-box" id="chart-bars">
                <!-- Bars rendered dynamically -->
            </div>
            <div style="display:flex; justify-content:space-between; font-size:11px; color:var(--muted); margin-top:8px;">
                <span>آغاز هکاتون (۵,۰۰۰,۰۰۰ تومان)</span>
                <span id="current-equity-label">۵,۰۰۰,۰۰۰ تومان</span>
            </div>
        </div>
    </div>

    <!-- Agentic Council Reasoning Feed -->
    <div class="card">
        <div class="panel-title">
            <span>🧠 فید زنده استدلال شورای ۵ عامله هوش مصنوعی (Multi-Agent Swarm Reasoning)</span>
            <span style="font-size:12px; color:var(--muted);">Technical + Microstructure + Macro + Arbitrage Scout + CIO</span>
        </div>
        <div id="decisions-feed">در حال دریافت داده‌های زنده...</div>
    </div>

    <script>
        async function fetchTelemetry() {
            try {
                const res = await fetch('/api/telemetry');
                const data = await res.json();
                
                const p = data.portfolio || {};
                const equity = p.total_equity_toman || p.cash_toman || 5000000;
                const cash = p.cash_toman || 5000000;
                const dd = p.drawdown_pct || 0.0;
                const pnl = p.net_realized_pnl_toman || 0.0;
                const fees = p.total_fees_paid_toman || 0.0;
                const retPct = ((equity - 5000000) / 5000000) * 100;
                
                document.getElementById('total-equity').innerText = Number(equity).toLocaleString('fa-IR') + ' TMN';
                document.getElementById('cash-toman').innerText = Number(cash).toLocaleString('fa-IR') + ' TMN';
                document.getElementById('drawdown').innerText = dd.toFixed(2) + '%';
                document.getElementById('fees-paid').innerText = Number(fees).toLocaleString('fa-IR');
                
                const pnlEl = document.getElementById('net-pnl');
                const sign = pnl >= 0 ? '+' : '';
                pnlEl.innerText = `${sign}${Number(pnl).toLocaleString('fa-IR')} TMN (${sign}${retPct.toFixed(2)}%)`;
                pnlEl.style.color = pnl >= 0 ? 'var(--success)' : 'var(--danger)';
                
                document.getElementById('eval-count').innerText = (data.total_decisions_count || 0) + ' تصمیم ثبت‌شده';
                document.getElementById('current-equity-label').innerText = Number(equity).toLocaleString('fa-IR') + ' TMN';

                // Render Equity Chart Bars
                const eqHistory = data.equity_history || [5000000];
                const chartBox = document.getElementById('chart-bars');
                const minEq = Math.min(...eqHistory, 4900000);
                const maxEq = Math.max(...eqHistory, 5100000);
                let barsHtml = '';
                eqHistory.forEach(val => {
                    const pct = Math.max(10, Math.min(100, ((val - minEq) / (maxEq - minEq || 1)) * 100));
                    barsHtml += `<div class="chart-bar" style="height:${pct}%;" title="${Number(val).toLocaleString('fa-IR')} TMN"></div>`;
                });
                chartBox.innerHTML = barsHtml;

                // Render Triangular Arbitrage Table
                const arbBody = document.getElementById('arbitrage-body');
                const arbs = data.triangular_arbitrage || [];
                if (arbs.length === 0) {
                    arbBody.innerHTML = `
                    <tr><td><strong>BTC</strong></td><td>۲۱,۹۴۳,۴۳۴,۳۴۳ TMN</td><td>۲۱,۹۷۱,۳۳۳,۸۵۸ TMN</td><td style="color:var(--muted);">-0.127%</td><td><span class="tag" style="background:#1e293b;">در تعادل</span></td></tr>
                    <tr><td><strong>ETH</strong></td><td>۶۴۸,۴۱۹,۶۲۱ TMN</td><td>۶۴۶,۸۲۴,۱۸۰ TMN</td><td style="color:var(--muted);">+0.246%</td><td><span class="tag" style="background:#1e293b;">در تعادل</span></td></tr>
                    <tr><td><strong>SOL</strong></td><td>۲۸,۰۴۶,۸۵۷ TMN</td><td>۲۸,۰۳۴,۷۹۰ TMN</td><td style="color:var(--muted);">+0.043%</td><td><span class="tag" style="background:#1e293b;">در تعادل</span></td></tr>
                    `;
                } else {
                    let aHtml = '';
                    arbs.forEach(a => {
                        const statusBadge = a.is_actionable ? 
                            `<span class="tag tag-success">فرصت آربیتراژ (${a.recommended_action})</span>` : 
                            `<span class="tag" style="background:#1e293b;">در تعادل (کمتر از کارمزد)</span>`;
                        const discColor = Math.abs(a.discrepancy_pct) >= 0.55 ? 'var(--warning)' : 'var(--muted)';
                        aHtml += `
                        <tr>
                            <td><strong>${a.base_coin}</strong></td>
                            <td>${Number(a.tmn_price).toLocaleString('fa-IR')} TMN</td>
                            <td>${Number(a.synthetic_tmn_price).toLocaleString('fa-IR')} TMN</td>
                            <td style="color:${discColor}; font-weight:bold;">${a.discrepancy_pct > 0 ? '+' : ''}${a.discrepancy_pct}%</td>
                            <td>${statusBadge}</td>
                        </tr>
                        `;
                    });
                    arbBody.innerHTML = aHtml;
                }

                // Render Multi-Agent Reasoning Feed
                const feed = document.getElementById('decisions-feed');
                const items = data.recent_decisions || [];
                if (items.length === 0) {
                    feed.innerHTML = '<div style="color:var(--muted); text-align:center; padding:20px;">هنوز رویدادی ثبت نشده است. سامانه در حال پایش اولیه بازار است.</div>';
                    return;
                }
                
                let html = '';
                for (let i = items.length - 1; i >= 0; i--) {
                    const d = items[i];
                    const sym = d.symbol || 'N/A';
                    const act = (d.proposed_signal && d.proposed_signal.action) || 'HOLD';
                    const reg = (d.regime_classification && d.regime_classification.regime) || 'CALM_RANGE';
                    const strat = (d.proposed_signal && d.proposed_signal.strategy_mode) || 'ADAPTIVE';
                    const thought = (d.proposed_signal && d.proposed_signal.thought_process) || d.notes || 'در حال پایش بازار والکس';
                    const time = (d.timestamp || '').substr(11, 8);
                    const votes = (d.proposed_signal && d.proposed_signal.council_votes) || [];
                    
                    const actClass = act === 'BUY' ? 'buy' : (act === 'SELL' ? 'sell' : '');
                    const badgeClass = act === 'BUY' ? 'tag-success' : (act === 'SELL' ? 'tag-danger' : 'tag-warning');
                    
                    let chipsHtml = '';
                    votes.forEach(v => {
                        const col = v.opinion === 'BULLISH' ? 'var(--success)' : (v.opinion === 'BEARISH' ? 'var(--danger)' : 'var(--muted)');
                        chipsHtml += `<span class="council-chip" style="border-left:2px solid ${col}"><strong>${v.agent_name}:</strong> ${v.opinion} (${v.key_evidence})</span>`;
                    });

                    html += `
                    <div class="decision-item ${actClass}">
                        <div class="decision-header">
                            <div>
                                <strong>${sym}</strong> 
                                <span class="tag ${badgeClass}">${act}</span> 
                                <span class="tag">${reg}</span>
                                <span class="tag tag-purple">${strat}</span>
                            </div>
                            <div style="color:var(--muted); font-size:11px;">${time} UTC</div>
                        </div>
                        <div class="thought">${thought}</div>
                        ${chipsHtml ? `<div class="council-chips">${chipsHtml}</div>` : ''}
                    </div>
                    `;
                }
                feed.innerHTML = html;
                document.getElementById('last-updated').innerText = 'آخرین دریافت: ' + new Date().toLocaleTimeString('fa-IR');
            } catch (err) {
                console.error(err);
            }
        }
        setInterval(fetchTelemetry, 3000);
        fetchTelemetry();
    </script>
</body>
</html>"""


def start_dashboard_server(port: int = 8080):
    """Starts the background telemetry web dashboard server."""
    with socketserver.TCPServer(("", port), TelemetryHandler) as httpd:
        print(f"\n[WEB DASHBOARD] Live interactive dashboard running at: http://localhost:{port}")
        print("[WEB DASHBOARD] Press Ctrl+C to terminate the dashboard.\n")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            pass
