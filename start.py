"""Startup script: seed demo data if store is empty, then launch uvicorn."""

import os
import json
from pathlib import Path

STORE_FILE = Path.home() / ".costguard" / "store.json"

def seed_if_empty():
    """Seed demo data on first run so the app has real working data."""
    if STORE_FILE.exists():
        data = json.loads(STORE_FILE.read_text())
        if data.get("projects"):
            print(f"[startup] Store exists with {len(data['projects'])} projects — skipping seed")
            return

    print("[startup] No data found — seeding demo data...")
    from costguard.models import Agent, ApiCall, Project, Provider
    from costguard.store import save_agent, save_call, save_project
    from costguard.pricing import estimate_cost
    from datetime import datetime, timedelta, timezone
    import random

    # Use a fixed API key for the demo so the frontend can connect
    DEMO_API_KEY = os.environ.get("DEMO_API_KEY", "cg_demo_costguard_2026")

    project = Project(
        name="AI Startup Demo",
        api_key=DEMO_API_KEY,
        budget_monthly=1500.0,
        hard_limit=2000.0,
    )
    save_project(project)

    agents_def = [
        ("research-agent", "langchain", [Provider.OPENAI, Provider.ANTHROPIC]),
        ("customer-support", "crewai", [Provider.OPENAI]),
        ("code-reviewer", "custom", [Provider.ANTHROPIC]),
        ("data-analyst", "autogen", [Provider.OPENAI, Provider.GOOGLE]),
        ("content-writer", "langchain", [Provider.ANTHROPIC]),
        ("sales-copilot", "langchain", [Provider.OPENAI]),
        ("devops-monitor", "custom", [Provider.ANTHROPIC, Provider.DEEPSEEK]),
    ]

    agents = []
    for name, framework, providers in agents_def:
        agent = Agent(project_id=project.id, name=name, framework=framework, providers=providers)
        save_agent(agent)
        agents.append(agent)

    now = datetime.now(timezone.utc)
    models_by_provider = {
        Provider.OPENAI: ["gpt-4o", "gpt-4o-mini", "o3-mini"],
        Provider.ANTHROPIC: ["claude-sonnet-4", "claude-haiku-3.5"],
        Provider.GOOGLE: ["gemini-2.5-flash", "gemini-2.0-flash"],
        Provider.DEEPSEEK: ["deepseek-v3"],
    }

    total_calls = 0
    total_cost = 0.0

    for day in range(30):
        ts = now - timedelta(days=30 - day)
        daily_calls = random.randint(80, 300) if day % 7 < 5 else random.randint(20, 80)

        for _ in range(daily_calls):
            agent = random.choice(agents)
            provider = random.choice(agent.providers)
            models = models_by_provider.get(provider, ["gpt-4o"])
            model = random.choice(models)

            tokens_in = random.randint(200, 12000)
            tokens_out = random.randint(50, 6000)
            cost = estimate_cost(model, tokens_in, tokens_out)

            call = ApiCall(
                project_id=project.id,
                agent_id=agent.id,
                provider=provider,
                model=model,
                tokens_in=tokens_in,
                tokens_out=tokens_out,
                cost=cost,
                latency_ms=random.randint(150, 8000),
                cached=random.random() < 0.12,
                timestamp=ts + timedelta(
                    hours=random.randint(6, 23),
                    minutes=random.randint(0, 59),
                ),
            )
            save_call(call)
            total_calls += 1
            total_cost += cost

    print(f"[startup] Seeded: {len(agents)} agents, {total_calls:,} calls, ${total_cost:.2f} total cost")
    print(f"[startup] Demo API key: {DEMO_API_KEY}")
    print(f"[startup] Project ID: {project.id}")


if __name__ == "__main__":
    seed_if_empty()

    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("costguard.api:app", host="0.0.0.0", port=port)
