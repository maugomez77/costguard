"""CLI for Cost Guard — local management and server control."""

from __future__ import annotations

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .models import Project
from .store import compute_spend, get_alerts, list_agents, list_projects, save_project

app = typer.Typer(help="AI Agent Cost Guard — real-time cost monitoring for AI agents")
console = Console()


@app.command()
def serve(
    host: str = typer.Option("0.0.0.0", help="Host to bind"),
    port: int = typer.Option(8000, help="Port to bind"),
    reload: bool = typer.Option(False, help="Auto-reload on changes"),
):
    """Start the Cost Guard API server."""
    import uvicorn
    console.print(Panel(
        f"[bold green]Cost Guard API[/bold green]\n"
        f"Listening on [cyan]{host}:{port}[/cyan]\n"
        f"Docs at [link]http://localhost:{port}/docs[/link]",
        title="Cost Guard",
    ))
    uvicorn.run("costguard.api:app", host=host, port=port, reload=reload)


@app.command()
def init(
    name: str = typer.Option(..., prompt="Project name"),
    budget: float = typer.Option(500.0, help="Monthly budget ($)"),
    hard_limit: float = typer.Option(None, help="Hard spending limit — circuit opens here"),
):
    """Create a new project and get your API key."""
    project = Project(name=name, budget_monthly=budget, hard_limit=hard_limit)
    save_project(project)
    console.print(Panel(
        f"[bold green]Project created![/bold green]\n\n"
        f"Project ID: [cyan]{project.id}[/cyan]\n"
        f"API Key:    [bold yellow]{project.api_key}[/bold yellow]\n"
        f"Budget:     ${budget:.2f}/month\n"
        f"Hard Limit: {'$' + f'{hard_limit:.2f}' if hard_limit else 'None'}\n\n"
        f"[dim]Save your API key — it won't be shown again.[/dim]",
        title="Cost Guard Setup",
    ))


@app.command()
def projects():
    """List all projects."""
    projs = list_projects()
    if not projs:
        console.print("[dim]No projects yet. Run [bold]costguard init[/bold] to create one.[/dim]")
        return

    table = Table(title="Projects")
    table.add_column("ID", style="cyan")
    table.add_column("Name")
    table.add_column("Budget", justify="right")
    table.add_column("Agents", justify="right")
    table.add_column("Spend (Month)", justify="right")
    table.add_column("Budget %", justify="right")

    for p in projs:
        agents = list_agents(p.id)
        spend = compute_spend(p.id)
        pct_style = "green" if spend.budget_pct < 80 else "yellow" if spend.budget_pct < 95 else "red"
        table.add_row(
            p.id,
            p.name,
            f"${p.budget_monthly:.2f}",
            str(len(agents)),
            f"${spend.total_cost:.2f}",
            f"[{pct_style}]{spend.budget_pct:.1f}%[/{pct_style}]",
        )

    console.print(table)


@app.command()
def spend(
    project_id: str = typer.Argument(None, help="Project ID (uses first if omitted)"),
    period: str = typer.Option("month", help="today, week, or month"),
):
    """Show spend dashboard."""
    projs = list_projects()
    if not projs:
        console.print("[dim]No projects yet.[/dim]")
        return

    pid = project_id or projs[0].id
    s = compute_spend(pid, period=period)

    console.print(Panel(
        f"Period: [cyan]{s.period}[/cyan]\n"
        f"Total Cost: [bold]${s.total_cost:.4f}[/bold]\n"
        f"Total Calls: {s.total_calls}\n"
        f"Burn Rate: ${s.burn_rate_daily:.4f}/day\n"
        f"Projected Monthly: ${s.projected_monthly:.2f}\n"
        f"Budget: ${s.budget_monthly:.2f} ([{'green' if s.budget_pct < 80 else 'red'}]{s.budget_pct:.1f}%[/])",
        title=f"Spend — {pid}",
    ))

    if s.by_provider:
        table = Table(title="By Provider")
        table.add_column("Provider")
        table.add_column("Cost", justify="right")
        for k, v in sorted(s.by_provider.items(), key=lambda x: -x[1]):
            table.add_row(k, f"${v:.4f}")
        console.print(table)

    if s.by_model:
        table = Table(title="By Model")
        table.add_column("Model")
        table.add_column("Cost", justify="right")
        for k, v in sorted(s.by_model.items(), key=lambda x: -x[1]):
            table.add_row(k, f"${v:.4f}")
        console.print(table)


