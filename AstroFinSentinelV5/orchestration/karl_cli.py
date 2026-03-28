"""orchestration/karl_cli.py — ATOM-015: KARL CLI + Dashboard + Persistence"""
import asyncio
import json
import sys
import os
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


def print_banner():
    print("=" * 70)
    print("  ASTROFIN SENTINEL v5 — KARL MODE (ATOM-015)")
    print("=" * 70)


def print_decision_summary(record: dict, amre: dict, synth: dict):
    print()
    print("┌" + "─" * 68 + "┐")
    print("│" + " " * 20 + "KARL DECISION SUMMARY" + " " * 27 + "│")
    print("├" + "─" * 68 + "┤")
    
    action = record.get("final_action", synth.get("signal", "NEUTRAL"))
    confidence = record.get("confidence_final", synth.get("confidence", 50))
    regime = record.get("regime", "NORMAL")
    price = record.get("price", 0)
    decision_id = record.get("decision_id", "N/A")
    
    icon = {"LONG": "🟢", "SHORT": "🟣", "NEUTRAL": "⚪", "AVOID": "⛔"}.get(action, "⚪")
    regime_icon = {"LOW": "🟢", "NORMAL": "🟡", "HIGH": "🟠", "EXTREME": "🟣"}.get(regime, "⚪")
    
    print(f"│  {icon} {action:8}  CONF={confidence:3}  REGIME={regime_icon}{regime:7}  ID={decision_id}")
    print(f"│  Price: {price:,.2f}  |  Position: {record.get('position_pct', 0)*100:.1f}%")
    
    unc = amre.get("uncertainty", {})
    print(f"│  Uncertainty: aleatoric={unc.get('aleatoric', 0):.3f}  epistemic={unc.get('epistemic', 0):.3f}  total={unc.get('total', 0):.3f}")
    
    q_star = record.get("q_star", 0)
    reward = amre.get("reward_estimate", 0)
    print(f"│  Q*={q_star:.4f}  reward={reward:.4f}")
    
    grounded = amre.get("grounding_passed", True)
    print(f"│  Grounding: {'PASSED' if grounded else 'FAILED'}")
    
    print("└" + "─" * 68 + "┤")


def print_signal_breakdown(synth: dict):
    breakdown = synth.get("metadata", {}).get("breakdown", "")
    if breakdown:
        print()
        print("┌" + "─" * 68 + "┐")
        print("│" + " " * 20 + "AGENT BREAKDOWN" + " " * 32 + "│")
        print("├" + "─" * 68 + "┤")
        for line in breakdown.split("\n"):
            if line.strip():
                print(f"│  {line[:66]}")
        print("└" + "─" * 68 + "┤")


def print_karl_diagnostics(diagnostics: dict):
    print()
    print("┌" + "─" * 68 + "┐")
    print("│" + " " * 20 + "KARL DIAGNOSTICS" + " " * 30 + "│")
    print("├" + "─" * 68 + "┤")
    
    oap = diagnostics.get("oap_kpi", {})
    print(f"│  OAP: TTC_depth={oap.get('current_ttc_depth', '?')}  OOS_fail={oap.get('oos_fail_rate', 0):.3f}  entropy={oap.get('entropy_avg', 0):.3f}")
    
    audit = diagnostics.get("audit_summary", {})
    print(f"│  Audit: total={audit.get('total', 0)}  avg_conf={audit.get('avg_confidence_final', 0):.1f}")
    
    print("└" + "─" * 68 + "┤")


def save_decision_to_jsonl(record: dict, filepath: str = "data/karl_decisions.jsonl"):
    Path(filepath).parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, "a") as f:
        f.write(json.dumps(record, default=str) + "\n")


