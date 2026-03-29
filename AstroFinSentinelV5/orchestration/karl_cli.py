"""orchestration/karl_cli.py — ATOM-017: Industrial KARL CLI + Rich UI"""
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
    banner = r"""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║   ███████╗██╗   ██╗██████╗ ██████╗  █████╗ ██████╗ ██████╗   ║
║   ██╔════╝██║   ██║██╔══██╗██╔══██╗██╔══██╗██╔══██╗██╔══██╗  ║
║   ███████╗██║   ██║██████╔╝██████╔╝███████║██████╔╝██║  ██║  ║
║   ╚════██║██║   ██║██╔═══╝ ██╔══██╗██╔══██║██╔══██╗██║  ██║  ║
║   ███████║╚██████╔╝██║     ██║  ██║██║  ██║██║  ██║██████╔╝  ║
║   ╚══════╝ ╚═════╝ ╚═╝     ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝╚═════╝   ║
║                                                              ║
║   SENTINEL v5 — KARL MODE  ·  ATOM-017  ·  Industrial CLI  ║
╚══════════════════════════════════════════════════════════════╝"""
    cprint(banner, "bold cyan on black")

def print_decision_rich(record, amre, synth):
    if not RICH: return print_decision_ascii(record, amre, synth)
    action = record.get("final_action", synth.get("signal", "NEUTRAL"))
    confidence = record.get("confidence_final", synth.get("confidence", 50))
    regime = record.get("regime", "NORMAL")
    price = record.get("price", 0)
    decision_id = record.get("decision_id", "N/A")
    q_star = record.get("q_star", 0)
    reward = amre.get("reward_estimate", 0)
    unc = amre.get("uncertainty", {})
    grounded = amre.get("grounding_passed", True)
    action_color = {"LONG":"green","SHORT":"red","NEUTRAL":"yellow","AVOID":"bold red"}.get(action, "white")
    regime_color = {"LOW":"green","NORMAL":"yellow","HIGH":"bold yellow","EXTREME":"bold red"}.get(regime, "white")
    action_icon = {"LONG":"📈","SHORT":"📉","NEUTRAL":"⏸","AVOID":"🚫"}.get(action, "❓")
    main = Text()
    main.append(f"  {action_icon} ACTION  ", style=f"bold {action_color}")
    main.append(f"  CONF={confidence:3}  ", style="bold white")
    main.append(f"  REGIME={regime}  ", style=regime_color)
    main.append(f"  ID={decision_id}", style="dim")
    t = Table(show_header=False, box=None)
    t.add_column(style="dim", width=20); t.add_column(style="white", width=20)
    t.add_column(style="dim", width=20); t.add_column(style="white", width=20)
    t.add_row("Price", f"${price:,.2f}", "Position", f"{record.get('position_pct',0)*100:.1f}%")
    t.add_row("Q*", f"{q_star:.4f}", "Reward", f"{reward:.4f}")
    t.add_row("Uncertainty (total)", f"{unc.get('total',0):.3f}", "Grounding", "✓ PASSED" if grounded else "✗ FAILED")
    try:
        console.print(Panel(main, title="[bold]KARL DECISION[/bold]", border_style="cyan", expand=False))
        console.print(Panel(t, title="[bold]Metrics[/bold]", border_style="blue", expand=False))
    except Exception as e:
        print(f"[WARN] Failed to print decision panel: {e}")
    console.print()

def print_decision_ascii(record, amre, synth):
    W = 68
    action = record.get("final_action", synth.get("signal", "NEUTRAL"))
    confidence = record.get("confidence_final", synth.get("confidence", 50))
    regime = record.get("regime", "NORMAL")
    price = record.get("price", 0); decision_id = record.get("decision_id", "N/A")
    unc = amre.get("uncertainty", {}); grounded = amre.get("grounding_passed", True)
    icon = {"LONG":"+LONG","SHORT":"-SHORT","NEUTRAL":"=NEUT","AVOID":"!AVOID"}.get(action, " ? ")
    sep = "+" + "="*W + "+"
    print()
    print(sep)
    print("|  " + icon + "  CONF=" + str(confidence) + "  REGIME=" + regime + "  ID=" + decision_id)
    print("|  Price: $%s  |  Position: %.1f%%" % ("%,.2f" % price, record.get("position_pct",0)*100))
    print("|  Uncertainty: aleatoric=%.3f  epistemic=%.3f  total=%.3f" % (unc.get("aleatoric",0), unc.get("epistemic",0), unc.get("total",0)))
    print("|  Grounding: " + ("PASSED" if grounded else "FAILED"))
    print(sep)
    print()