@app.command()
def alerts(
    project_id: str = typer.Argument(None, help="Project ID"),
):
    """Show active alerts."""
    projs = list_projects()
    if not projs:
        console.print("[dim]No projects yet.[/dim]")
        return

    pid = project_id or projs[0].id
    active = get_alerts(pid, resolved=False)

    if not active:
        console.print("[green]No active alerts.[/green]")
        return

    table = Table(title="Active Alerts")
    table.add_column("Level")
    table.add_column("Type")
    table.add_column("Message")
    table.add_column("Time")

    for a in active[-50:]:
        level_style = {"critical": "bold red", "warning": "yellow", "info": "blue"}.get(a.level.value, "")
        table.add_row(
            f"[{level_style}]{a.level.value.upper()}[/{level_style}]",
            a.alert_type.value,
            a.message,
            str(a.created_at)[:19],
        )
    console.print(table)


@app.command()
def agents(
    project_id: str = typer.Argument(None, help="Project ID"),
):
    """List monitored agents."""
    projs = list_projects()
    if not projs:
        console.print("[dim]No projects yet.[/dim]")
        return

    pid = project_id or projs[0].id
    agts = list_agents(pid)

    if not agts:
        console.print("[dim]No agents registered yet. Send your first API call to auto-register.[/dim]")
        return

    table = Table(title="Agents")
    table.add_column("ID", style="cyan")
    table.add_column("Name")
    table.add_column("Framework")
    table.add_column("Circuit")
    table.add_column("Last Seen")

    for a in agts:
        circuit_style = {"closed": "green", "open": "bold red", "half_open": "yellow"}.get(a.circuit.value, "")
        table.add_row(
            a.id,
            a.name,
            a.framework,
            f"[{circuit_style}]{a.circuit.value.upper()}[/{circuit_style}]",
            str(a.last_seen)[:19] if a.last_seen else "-",
        )
    console.print(table)


@app.command()
def predict(
    project_id: str = typer.Argument(None, help="Project ID"),
):
    """AI-powered cost prediction and optimization suggestions."""
    from .predictor import predict_costs

    projs = list_projects()
    if not projs:
        console.print("[dim]No projects yet.[/dim]")
        return

    pid = project_id or projs[0].id
    console.print("[dim]Analyzing cost patterns with Claude...[/dim]")

    result = predict_costs(pid)

    risk_style = {"low": "green", "medium": "yellow", "high": "bold red"}.get(result.get("risk_level", ""), "")
    conf_style = {"low": "red", "medium": "yellow", "high": "green"}.get(result.get("confidence", ""), "")

    console.print(Panel(
        f"[bold]Predicted Cost:[/bold] ${result.get('predicted_cost', 0):.2f}/month "
        f"([{conf_style}]{result.get('confidence', 'unknown')} confidence[/{conf_style}])\n"
        f"[bold]Risk Level:[/bold] [{risk_style}]{result.get('risk_level', 'unknown').upper()}[/{risk_style}]\n\n"
        f"{result.get('summary', '')}",
        title="Cost Prediction",
    ))

    optimizations = result.get("optimizations", [])
    if optimizations:
        table = Table(title="Optimization Recommendations")
        table.add_column("#", justify="right", width=3)
        table.add_column("Action")
        table.add_column("Savings", justify="right")
        table.add_column("Effort")
        for i, opt in enumerate(optimizations, 1):
            table.add_row(
                str(i),
                opt.get("action", ""),
                f"${opt.get('estimated_savings', 0):.2f}",
                opt.get("effort", ""),
            )
        console.print(table)

    risks = result.get("risk_factors", [])
    if risks:
        console.print("\n[bold]Risk Factors:[/bold]")
        for r in risks:
            console.print(f"  • {r}")