def generate_html_report(result: dict, output_path: str = "data/karl_report.html"):
    synth = result.get("final_recommendation", {})
    record = result.get("decision_record", {})
    amre = result.get("amre_output", {})
    
    action = synth.get("signal", "NEUTRAL")
    confidence = synth.get("confidence", 50)
    price = synth.get("metadata", {}).get("current_price", 0)
    regime = synth.get("metadata", {}).get("volatility_risk", {}).get("regime", "NORMAL")
    breakdown = synth.get("metadata", {}).get("breakdown", "")
    
    regime_color = {"LOW": "#22c55e", "NORMAL": "#eab308", "HIGH": "#f97316", "EXTREME": "#ef4444"}.get(regime, "#6b7280")
    action_color = {"LONG": "#22c55e", "SHORT": "#ef4444", "NEUTRAL": "#6b7280", "AVOID": "#dc2626"}.get(action, "#6b7280")
    
    breakdown_html = "".join(f"<tr><td colspan='4' style='font-family:monospace;font-size:11px'>{line}</td></tr>" for line in breakdown.split("\n") if line.strip())
    
    html = f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><title>ATOM-015 KARL Report</title>
<style>
  body {{ font-family: -apple-system, sans-serif; background: #0f172a; color: #e2e8f0; padding: 20px; }}
  .container {{ max-width: 900px; margin: 0 auto; }}
  h1 {{ color: #f8fafc; border-bottom: 2px solid #334155; padding-bottom: 10px; }}
  .signal-box {{ background: {action_color}22; border-left: 6px solid {action_color}; padding: 20px; margin: 20px 0; border-radius: 8px; }}
  .signal-action {{ font-size: 32px; font-weight: bold; color: {action_color}; }}
  .metric {{ font-size: 24px; font-weight: bold; color: #38bdf8; }}
  .metric-label {{ font-size: 12px; color: #94a3b8; }}
  .grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin: 20px 0; }}
  .card {{ background: #1e293b; border-radius: 8px; padding: 16px; }}
  table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
  th {{ background: #1e293b; text-align: left; padding: 8px; }}
  td {{ padding: 8px; border-bottom: 1px solid #334155; }}
</style>
</head>
<body>
<div class="container">
  <h1>AstroFin Sentinel v5 — KARL Report</h1>
  <div class="timestamp">Generated: {datetime.now().isoformat()}</div>
  <div class="signal-box">
    <div class="signal-action">{action}</div>
    <div>Confidence: {confidence}/100 | Price: {price:,.2f} | Symbol: {result.get('symbol', 'BTC')}</div>
    <div>Regime: {regime}</div>
  </div>
  <div class="grid">
    <div class="card"><div class="metric-label">Decision ID</div><div class="metric">{record.get('decision_id', 'N/A')}</div></div>
    <div class="card"><div class="metric-label">Q*</div><div class="metric">{record.get('q_star', 0):.4f}</div></div>
    <div class="card"><div class="metric-label">Uncertainty</div><div class="metric">{amre.get('uncertainty', {}).get('total', 0):.3f}</div></div>
  </div>
  <h2>Agent Breakdown</h2>
  <table><tr><th colspan="4">Signals</th></tr>{breakdown_html}</table>
  <h2>Entry Levels</h2>
  <table>
    <tr><td>Entry Zone</td><td>{synth.get('metadata', {}).get('entry_zone', 'N/A')}</td></tr>
    <tr><td>Stop Loss</td><td>{synth.get('metadata', {}).get('stop_loss', 'N/A')}</td></tr>
    <tr><td>Targets</td><td>{synth.get('metadata', {}).get('targets', 'N/A')}</td></tr>
    <tr><td>Position Size</td><td>{(synth.get('metadata', {}).get('position_size', 0)*100):.2f}%</td></tr>
  </table>
  <h2>Reasoning</h2><p>{synth.get('reasoning', 'N/A')}</p>
</div>
</body>
</html>"""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        f.write(html)
    return output_path


async def run_continuous_backtest(symbol: str = "BTCUSDT", max_iterations: int = 6):
    from orchestration.sentinel_v5 import run_sentinel_v5_karl
    import requests
    
    print("=" * 70)
    print(f"CONTINUOUS BACKTEST — {symbol} — max {max_iterations} iterations")
    print("=" * 70)
    results = []
    
    for i in range(max_iterations):
        print(f"\n[Iteration {i+1}/{max_iterations}] ", end="", flush=True)
        try:
            resp = requests.get(f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}", timeout=5)
            price = float(resp.json()["price"])
        except:
            price = 50000.0
        
        try:
            result = await run_sentinel_v5_karl(
                user_query=f"Analyze {symbol}",
                symbol=symbol, timeframe="SWING", current_price=price,
                include_technical=True, include_astro=True, include_electional=False,
            )
            synth = result.get("final_recommendation", {})
            record = result.get("decision_record", {})
            amre = result.get("amre_output", {})
            action = synth.get("signal", "?")
            confidence = synth.get("confidence", 0)
            print(f"→ {action} (conf={confidence}) | price={price:,.0f}")
            if record:
                print(f"   decision_id={record.get('decision_id', 'N/A')}  uncertainty={amre.get('uncertainty', {}).get('total', 0):.3f}")
            results.append(result)
            if record:
                save_decision_to_jsonl(record)
        except Exception as e:
            print(f"ERROR: {e}")
        
        if i < max_iterations - 1:
            await asyncio.sleep(1)
    
    print("\n" + "=" * 70)
    print("CONTINUOUS BACKTEST COMPLETE")
    print("=" * 70)
    if results:
        actions = [r.get("final_recommendation", {}).get("signal", "?") for r in results]
        print(f"Total: {len(results)} | LONG={actions.count('LONG')} SHORT={actions.count('SHORT')} NEUTRAL={actions.count('NEUTRAL')}")
        print(f"Records saved: data/karl_decisions.jsonl")
    return results


async def main():
    print_banner()
    
    if len(sys.argv) < 2:
        print("\nUsage:")
        print("  python -m orchestration.karl_cli <query> [symbol] [timeframe]   # Single KARL run")
        print("  python -m orchestration.karl_cli --continuous [symbol]            # Continuous backtest")
        print("  python -m orchestration.karl_cli --diag                          # Diagnostics")
        print("  python -m orchestration.karl_cli --report                        # HTML report")
        sys.exit(1)
    
    cmd = sys.argv[1]
    
    if cmd == "--diag":
        from orchestration.sentinel_v5 import karl_diagnostics
        await karl_diagnostics()
    elif cmd == "--continuous":
        symbol = sys.argv[2] if len(sys.argv) > 2 else "BTCUSDT"
        await run_continuous_backtest(symbol=symbol, max_iterations=6)
    elif cmd == "--report":
        print("Use: python -m orchestration.karl_cli <query> [symbol] [timeframe] --html")
        print("HTML report is auto-generated after each --karl run")
    else:
        from orchestration.sentinel_v5 import run_sentinel_v5_karl
        query = sys.argv[1]
        symbol = sys.argv[2] if len(sys.argv) > 2 else "BTCUSDT"
        timeframe = sys.argv[3] if len(sys.argv) > 3 else "SWING"
        
        result = await run_sentinel_v5_karl(query, symbol, timeframe)
        
        synth = result.get("final_recommendation", {})
        record = result.get("decision_record", {})
        amre = result.get("amre_output", {})
        diagnostics = result.get("karl_diagnostics", {})
        
        print_decision_summary(record or {}, amre or {}, synth or {})
        print_signal_breakdown(synth or {})
        print_karl_diagnostics(diagnostics or {})
        
        if record:
            save_decision_to_jsonl(record)
            report_path = generate_html_report(result)
            print(f"\nHTML report: {report_path}")
            print(f"JSONL record: data/karl_decisions.jsonl")


if __name__ == "__main__":
    asyncio.run(main())