def print_signal_breakdown_rich(synth):
    if not RICH: return print_signal_breakdown_ascii(synth)
    breakdown = synth.get("metadata", {}).get("breakdown", "")
    if not breakdown: return
    t = Table(title="[bold cyan]Agent Breakdown[/bold cyan]", show_header=True, box=None)
    t.add_column("Category", style="cyan", width=14); t.add_column("Signal", width=10)
    t.add_column("Confidence", width=12); t.add_column("Agents", style="dim")
    for line in breakdown.split("\n"):
        if not line.strip(): continue
        parts = line.strip()[1:-1].split("]")
        if len(parts) < 2: continue
        cat = parts[0].strip(); rest = parts[1].strip().split()
        signal = rest[0] if rest else "?"; conf = rest[1] if len(rest) > 1 else "?"
        agents = " ".join(rest[2:]) if len(rest) > 2 else ""
        sc = {"LONG":"green","SHORT":"red","NEUTRAL":"yellow"}.get(signal, "white")
        t.add_row(f"[{cat}]", f"[{sc}]{signal}[/{sc}]", conf, agents)
    try:
        console.print(t); console.print()
    except Exception as e:
        print(f"[WARN] Failed to print signal breakdown panel: {e}")

def print_signal_breakdown_ascii(synth):
    breakdown = synth.get("metadata", {}).get("breakdown", "")
    if breakdown:
        W = 68
        horiz = "─"*W
        vert = "│"
        sep_h = "+" + horiz + "+"
        print()
        print(sep_h)
        print(vert + "AGENT BREAKDOWN".center(W) + vert)
        print(sep_h)
        for line in breakdown.split("\n"):
            if line.strip(): print(vert + "  " + line[:66].ljust(W-2) + vert)
        print(sep_h)
        print()

def print_karl_diagnostics_rich(diagnostics):
    if not RICH: return print_karl_diagnostics_ascii(diagnostics)
    oap = diagnostics.get("oap_kpi", {}); audit = diagnostics.get("audit_summary", {})
    drift = diagnostics.get("drift_status", {}); calibr = diagnostics.get("calibration", {})
    ot = Table(title="[bold]OAP KPIs[/bold]", show_header=False, box=None)
    ot.add_column(style="dim", width=22); ot.add_column(style="white", width=15)
    ot.add_row("TTC Depth", str(oap.get("current_ttc_depth", "N/A")))
    ot.add_row("OOS Fail Rate", f"{oap.get('oos_fail_rate',0):.3f}")
    ot.add_row("Entropy", f"{oap.get('entropy_avg',0):.3f}")
    ot.add_row("Grounding Strength", f"{oap.get('grounding_strength',0):.3f}")
    ct = Table(title="[bold]Reward Calibration[/bold]", show_header=False, box=None)
    ct.add_column(style="dim", width=22); ct.add_column(style="white", width=15)
    ct.add_row("Calibration Error", f"{calibr.get('calibration_error',0):.4f}")
    ct.add_row("Slope", f"{calibr.get('slope',0):.4f}")
    ct.add_row("Intercept", f"{calibr.get('intercept',0):.4f}")
    at = Table(title="[bold]Audit Log[/bold]", show_header=False, box=None)
    at.add_column(style="dim", width=22); at.add_column(style="white", width=15)
    at.add_row("Total Decisions", str(audit.get("total", 0)))
    at.add_row("Avg Confidence", f"{audit.get('avg_confidence_final',0):.1f}")
    ad = audit.get("action_distribution", {})
    at.add_row("Action Distribution", f"L={ad.get('LONG',0)} S={ad.get('SHORT',0)} N={ad.get('NEUTRAL',0)}")
    if drift.get("status") == "degrading":
        dt = Text(); dt.append("⚠  DRIFT DETECTED\n", style="bold yellow")
        dt.append(f"   Confidence drift: {drift.get('confidence_drift',0):+.2f}\n")
        dt.append(f"   Uncertainty drift: {drift.get('uncertainty_drift',0):+.3f}")
        try:
            console.print(Panel(dt, title="[bold yellow]Drift Alert[/bold yellow]", border_style="yellow"))
        except Exception as e:
            print(f"[WARN] Failed to print drift alert panel: {e}")
    try:
        console.print(ot); console.print(ct); console.print(at); console.print()
    except Exception as e:
        print(f"[WARN] Failed to print diagnostics panels: {e}")

