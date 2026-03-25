"""Persistence layer for Cost Guard."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from .models import Agent, Alert, ApiCall, Project, SpendSummary

STORE_DIR = Path.home() / ".costguard"
STORE_FILE = STORE_DIR / "store.json"


def _load() -> dict:
    if not STORE_FILE.exists():
        return {"projects": [], "agents": [], "calls": [], "alerts": []}
    return json.loads(STORE_FILE.read_text())


def _save(data: dict) -> None:
    STORE_DIR.mkdir(parents=True, exist_ok=True)
    STORE_FILE.write_text(json.dumps(data, default=str, indent=2))


# --- Projects ---

def save_project(project: Project) -> None:
    data = _load()
    data["projects"] = [p for p in data["projects"] if p["id"] != project.id]
    data["projects"].append(project.model_dump(mode="json"))
    _save(data)


def get_project(project_id: str) -> Project | None:
    data = _load()
    for p in data["projects"]:
        if p["id"] == project_id:
            return Project(**p)
    return None


def get_project_by_api_key(api_key: str) -> Project | None:
    data = _load()
    for p in data["projects"]:
        if p["api_key"] == api_key:
            return Project(**p)
    return None


def list_projects() -> list[Project]:
    data = _load()
    return [Project(**p) for p in data["projects"]]


# --- Agents ---

def save_agent(agent: Agent) -> None:
    data = _load()
    data["agents"] = [a for a in data["agents"] if a["id"] != agent.id]
    data["agents"].append(agent.model_dump(mode="json"))
    _save(data)


def get_agent(agent_id: str) -> Agent | None:
    data = _load()
    for a in data["agents"]:
        if a["id"] == agent_id:
            return Agent(**a)
    return None


def get_agent_by_name(project_id: str, name: str) -> Agent | None:
    data = _load()
    for a in data["agents"]:
        if a["project_id"] == project_id and a["name"] == name:
            return Agent(**a)
    return None


def list_agents(project_id: str) -> list[Agent]:
    data = _load()
    return [Agent(**a) for a in data["agents"] if a["project_id"] == project_id]


# --- API Calls ---

def save_call(call: ApiCall) -> None:
    data = _load()
    data["calls"].append(call.model_dump(mode="json"))
    # Keep last 50k calls
    if len(data["calls"]) > 50000:
        data["calls"] = data["calls"][-50000:]
    _save(data)


def get_calls(
    project_id: str,
    agent_id: str | None = None,
    since: datetime | None = None,
) -> list[ApiCall]:
    data = _load()
    calls = []
    for c in data["calls"]:
        if c["project_id"] != project_id:
            continue
        if agent_id and c["agent_id"] != agent_id:
            continue
        call = ApiCall(**c)
        if since and call.timestamp < since:
            continue
        calls.append(call)
    return calls


# --- Alerts ---

def save_alert(alert: Alert) -> None:
    data = _load()
    data["alerts"].append(alert.model_dump(mode="json"))
    if len(data["alerts"]) > 10000:
        data["alerts"] = data["alerts"][-10000:]
    _save(data)


def get_alerts(project_id: str, agent_id: str | None = None, resolved: bool | None = None) -> list[Alert]:
    data = _load()
    alerts = []
    for a in data["alerts"]:
        if a["project_id"] != project_id:
            continue
        if agent_id and a.get("agent_id") != agent_id:
            continue
        if resolved is not None and a.get("resolved") != resolved:
            continue
        alerts.append(Alert(**a))
    return alerts


# --- Spend Summary ---

def compute_spend(
    project_id: str,
    period: str = "month",
    agent_id: str | None = None,
) -> SpendSummary:
    now = datetime.now(timezone.utc)
    if period == "today":
        since = now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif period == "week":
        since = now - timedelta(days=7)
    else:
        since = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    calls = get_calls(project_id, agent_id=agent_id, since=since)
    project = get_project(project_id)
    budget = project.budget_monthly if project else 500.0

    total_cost = sum(c.cost for c in calls)
    by_provider: dict[str, float] = {}
    by_model: dict[str, float] = {}
    by_agent: dict[str, float] = {}

    for c in calls:
        by_provider[c.provider.value] = by_provider.get(c.provider.value, 0) + c.cost
        by_model[c.model] = by_model.get(c.model, 0) + c.cost
        by_agent[c.agent_id] = by_agent.get(c.agent_id, 0) + c.cost

    days_elapsed = max((now - since).days, 1)
    burn_rate = total_cost / days_elapsed
    days_in_month = 30
    projected = burn_rate * days_in_month

    return SpendSummary(
        project_id=project_id,
        period=period,
        total_cost=round(total_cost, 4),
        total_calls=len(calls),
        burn_rate_daily=round(burn_rate, 4),
        by_provider=by_provider,
        by_model=by_model,
        by_agent=by_agent,
        budget_monthly=budget,
        budget_pct=round((total_cost / budget) * 100, 1) if budget > 0 else 0,
        projected_monthly=round(projected, 2),
    )
