"""Startup script: launch uvicorn immediately, seed in background thread."""

import os
import random
import threading
from datetime import datetime, timedelta, timezone


def seed_if_empty():
    """Seed demo data via the store layer (DB when DATABASE_URL is set, JSON file otherwise)."""
    from costguard.store import bulk_seed, has_any_projects

    if has_any_projects():
        print("[seed] Store already populated — skipping")
        return

    print("[seed] Seeding demo data...")

    from costguard.models import Agent, ApiCall, Project, Provider
    from costguard.pricing import estimate_cost

    DEMO_API_KEY = os.environ.get("DEMO_API_KEY", "cg_demo_costguard_2026")

    project = Project(name="AI Startup Demo", api_key=DEMO_API_KEY, budget_monthly=1500.0, hard_limit=2000.0)

    agents_def = [
        ("research-agent", "langchain", [Provider.OPENAI, Provider.ANTHROPIC]),
        ("customer-support", "crewai", [Provider.OPENAI]),
        ("code-reviewer", "custom", [Provider.ANTHROPIC]),
        ("data-analyst", "autogen", [Provider.OPENAI, Provider.GOOGLE]),
        ("content-writer", "langchain", [Provider.ANTHROPIC]),
        ("sales-copilot", "langchain", [Provider.OPENAI]),
        ("devops-monitor", "custom", [Provider.ANTHROPIC, Provider.DEEPSEEK]),
    ]

    agents = [
        Agent(project_id=project.id, name=name, framework=framework, providers=providers)
        for name, framework, providers in agents_def
    ]

    now = datetime.now(timezone.utc)
    mp = {
        Provider.OPENAI: ["gpt-4o", "gpt-4o-mini", "o3-mini"],
        Provider.ANTHROPIC: ["claude-sonnet-4", "claude-haiku-3.5"],
        Provider.GOOGLE: ["gemini-2.5-flash", "gemini-2.0-flash"],
        Provider.DEEPSEEK: ["deepseek-v3"],
    }

    calls = []
    for day in range(30):
        ts = now - timedelta(days=30 - day)
        n = random.randint(40, 150) if day % 7 < 5 else random.randint(10, 40)
        for _ in range(n):
            a = random.choice(agents)
            p = random.choice(a.providers)
            m = random.choice(mp.get(p, ["gpt-4o"]))
            ti, to = random.randint(200, 10000), random.randint(50, 5000)
            calls.append(ApiCall(
                project_id=project.id, agent_id=a.id, provider=p, model=m,
                tokens_in=ti, tokens_out=to, cost=estimate_cost(m, ti, to),
                latency_ms=random.randint(150, 6000), cached=random.random() < 0.12,
                timestamp=ts + timedelta(hours=random.randint(6, 23), minutes=random.randint(0, 59)),
            ))

    bulk_seed({
        "projects": [project.model_dump(mode="json")],
        "agents": [a.model_dump(mode="json") for a in agents],
        "calls": [c.model_dump(mode="json") for c in calls],
        "alerts": [],
    })

    print(f"[seed] Done: {len(agents)} agents, {len(calls)} calls")


if __name__ == "__main__":
    # Seed in background so uvicorn starts immediately
    t = threading.Thread(target=seed_if_empty, daemon=True)
    t.start()

    import uvicorn
    port = int(os.environ.get("PORT", 10000))
    print(f"[startup] Starting uvicorn on port {port}")
    uvicorn.run("costguard.api:app", host="0.0.0.0", port=port)