def print_karl_diagnostics_ascii(diagnostics):
    oap = diagnostics.get("oap_kpi", {}); audit = diagnostics.get("audit_summary", {})
    ad = audit.get("action_distribution", {})
    W = 68
    horiz = "─"*W; vert = "│"
    sep_h = "+" + horiz + "+"
    print()
    print(sep_h)
    print(vert + "KARL DIAGNOSTICS".center(W) + vert)
    print(sep_h)
    print(vert + "  OAP: TTC=%s  OOS_fail=%.3f  entropy=%.3f" % (
        oap.get('current_ttc_depth','?'), oap.get('oos_fail_rate',0), oap.get('entropy_avg',0)) + vert)
    print(vert + "  Audit: total=%d  avg_conf=%.1f" % (
        audit.get('total',0), audit.get('avg_confidence_final',0)) + vert)
    print(vert + "  Actions: L=%d  S=%d  N=%d" % (
        ad.get('LONG',0), ad.get('SHORT',0), ad.get('NEUTRAL',0)) + vert)
    print(sep_h)
    print()

def print_entry_levels_rich(synth):
    if not RICH: return
    meta = synth.get("metadata", {})
    entry = meta.get("entry_zone", (0,0)); stop = meta.get("stop_loss", 0)
    targets = meta.get("targets", []); position = meta.get("position_size", 0)
    price = meta.get("current_price", 0)
    t = Table(title="[bold green]Entry Levels[/bold green]", show_header=True, box=None)
    t.add_column("Level", style="cyan", width=20); t.add_column("Price", style="white", width=15); t.add_column("Distance", style="dim", width=15)
    for i, tp in enumerate(targets[:3]):
        dist = f"+{(tp-price)/price*100:.1f}%" if price else "?"
        t.add_row(f"Target {i+1}", f"${tp:,.2f}", dist)
    t.add_row("Stop Loss", f"${stop:,.2f}", f"-{(price-stop)/price*100:.1f}%" if price else "?")
    t.add_row("Position Size", f"{position*100:.2f}%", f"Risk: ${price*position:.0f}" if price else "?")
    try:
        console.print(t)
    except Exception as e:
        print(f"[WARN] Failed to print entry levels panel: {e}")

def print_entry_levels_ascii(synth):
    meta = synth.get("metadata", {}); entry = meta.get("entry_zone", (0,0))
    stop = meta.get("stop_loss", 0); targets = meta.get("targets", [])
    W = 68
    horiz = "─"*W; vert = "│"
    sep_h = "+" + horiz + "+"
    print()
    print(sep_h)
    print(vert + "ENTRY LEVELS".center(W) + vert)
    print(sep_h)
    print(vert + "  Entry Zone:  $%.2f — $%.2f" % (entry[0], entry[1]) + vert)
    print(vert + "  Stop Loss:    $%.2f" % stop + vert)
    for i, tp in enumerate(targets[:3]): print(vert + "  Target %d:    $%.2f" % (i+1, tp) + vert)
    print(sep_h)
    print()

def save_decision_jsonl(record, filepath="data/karl_decisions.jsonl"):
    if not record:
        print("[WARN] Skipping empty decision record"); return
    from core.safe_json import safe_jsonl_append
    safe_jsonl_append(record, filepath)