@app.command()
def demo():
    """Generate realistic demo data for testing."""
    import random
    from datetime import datetime, timedelta, timezone
    from .models import Agent, ApiCall, Project, Provider
    from .store import save_agent, save_call, save_project

    console.print("[dim]Generating demo data...[/dim]")

    # Create demo project
    project = Project(name="AI Startup Demo", budget_monthly=500.0, hard_limit=600.0)
    save_project(project)

    # Create agents
    agents_def = [
        ("research-agent", "langchain", [Provider.OPENAI, Provider.ANTHROPIC]),
        ("customer-support", "crewai", [Provider.OPENAI]),
        ("code-reviewer", "custom", [Provider.ANTHROPIC]),
        ("data-analyst", "autogen", [Provider.OPENAI, Provider.GOOGLE]),
        ("content-writer", "langchain", [Provider.ANTHROPIC]),
    ]

    agents = []
    for name, framework, providers in agents_def:
        agent = Agent(project_id=project.id, name=name, framework=framework, providers=providers)
        save_agent(agent)
        agents.append(agent)

    # Generate 30 days of API calls
    now = datetime.now(timezone.utc)
    models_by_provider = {
        Provider.OPENAI: ["gpt-4o", "gpt-4o-mini", "o3-mini"],
        Provider.ANTHROPIC: ["claude-sonnet-4", "claude-haiku-3.5"],
        Provider.GOOGLE: ["gemini-2.5-flash", "gemini-2.0-flash"],
    }

    from .pricing import estimate_cost

    total_calls = 0
    total_cost = 0.0

    for day in range(30):
        ts = now - timedelta(days=30 - day)
        # More calls on weekdays
        daily_calls = random.randint(50, 200) if day % 7 < 5 else random.randint(10, 50)

        for _ in range(daily_calls):
            agent = random.choice(agents)
            provider = random.choice(agent.providers)
            models = models_by_provider.get(provider, ["gpt-4o"])
            model = random.choice(models)

            tokens_in = random.randint(200, 8000)
            tokens_out = random.randint(50, 4000)
            cost = estimate_cost(model, tokens_in, tokens_out)

            call = ApiCall(
                project_id=project.id,
                agent_id=agent.id,
                provider=provider,
                model=model,
                tokens_in=tokens_in,
                tokens_out=tokens_out,
                cost=cost,
                latency_ms=random.randint(200, 5000),
                cached=random.random() < 0.15,
                timestamp=ts + timedelta(
                    hours=random.randint(8, 22),
                    minutes=random.randint(0, 59),
                ),
            )
            save_call(call)
            total_calls += 1
            total_cost += cost

    console.print(Panel(
        f"[bold green]Demo data generated![/bold green]\n\n"
        f"Project: [cyan]{project.name}[/cyan] ({project.id})\n"
        f"API Key: [bold yellow]{project.api_key}[/bold yellow]\n"
        f"Agents:  {len(agents)}\n"
        f"Calls:   {total_calls:,}\n"
        f"Cost:    ${total_cost:.2f}\n\n"
        f"Try: [bold]costguard status[/bold], [bold]costguard spend[/bold], [bold]costguard agents[/bold]",
        title="Demo Setup",
    ))


@app.command()
def status():
    """Quick status overview."""
    projs = list_projects()
    if not projs:
        console.print(Panel(
            "[dim]No projects yet. Run [bold]costguard init[/bold] to get started.[/dim]",
            title="Cost Guard",
        ))
        return

    for p in projs:
        agts = list_agents(p.id)
        s = compute_spend(p.id)
        active_alerts = get_alerts(p.id, resolved=False)
        open_circuits = [a for a in agts if a.circuit.value == "open"]

        pct_style = "green" if s.budget_pct < 80 else "yellow" if s.budget_pct < 95 else "bold red"
        circuit_msg = f"[bold red]{len(open_circuits)} OPEN[/bold red]" if open_circuits else "[green]All closed[/green]"

        console.print(Panel(
            f"Agents: {len(agts)}  |  Calls (month): {s.total_calls}  |  "
            f"Spend: [bold]${s.total_cost:.2f}[/bold] ([{pct_style}]{s.budget_pct:.1f}%[/{pct_style}])\n"
            f"Burn rate: ${s.burn_rate_daily:.2f}/day  |  Projected: ${s.projected_monthly:.2f}/month\n"
            f"Circuits: {circuit_msg}  |  Alerts: {len(active_alerts)} active",
            title=f"[bold]{p.name}[/bold] ({p.id})",
        ))
