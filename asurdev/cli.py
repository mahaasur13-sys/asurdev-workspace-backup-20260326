#!/usr/bin/env python3
"""
asurdev Sentinel CLI
=====================
Автономный CLI для расчёта астрологических карт, панчанги, мухурты и финансовых сигналов.

Запуск:
    python cli.py chart 2026-03-22 12:00:00 --lat 55.75 --lon 37.62
    python cli.py astro now
    python cli.py analyze BTC --action hold
"""
import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import print as rprint
from rich.tree import Tree
from datetime import datetime, timedelta
from typing import Optional, List
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

app = typer.Typer(
    name="asurdev",
    help="asurdev Sentinel CLI — астрологические расчёты и финансовые сигналы",
    add_completion=False,
    no_args_is_help=True,
)

console = Console()


# ============================================================================
# HELPERS
# ============================================================================

def load_swiss_ephemeris():
    """Lazy load Swiss Ephemeris tool."""
    from swiss_ephemeris.swiss_ephemeris_tool import swiss_ephemeris
    return swiss_ephemeris


def format_degrees(deg: float) -> str:
    """Format degrees as zodiac sign and degree."""
    signs = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
             "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
    deg = deg % 360
    sign_idx = int(deg // 30)
    deg_in_sign = deg % 30
    return f"{signs[sign_idx]} {deg_in_sign:.2f}°"


def render_planets(positions: dict) -> Table:
    """Render planet positions as a table."""
    table = Table(title="Позиции планет", show_header=True, header_style="bold cyan")
    table.add_column("Планета", style="cyan", width=12)
    table.add_column("Знак", style="magenta")
    table.add_column("Долгота", justify="right", width=12)
    table.add_column("Скорость", justify="right", width=10)

    for planet, data in positions.items():
        lon = data.get("lon", 0)
        speed = data.get("speed", 0)
        table.add_row(
            planet,
            format_degrees(lon),
            f"{lon:.4f}°",
            f"{speed:+.4f}°/day"
        )
    return table


def render_panchanga(panchanga: dict) -> Table:
    """Render Panchanga data as a table."""
    table = Table(title="Панчанга", show_header=True, header_style="bold green")
    table.add_column("Элемент", style="green", width=16)
    table.add_column("Значение", style="white")

    items = [
        ("Вара (день)", panchanga.get("vara", "-")),
        ("Титхи", f"{panchanga.get('tithi', '-')} ({panchanga.get('tithi_paksha', '')})"),
        ("Накшатра", f"{panchanga.get('nakshatra', '-')} ({panchanga.get('nakshatra_number', '')}/{panchanga.get('nakshatra_pada', '')})"),
        ("Йога", f"{panchanga.get('yoga', '-')} ({panchanga.get('yoga_category', '')})"),
        ("Карана", panchanga.get("karana", "-")),
    ]
    for k, v in items:
        table.add_row(k, str(v))
    return table


def render_houses(houses: dict) -> Table:
    """Render house cusps as a table."""
    table = Table(title="Дома (Куспы)", show_header=True, header_style="bold yellow")
    table.add_column("Дом", style="yellow", width=6, justify="center")
    table.add_column("Куспид", style="white", width=20)

    for i in range(1, 13):
        key = f"house_{i}"
        if key in houses:
            lon = houses[key]
            table.add_row(str(i), format_degrees(lon))
    return table


# ============================================================================
# COMMANDS
# ============================================================================

@app.command("chart")
def compute_chart(
    date: str = typer.Argument(..., help="Дата в формате YYYY-MM-DD"),
    time: str = typer.Argument(..., help="Время в формате HH:MM:SS"),
    lat: float = typer.Option(55.7558, "--lat", "-l", help="Широта места"),
    lon: float = typer.Option(37.6173, "--lon", "-o", help="Долгота места"),
    ayanamsa: str = typer.Option("lahiri", "--ayanamsa", "-a", help="Аянамаса (lahiri, raman, krishnamurti)"),
    zodiac: str = typer.Option("sidereal", "--zodiac", "-z", help="Зодиак (sidereal, tropical)"),
    house_system: str = typer.Option("W", "--houses", "-h", help="Система домов (W=Whole Sign, P=Placidus, K=Koch)"),
    compute_panchanga: bool = typer.Option(True, "--panchanga/--no-panchanga", "-p", help="Расчёт панчанги"),
    compute_choghadiya: bool = typer.Option(True, "--choghadiya/--no-choghadiya", "-c", help="Расчёт чохгадии"),
    compute_ashtakavarga: bool = typer.Option(False, "--ashtakavarga/--no-ashtakavarga", help="Расчёт аштакаварги"),
):
    """
    Расчёт натальной карты с панчандой и чохгадией.

    Примеры:
        asurdev chart 2026-03-22 12:00:00 --lat 55.75 --lon 37.62
        asurdev chart 2026-04-15 06:30:00 -l 59.93 -o 30.35 -a raman
    """
    swiss_ephemeris = load_swiss_ephemeris()

    console.print(Panel.fit(
        f"[bold cyan]Расчёт карты[/bold cyan] {date} {time}",
        subtitle=f"{lat}°, {lon}° | {ayanamsa} | {zodiac} | {house_system}"
    ))

    try:
        result = swiss_ephemeris(
            date=date,
            time=time,
            lat=lat,
            lon=lon,
            ayanamsa=ayanamsa,
            zodiac=zodiac,
            house_system=house_system,
            compute_houses=True,
            compute_panchanga=compute_panchanga,
            compute_choghadiya=compute_choghadiya,
            compute_ashtakavarga=compute_ashtakavarga,
        )

        if "errors" in result and result["errors"]:
            console.print(f"[bold red]Ошибка:[/bold red] {result['errors']}")
            raise typer.Exit(1)

        # Render planets
        positions = result.get("positions", {})
        if positions:
            console.print(render_planets(positions))

        # Render houses
        houses = result.get("houses", {})
        if houses:
            console.print(render_houses(houses))

        # Render Panchanga
        if compute_panchanga:
            panchanga = result.get("panchanga", {})
            if panchanga:
                console.print(render_panchanga(panchanga))

                # Render Choghadiya
                if compute_choghadiya:
                    choghadiya = result.get("choghadiya", [])
                    if choghadiya:
                        chogh_table = Table(title="Чохгадия (сегодня)", show_header=True, header_style="bold blue")
                        chogh_table.add_column("Период", style="blue", width=8)
                        chogh_table.add_column("Название", style="cyan")
                        chogh_table.add_column("Тип", width=10)
                        for ch in choghadiya[:8]:
                            favorable = "✓" if ch.get("favorable") else "✗"
                            chogh_table.add_row(
                                ch.get("period", "-"),
                                ch.get("name", "-"),
                                f"[{'green' if ch.get('favorable') else 'red'}]{favorable}[/]"
                            )
                        console.print(chogh_table)

        console.print(f"\n[bold green]✓[/bold green] Расчёт завершён за {result.get('calculation_time', 'N/A')}ms")

    except Exception as e:
        console.print(f"[bold red]Ошибка расчёта:[/bold red] {str(e)}")
        raise typer.Exit(1)


@app.command("astro")
def current_astro(
    lat: float = typer.Option(55.7558, "--lat", "-l", help="Широта"),
    lon: float = typer.Option(37.6173, "--lon", "-o", help="Долгота"),
):
    """
    Текущее астрологическое состояние (быстрый расчёт).
    """
    swiss_ephemeris = load_swiss_ephemeris()

    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H:%M:%S")

    console.print(Panel.fit(
        f"[bold cyan]Текущее состояние[/bold cyan] {date_str} {time_str}",
        subtitle=f"{lat}°, {lon}°"
    ))

    try:
        result = swiss_ephemeris(
            date=date_str,
            time=time_str,
            lat=lat,
            lon=lon,
            ayanamsa="lahiri",
            zodiac="sidereal",
            house_system="W",
            compute_houses=False,
            compute_panchanga=True,
            compute_choghadiya=True,
        )

        p = result.get("panchanga", {})

        # Quick summary
        summary = Table(show_header=False, box=None, padding=(0, 2))
        summary.add_row("[bold]Солнце в[/bold]", format_degrees(result.get("positions", {}).get("Sun", {}).get("lon", 0)))
        summary.add_row("[bold]Луна в[/bold]", format_degrees(result.get("positions", {}).get("Moon", {}).get("lon", 0)))
        summary.add_row("[bold]Вара[/bold]", p.get("vara", "-"))
        summary.add_row("[bold]Титхи[/bold]", f"{p.get('tithi', '-')} ({p.get('tithi_paksha', '')})")
        summary.add_row("[bold]Накшатра[/bold]", p.get("nakshatra", "-"))
        summary.add_row("[bold]Йога[/bold]", p.get("yoga", "-"))

        console.print(summary)

        # Current Choghadiya
        choghadiya = result.get("choghadiya", {})
        if choghadiya:
            console.print("\n[bold cyan]Текущая Чохгадия:[/bold cyan]")
            day_parts = choghadiya.get("day_parts", [])
            night_parts = choghadiya.get("night_parts", [])
            all_parts = day_parts + night_parts
            
            if all_parts:
                for ch in all_parts[:3]:
                    favorable = "🟢" if ch.get("auspicious") else "🔴"
                    console.print(f"  {favorable} {ch.get('type', '-')} ({ch.get('period', '-')})")

    except Exception as e:
        console.print(f"[bold red]Ошибка:[/bold red] {str(e)}")
        raise typer.Exit(1)


@app.command("analyze")
def analyze(
    symbol: str = typer.Argument(..., help="Тикер (BTC, ETH, SOL...)"),
    action: str = typer.Option("hold", "--action", "-a", help="Действие (buy/sell/hold)"),
    lat: float = typer.Option(55.7558, "--lat", "-l", help="Широта"),
    lon: float = typer.Option(37.6173, "--lon", "-o", help="Долгота"),
):
    """
    Полный анализ символа через AstroCouncil.

    Пример:
        asurdev analyze BTC --action hold
    """
    console.print(Panel.fit(
        f"[bold cyan]Анализ {symbol.upper()}[/bold cyan]",
        subtitle=f"Действие: {action.upper()} | {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    ))

    try:
        from agents.orchestrator import Orchestrator
        import asyncio

        orch = Orchestrator()
        result = asyncio.run(orch.analyze(symbol.upper(), action))

        if result.get("error"):
            console.print(f"[bold red]Ошибка:[/bold red] {result['error']}")
            raise typer.Exit(1)

        # Print summary
        tree = Tree("📊 Результат")
        tree.add(f"Сигнал: [bold]{result.get('signal', 'NEUTRAL')}[/bold]")
        tree.add(f"Уверенность: [yellow]{result.get('confidence', 0)}%[/yellow]")
        tree.add(f"Действие: [bold]{result.get('action', 'hold').upper()}[/bold]")

        console.print(tree)

        # Show agent votes if available
        if "agent_signals" in result:
            console.print("\n[bold cyan]Голоса агентов:[/bold cyan]")
            for agent_name, vote in result["agent_signals"].items():
                signal_emoji = "🟢" if vote.get("signal") == "BUY" else "🔴" if vote.get("signal") == "SELL" else "🟡"
                console.print(f"  {signal_emoji} {agent_name}: {vote.get('signal')} ({vote.get('confidence', 0)}%)")

    except ImportError as e:
        console.print(f"[bold red]Ошибка импорта:[/bold red] {str(e)}")
        console.print("Установите зависимости: pip install -r requirements.txt")
    except Exception as e:
        console.print(f"[bold red]Ошибка анализа:[/bold red] {str(e)}")
        raise typer.Exit(1)


@app.command("now")
def quick_now(
    lat: float = typer.Option(55.7558, "--lat", "-l", help="Широта"),
    lon: float = typer.Option(37.6173, "--lon", "-o", help="Долгота"),
):
    """Быстрая сводка — то же самое что astro now."""
    ctx = typer.Context.current
    ctx.invoke(current_astro, lat=lat, lon=lon)


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    app()

# ============================================================================
# BOARD OF DIRECTORS COMMANDS
# ============================================================================

@app.command("board")
def board_command(
    query: str = typer.Argument(..., help="Финансовый вопрос для анализа"),
    mode: str = typer.Option("debate", "--mode", "-m", help="Режим: debate или round-robin"),
    no_astro: bool = typer.Option(False, "--no-astro", help="Без астрологии"),
    no_risk: bool = typer.Option(False, "--no-risk", help="Без управления рисками"),
    json_output: bool = typer.Option(False, "--json", help="JSON вывод"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Подробный вывод"),
):
    """
    Запуск Board of Directors — мультиагентный совет директоров.
    
    Примеры:
        asurdev board "Should I buy BTC at current levels?"
        asurdev board "Анализ ETH для покупки" --mode debate --json
    """
    import asyncio
    import json
    
    async def run():
        from agents._impl.board import BoardOfDirectors
        
        if verbose:
            console.print(f"[dim]Режим: {mode}[/dim]")
            console.print(f"[dim]Астрология: {not no_astro}[/dim]")
            console.print(f"[dim]Риск-менеджер: {not no_risk}[/dim]")
        
        board = BoardOfDirectors(
            provider="auto",
            mode=mode,
            include_astrology=not no_astro,
            include_risk_manager=not no_risk,
        )
        
        await board.initialize()
        
        try:
            verdict = await board.conduct_vote(query)
            
            if json_output:
                console.print_json(json.dumps(verdict.to_dict(), ensure_ascii=False))
            else:
                _print_board_verdict(verdict)
                
        finally:
            pass
    
    asyncio.run(run())


def _print_board_verdict(verdict):
    """Print board verdict in human-readable format."""
    console.print(Panel.fit(
        "[bold cyan]FINAL BOARD VERDICT[/bold cyan]",
        subtitle=f"Вердикт вынесен за {verdict.elapsed_seconds:.1f}s"
    ))
    
    # Print individual votes
    for vote in verdict.votes:
        emoji = "🟢" if vote.recommendation.value == "BUY" else "🔴" if vote.recommendation.value == "SELL" else "🟡"
        console.print(f"\n{emoji} [bold]{vote.agent_name}[/bold]")
        console.print(f"   Рекомендация: {vote.recommendation.value}")
        console.print(f"   Уверенность: {vote.confidence:.0%}")
    
    # Print final verdict
    console.print(f"\n{'='*60}")
    console.print(f"[bold]ИТОГОВЫЙ ВЕРДИКТ: {verdict.recommendation.value}[/bold]")
    console.print(f"Уверенность: {verdict.confidence:.0%}")
    console.print(f"Риск: {verdict.risk_level.value}")
    console.print(f"Горизонт: {verdict.time_horizon}")
    console.print(f"\nТезис: {verdict.thesis}")
    
    if verdict.dissent:
        console.print(f"\n[yellow]⚠️ Особое мнение:[/yellow]")
        for d in verdict.dissent:
            console.print(f"   - {d}")
    
    console.print(f"\n{'='*60}")