def generate_html_report(result, output_path="data/karl_report.html"):
    synth = result.get("final_recommendation", {})
    record = result.get("decision_record", {}); amre = result.get("amre_output", {})
    action = synth.get("signal", "NEUTRAL"); confidence = synth.get("confidence", 50)
    price = synth.get("metadata", {}).get("current_price", 0)
    regime = synth.get("metadata", {}).get("volatility_risk", {}).get("regime", "NORMAL")
    breakdown = synth.get("metadata", {}).get("breakdown", "")
    regime_c = {"LOW":"#22c55e","NORMAL":"#eab308","HIGH":"#f97316","EXTREME":"#ef4444"}.get(regime,"#6b7280")
    action_c = {"LONG":"#22c55e","SHORT":"#ef4444","NEUTRAL":"#6b7280","AVOID":"#dc2626"}.get(action,"#6b7280")
    unc = amre.get("uncertainty", {}); q_star = record.get("q_star", 0)
    bh = "".join(f"<tr><td colspan=4 style=font-family:monospace;font-size:11px>{l}</td></tr>" for l in breakdown.split("\n") if l.strip())
    html = f"""<!DOCTYPE html><html><head><meta charset=utf-8><title>ATOM-017 KARL Report</title>"""
    html += f"""<style>body{{font-family:-apple-system,sans-serif;background:#0f172a;color:#e2e8f0;padding:20px}}"""
    html += f"""<style>.container{{max-width:900px;margin:0 auto}}.signal-box{{background:{action_c}22;border-left:6px solid {action_c};padding:20px;margin:20px 0;border-radius:8px}}.signal-action{{font-size:32px;font-weight:bold;color:{action_c}}}.metric{{font-size:24px;font-weight:bold;color:#38bdf8}}.metric-label{{font-size:12px;color:#94a3b8}}.grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin:20px 0}}.card{{background:#1e293b;border-radius:8px;padding:16px}}table{{width:100%;border-collapse:collapse;margin:20px 0}}th{{background:#1e293b;text-align:left;padding:8px}}td{{padding:8px;border-bottom:1px solid #334155}}</style></head>"""
    html += f"""<body><div class="container"><h1>AstroFin Sentinel v5 — KARL Report</h1>"""
    html += f"""<div class="timestamp">Generated: {datetime.now().isoformat()}</div>"""
    html += f"""<div class="signal-box"><div class="signal-action">{action}</div><div>Confidence: {confidence}/100 | Price: ${price:,.2f} | Symbol: {result.get("symbol","BTC")}</div><div>Regime: {regime}</div></div>"""
    html += f"""<div class="grid"><div class="card"><div class="metric-label">Decision ID</div><div class="metric">{record.get("decision_id","N/A")}</div></div>"""
    html += f"""<div class="card"><div class="metric-label">Q*</div><div class="metric">{q_star:.4f}</div></div>"""
    html += f"""<div class="card"><div class="metric-label">Uncertainty</div><div class="metric">{unc.get("total",0):.3f}</div></div></div>"""
    html += f"""<h2>Agent Breakdown</h2><table><th colspan=4>Signals</th>{bh}</table>"""
    entry_zone = synth.get("metadata", {}).get("entry_zone", "N/A")
    stop_loss = synth.get("metadata", {}).get("stop_loss", "N/A")
    targets = synth.get("metadata", {}).get("targets", [])
    position = synth.get("metadata", {}).get("position_size", 0)
    html += f"""<h2>Entry Levels</h2><table><tr><td>Entry Zone</td><td>{entry_zone}</td></tr><tr><td>Stop Loss</td><td>{stop_loss}</td></tr>"""
    for i, t in enumerate(targets[:3]): html += f"""<tr><td>Target {i+1}</td><td>${t:,.2f}</td></tr>"""
    html += f"""<tr><td>Position Size</td><td>{position*100:.2f}%</td></tr></table></div></body></html>"""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f: f.write(html)
    return output_path
def print_topology_viz(topology_dict: dict = None, session_id: str = None):
    """Print topology visualization"""
    if topology_dict is None:
        print("[INFO] No topology provided. Use --topology flag in KARL mode.")
        return
    
    try:
        from mas_factory.topology import Topology
        from mas_factory.visualizer import TopologyVisualizer
        
        topo = Topology.from_dict(topology_dict) if isinstance(topology_dict, dict) else topology_dict
        viz = TopologyVisualizer(topo)
        
        print("\n" + "=" * 60)
        print("TOPOLOGY VISUALIZATION")
        print("=" * 60)
        print(viz.to_ascii())
        
        print("\n[CADvisor] Mermaid diagram saved. Use --viz flag to see full output.")
        
    except ImportError:
        print("[WARN] mas_factory not available")
    except Exception as e:
        print(f"[ERROR] Failed to visualize topology: {e}")

async def visualize_current_topology(session_id: str = None):
    """Load and visualize current topology from KARL system"""
    try:
        from mas_factory.architect import get_current_topology
        
        topo = get_current_topology()
        if topo:
            print_topology_viz(topo, session_id)
        else:
            print("[INFO] No active topology. Run a KARL session first.")
    except ImportError:
        print("[WARN] mas_factory not available")
