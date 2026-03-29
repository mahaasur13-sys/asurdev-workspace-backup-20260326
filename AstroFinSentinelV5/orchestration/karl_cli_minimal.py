"""orchestration/karl_cli.py — ATOM-017: Industrial KARL CLI + Rich UI + Real Agents"""
import asyncio, json, sys, os
from datetime import datetime
from pathlib import Path
try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.text import Text
    RICH = True
except ImportError:
    RICH = False
sys.path.insert(0, str(Path(__file__).parent.parent))
console = Console() if RICH else None
def cprint(msg, style=None):
    if RICH: console.print(msg, style=style or "")
    else: print(msg)

def print_banner():
    W = 70
    if RICH:
        t = Text()
        t.append("  " + "="*W + "\n", style="cyan")
        t.append("  " + " ASTROFIN SENTINEL v5  ·  KARL MODE  ·  ATOM-017 ".center(W) + "\n", style="bold cyan")
        t.append("  " + "="*W, style="cyan")
        cprint(t)
    else:
        print("="*W)
        print("  ASTROFIN SENTINEL v5  ·  KARL MODE  ·  ATOM-017".center(W))
        print("="*W)

def print_decision_rich(record, amre, synth):
    if not RICH: return _fallback_decision(record, amre, synth)
    action = record.get("final_action", synth.get("signal", "NEUTRAL"))
    confidence = record.get("confidence_final", synth.get("confidence", 50))
    regime = record.get("regime", "NORMAL")
    price = record.get("price", 0)
    q_star = record.get("q_star", 0)
    reward = amre.get("reward_estimate", 0)
    unc = amre.get("uncertainty", {})
    grounded = amre.get("grounding_passed", True)
    ac = {"LONG":"green","SHORT":"red","NEUTRAL":"yellow","AVOID":"bold red"}.get(action,"white")
    rc = {"LOW":"green","NORMAL":"yellow","HIGH":"bold yellow","EXTREME":"bold red"}.get(regime,"white")
    ai = {"LONG":"[green]📈[/green]","SHORT":"[red]📉[/red]","NEUTRAL":"[yellow]⏸[/yellow]","AVOID":"[bold red]🚫[/bold red]"}.get(action,"❓")
    main = Text()
    main.append(f"  {ai} ACTION  ", style=f"bold {ac}")
    main.append(f"  CONF={confidence}  ", style="bold white")
    main.append(f"  REGIME={regime}  ", style=rc)
    main.append(f"  ID={record.get('decision_id','N/A')}", style="dim")
    t = Table(show_header=False, box=None, pad_edge=False, pad_row=0)
    t.add_column(style="dim",width=20); t.add_column(style="white",width=20)
    t.add_column(style="dim",width=20); t.add_column(style="white",width=20)
    t.add_row("Price", f"${price:,.2f}", "Position", f"{record.get('position_pct',0)*100:.1f}%")
    t.add_row("Q*", f"{q_star:.4f}", "Reward", f"{reward:.4f}")
    t.add_row("Uncertainty (total)", f"{unc.get('total',0):.3f}", "Grounding", "✓ PASSED" if grounded else "✗ FAILED")
    console.print(Panel(main, title="[bold]KARL DECISION[/bold]", border_style="cyan", expand=False))
    console.print(Panel(t, title="[bold]Metrics[/bold]", border_style="blue", expand=False))
    console.print()

def _fallback_decision(record, amre, synth):
    a = record.get("final_action", synth.get("signal","NEUTRAL"))
    c = record.get("confidence_final", synth.get("confidence",50))
    r = record.get("regime","NORMAL"); p = record.get("price",0)
    u = amre.get("uncertainty",{}); g = amre.get("grounding_passed",True)
    ic = {"LONG":"📈","SHORT":"📉","NEUTRAL":"⏸","AVOID":"🚫"}.get(a,"❓")
    W = 68; print(); print("+"+"="*W+"+")
    print(f"|  {ic} {a}  CONF={c}  REGIME={r}  |")
    print(f"|  Price: ${p:,.2f}  Position: {record.get('position_pct',0)*100:.1f}%")
    print(f"|  Uncertainty: aleatoric={u.get('aleatoric',0):.3f} epistemic={u.get('epistemic',0):.3f} total={u.get('total',0):.3f}")
    print(f"|  Grounding: {'PASSED' if g else 'FAILED'}")
    print("+"+"="*W+"+")

