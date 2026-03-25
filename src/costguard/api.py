"""FastAPI application — the webhook-ready API."""

from __future__ import annotations

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .engine import close_circuit, ingest, open_circuit
from .models import (
    Agent,
    CircuitAction,
    CircuitState,
    IngestRequest,
    IngestResponse,
    Project,
    SpendSummary,
    WebhookConfig,
)
from .store import (
    compute_spend,
    get_agent,
    get_alerts,
    get_project_by_api_key,
    list_agents,
    list_projects,
    save_project,
)

app = FastAPI(
    title="Cost Guard",
    description="Real-time cost monitoring and circuit breakers for AI agents",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

from .middleware import RateLimitMiddleware
app.add_middleware(RateLimitMiddleware)


# --- Auth dependency ---

def _get_project(x_api_key: str = Header(..., alias="X-API-Key")) -> Project:
    project = get_project_by_api_key(x_api_key)
    if not project:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return project


# --- Health ---

@app.get("/health")
def health():
    return {"status": "ok", "version": "0.1.0"}


# --- Ingest (the hot path — called by SDK on every API call) ---

@app.post("/v1/ingest", response_model=IngestResponse)
def ingest_call(req: IngestRequest, project: Project = Depends(_get_project)):
    """Log an API call and get real-time circuit breaker status."""
    return ingest(project, req)


# --- Spend Dashboard ---

@app.get("/v1/spend", response_model=SpendSummary)
def get_spend(
    period: str = "month",
    agent_id: str | None = None,
    project: Project = Depends(_get_project),
):
    return compute_spend(project.id, period=period, agent_id=agent_id)


# --- Agents ---

@app.get("/v1/agents")
def get_agents(project: Project = Depends(_get_project)):
    agents = list_agents(project.id)
    return {"agents": [a.model_dump(mode="json") for a in agents]}


@app.get("/v1/agents/{agent_id}")
def get_agent_detail(agent_id: str, project: Project = Depends(_get_project)):
    agent = get_agent(agent_id)
    if not agent or agent.project_id != project.id:
        raise HTTPException(status_code=404, detail="Agent not found")
    spend = compute_spend(project.id, agent_id=agent_id)
    return {"agent": agent.model_dump(mode="json"), "spend": spend.model_dump(mode="json")}


# --- Circuit Breaker ---

@app.post("/v1/agents/{agent_id}/circuit")
def circuit_action(agent_id: str, body: CircuitAction, project: Project = Depends(_get_project)):
    agent = get_agent(agent_id)
    if not agent or agent.project_id != project.id:
        raise HTTPException(status_code=404, detail="Agent not found")

    if body.action == "open":
        agent = open_circuit(agent, body.reason or "Manual circuit open")
    elif body.action == "close":
        agent = close_circuit(agent)
    elif body.action == "half_open":
        agent.circuit = CircuitState.HALF_OPEN
        from .store import save_agent
        save_agent(agent)
    else:
        raise HTTPException(status_code=400, detail=f"Unknown action: {body.action}")

    return {"agent_id": agent.id, "circuit": agent.circuit.value}


# --- Alerts ---

@app.get("/v1/alerts")
def get_project_alerts(
    agent_id: str | None = None,
    resolved: bool | None = None,
    project: Project = Depends(_get_project),
):
    alerts = get_alerts(project.id, agent_id=agent_id, resolved=resolved)
    return {"alerts": [a.model_dump(mode="json") for a in alerts[-100:]]}


# --- Webhook Config ---

@app.put("/v1/webhook")
def set_webhook(config: WebhookConfig, project: Project = Depends(_get_project)):
    project.webhook_url = config.url
    project.webhook_events = config.events
    save_project(project)
    return {"status": "ok", "webhook_url": config.url, "events": [e.value for e in config.events]}


# --- Project Setup ---

@app.post("/v1/projects")
def create_project(name: str, budget_monthly: float = 500.0, hard_limit: float | None = None):
    project = Project(name=name, budget_monthly=budget_monthly, hard_limit=hard_limit)
    save_project(project)
    return {
        "project_id": project.id,
        "api_key": project.api_key,
        "message": "Save your API key — it won't be shown again.",
    }


# --- AI Predictions ---

@app.get("/v1/predict")
def predict(project: Project = Depends(_get_project)):
    from .predictor import predict_costs
    return predict_costs(project.id)


@app.get("/v1/zombies")
def zombie_agents(project: Project = Depends(_get_project)):
    from .predictor import detect_zombie_agents
    return {"zombies": detect_zombie_agents(project.id)}


# --- Billing ---

@app.get("/v1/billing/plans")
def get_plans():
    from .billing import PLAN_LIMITS, Plan
    return {
        "plans": [
            {
                "name": plan.value,
                "price": limits.price_monthly,
                "max_agents": limits.max_agents,
                "max_calls_monthly": limits.max_calls_monthly,
                "predictions_enabled": limits.predictions_enabled,
            }
            for plan, limits in PLAN_LIMITS.items()
        ]
    }


@app.post("/v1/billing/checkout")
def checkout(plan: str, project: Project = Depends(_get_project)):
    from .billing import Plan, create_checkout_session
    try:
        p = Plan(plan)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Unknown plan: {plan}")
    return create_checkout_session(
        p, project.id,
        success_url="http://localhost:3000/billing/success",
        cancel_url="http://localhost:3000/billing/cancel",
    )


# --- API Key Rotation ---

@app.post("/v1/rotate-key")
def rotate_api_key(project: Project = Depends(_get_project)):
    import hashlib, time
    new_key = f"cg_{hashlib.md5(f'{time.time()}{time.monotonic_ns()}'.encode()).hexdigest()}"
    project.api_key = new_key
    save_project(project)
    return {"api_key": new_key, "message": "Old key is now invalid. Save your new key."}