def print_signal_breakdown_rich(synth):
    if not RICH: return _fallback_breakdown(synth)
    bd = synth.get("metadata",{}).get("breakdown","")
    if not bd: return
    t = Table(title="[bold cyan]Agent Breakdown[/bold cyan]", show_header=True, box=None, pad_row=1)
    t.add_column("Category",style="cyan",width=14); t.add_column("Signal",width=10); t.add_column("Confidence",width=12); t.add_column("Agents",style="dim")
    for line in bd.split("\n"):
        if not line.strip(): continue
        parts = line.strip()[1:-1].split("]")
        if len(parts) < 2: continue
        cat = parts[0].strip(); rest = parts[1].strip().split()
        sig = rest[0] if rest else "?"; conf = rest[1] if len(rest)>1 else "?"
        ags = " ".join(rest[2:]) if len(rest)>2 else ""
        sc = {"LONG":"green","SHORT":"red","NEUTRAL":"yellow"}.get(sig,"white")
        t.add_row(f"[{cat}]", f"[{sc}]{sig}[/{sc}]", conf, ags)
    console.print(t); console.print()

def _fallback_breakdown(synth):
    bd = synth.get("metadata",{}).get("breakdown","")
    if bd:
        W = 68; print(); print("+"+"="*W+"+")
        print("|"+"AGENT BREAKDOWN".center(W)+"|")
        print("+"+"="*W+"+")
        for line in bd.split("\n"):
            if line.strip(): print(f"|  {line[:66]}")
        print("+"+"="*W+"+")

def print_karl_diagnostics_rich(diagnostics):
    if not RICH: return _fallback_karl(diagnostics)
    oap = diagnostics.get("oap_kpi",{}); audit = diagnostics.get("audit_summary",{})
    drift = diagnostics.get("drift_status",{}); calibr = diagnostics.get("calibration",{})
    ot = Table(title="[bold]OAP KPIs[/bold]", show_header=False, box=None)
    ot.add_column(style="dim",width=22); ot.add_column(style="white",width=15)
    ot.add_row("TTC Depth", str(oap.get("current_ttc_depth","N/A")))
    ot.add_row("OOS Fail Rate", f"{oap.get('oos_fail_rate',0):.3f}")
    ot.add_row("Entropy", f"{oap.get('entropy_avg',0):.3f}")
    ot.add_row("Grounding Strength", f"{oap.get('grounding_strength',0):.3f}")
    ct = Table(title="[bold]Reward Calibration[/bold]", show_header=False, box=None)
    ct.add_column(style="dim",width=22); ct.add_column(style="white",width=15)
    ct.add_row("Calibration Error", f"{calibr.get('calibration_error',0):.4f}")
    ct.add_row("Slope", f"{calibr.get('slope',0):.4f}")
    ct.add_row("Intercept", f"{calibr.get('intercept',0):.4f}")
    at = Table(title="[bold]Audit Log[/bold]", show_header=False, box=None)
    at.add_column(style="dim",width=22); at.add_column(style="white",width=15)
    at.add_row("Total Decisions", str(audit.get("total",0)))
    at.add_row("Avg Confidence", f"{audit.get('avg_confidence_final',0):.1f}")
    ad = audit.get("action_distribution",{})
    at.add_row("Distribution", f"L={ad.get('LONG',0)} S={ad.get('SHORT',0)} N={ad.get('NEUTRAL',0)}")
    if drift.get("status") == "degrading":
        dt = Text()
        dt.append("⚠  DRIFT DETECTED\n", style="bold yellow")
        dt.append(f"   Confidence drift: {drift.get('confidence_drift',0):+.2f}\n")
        dt.append(f"   Uncertainty drift: {drift.get('uncertainty_drift',0):+.3f}")
        console.print(Panel(dt, title="[bold yellow]Drift Alert[/bold yellow]", border_style="yellow"))
    console.print(ot); console.print(ct); console.print(at); console.print()

def _fallback_karl(diagnostics):
    oap = diagnostics.get("oap_kpi",{}); audit = diagnostics.get("audit_summary",{})
    ad = audit.get("action_distribution",{}); W = 68
    print(); print("+"+"="*W+"+")
    print("|"+"KARL DIAGNOSTICS".center(W)+"|")
    print("+"+"="*W+"+")
    print(f"|  OAP: TTC={oap.get('current_ttc_depth','?')} OOS_fail={oap.get('oos_fail_rate',0):.3f} entropy={oap.get('entropy_avg',0):.3f}")
    print(f"|  Audit: total={audit.get('total',0)} avg_conf={audit.get('avg_confidence_final',0):.1f}")
    print(f"|  Distribution: L={ad.get('LONG',0)} S={ad.get('SHORT',0)} N={ad.get('NEUTRAL',0)}")
    print("+"+"="*W+"+")

def print_entry_levels_rich(synth):
    if not RICH: return
    meta = synth.get("metadata",{}); entry = meta.get("entry_zone",(0,0))
    stop = meta.get("stop_loss",0); targets = meta.get("targets",[]); pos = meta.get("position_size",0)
    price = meta.get("current_price",0)
    t = Table(title="[bold green]Entry Levels[/bold green]", show_header=True, box=None)
    t.add_column("Level",style="cyan",width=20); t.add_column("Price",style="white",width=15); t.add_column("Distance",style="dim",width=15)
    for i, tp in enumerate(targets[:3]):
        dist = f"+{(tp-price)/price*100:.1f}%" if price else "?"
        t.add_row(f"Target {i+1}", f"${tp:,.2f}", dist)
    t.add_row("Stop Loss", f"${stop:,.2f}", f"-{(price-stop)/price*100:.1f}%" if price else "?")
    t.add_row("Position Size", f"{pos*100:.2f}%", f"Risk: ${price*pos:.0f}" if price else "?")
    console.print(t)

def save_decision_jsonl(record, filepath="data/karl_decisions.jsonl"):
    Path(filepath).parent.mkdir(parents=True, exist_ok=True)
    with open(filepath,"a") as f: f.write(json.dumps(record,default=str)+"\n")

def generate_html_report(result, output_path="data/karl_report.html"):
    synth = result.get("final_recommendation",{}); record = result.get("decision_record",{}); amre = result.get("amre_output",{})
    action = synth.get("signal","NEUTRAL"); confidence = synth.get("confidence",50)
    price = synth.get("metadata",{}).get("current_price",0)
    regime = synth.get("metadata",{}).get("volatility_risk",{}).get("regime","NORMAL")
    bd = synth.get("metadata",{}).get("breakdown","")
    rc = {"LOW":"#22c55e","NORMAL":"#eab308","HIGH":"#f97316","EXTREME":"#ef4444"}.get(regime,"#6b7280")
    ac = {"LONG":"#22c55e","SHORT":"#ef4444","NEUTRAL":"#6b7280","AVOID":"#dc2626"}.get(action,"#6b7280")
    unc = amre.get("uncertainty",{}); qs = record.get("q_star",0)
    bh = "".join(f"<tr><td colspan=4 style=font-family:monospace;font-size:11px>{l}</td></tr>" for l in bd.split("\n") if l.strip())
    html = f"<!DOCTYPE html><html><head><meta charset=utf-8><title>ATOM-017 KARL Report</title>"
    html += f"<style>body{{font-family:-apple-system,sans-serif;background:#0f172a;color:#e2e8f0;padding:20px}}.container{{max-width:900px;margin:0 auto}}.signal-box{{background:{ac}22;border-left:6px solid {ac};padding:20px;margin:20px 0;border-radius:8px}}.signal-action{{font-size:32px;font-weight:bold;color:{ac}}}.metric{{font-size:24px;font-weight:bold;color:#38bdf8}}.metric-label{{font-size:12px;color:#94a3b8}}.grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin:20px 0}}.card{{background:#1e293b;border-radius:8px;padding:16px}}table{{width:100%;border-collapse:collapse;margin:20px 0}}th{{background:#1e293b;text-align:left;padding:8px}}td{{padding:8px;border-bottom:1px solid #334155}}</style></head>"
    html += f"<body><div class=container><h1>AstroFin Sentinel v5 — KARL Report</h1>"
    html += f"<div class=timestamp>Generated: {datetime.now().isoformat()}</div>"
    html += f"<div class=signal-box><div class=signal-action>{action}</div>"
    html += f"<div>Confidence: {confidence}/100 | Price: ${price:,.2f} | Symbol: {result.get('symbol','BTC')}</div><div>Regime: {regime}</div></div>"
    html += f"<div class=grid><div class=card><div class=metric-label>Decision ID</div><div class=metric>{record.get('decision_id','N/A')}</div></div>"
    html += f"<div class=card><div class=metric-label>Q*</div><div class=metric>{qs:.4f}</div></div>"
    html += f"<div class=card><div class=metric-label>Uncertainty</div><div class=metric>{unc.get('total',0):.3f}</div></div></div>"
    html += f"<h2>Agent Breakdown</h2><table><th colspan=4>Signals</th>{bh}</table>"
    ez = synth.get("metadata",{}).get("entry_zone","N/A"); sl = synth.get("metadata",{}).get("stop_loss","N/A")
    tgs = synth.get("metadata",{}).get("targets",[]); pos = synth.get("metadata",{}).get("position_size",0)
    html += f"<h2>Entry Levels</h2><table><tr><td>Entry Zone</td><td>{ez}</td></tr><tr><td>Stop Loss</td><td>{sl}</td></tr>"
    for i, t in enumerate(tgs[:3]): html += f"<tr><td>Target {i+1}</td><td>${t:,.2f}</td></tr>"
    html += f"<tr><td>Position Size</td><td>{pos*100:.2f}%</td></tr></table></div></body></html>"
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path,"w") as f: f.write(html)
    return output_path