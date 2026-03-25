"""Core engine — ingestion, circuit breakers, alerting, webhooks."""

from __future__ import annotations

import hmac
import hashlib
import logging
from datetime import datetime, timedelta, timezone

import httpx

from .models import (
    Agent,
    Alert,
    AlertLevel,
    AlertType,
    ApiCall,
    CircuitState,
    IngestRequest,
    IngestResponse,
    Project,
    WebhookEvent,
)
from .pricing import estimate_cost
from .store import (
    compute_spend,
    get_agent,
    get_agent_by_name,
    get_calls,
    save_agent,
    save_alert,
    save_call,
)

logger = logging.getLogger("costguard")

# Thresholds
BUDGET_WARN = 0.80
BUDGET_CRITICAL = 0.90
BUDGET_HARD = 1.00
COST_SPIKE_MULTIPLIER = 3.0
VOLUME_SPIKE_MULTIPLIER = 5.0


def ingest(project: Project, req: IngestRequest) -> IngestResponse:
    """Process an incoming API call — the core hot path."""
    # Resolve or create agent
    agent = get_agent_by_name(project.id, req.agent_name)
    if not agent:
        agent = Agent(
            project_id=project.id,
            name=req.agent_name,
            providers=[req.provider],
        )
        save_agent(agent)

    # Check circuit breaker BEFORE processing
    if agent.circuit == CircuitState.OPEN:
        return IngestResponse(
            call_id="blocked",
            cost=0.0,
            circuit_state=CircuitState.OPEN,
            budget_pct=_budget_pct(project),
            alerts=[
                Alert(
                    project_id=project.id,
                    agent_id=agent.id,
                    alert_type=AlertType.CIRCUIT_OPEN,
                    level=AlertLevel.CRITICAL,
                    message=f"Circuit OPEN for agent '{agent.name}': {agent.circuit_reason}",
                )
            ],
        )

    # Estimate cost if not provided
    cost = req.cost if req.cost is not None else estimate_cost(req.model, req.tokens_in, req.tokens_out)

    # Save the call
    call = ApiCall(
        project_id=project.id,
        agent_id=agent.id,
        provider=req.provider,
        model=req.model,
        tokens_in=req.tokens_in,
        tokens_out=req.tokens_out,
        cost=cost,
        latency_ms=req.latency_ms,
        cached=req.cached,
        metadata=req.metadata,
    )
    save_call(call)

    # Update agent last_seen
    agent.last_seen = datetime.now(timezone.utc)
    if req.provider not in agent.providers:
        agent.providers.append(req.provider)
    save_agent(agent)

    # Check thresholds & generate alerts
    alerts = _check_thresholds(project, agent, call)

    budget_pct = _budget_pct(project)

    return IngestResponse(
        call_id=call.id,
        cost=cost,
        circuit_state=agent.circuit,
        budget_pct=budget_pct,
        alerts=alerts,
    )


def open_circuit(agent: Agent, reason: str) -> Agent:
    """Trip the circuit breaker for an agent."""
    agent.circuit = CircuitState.OPEN
    agent.circuit_opened_at = datetime.now(timezone.utc)
    agent.circuit_reason = reason
    save_agent(agent)
    return agent


def close_circuit(agent: Agent) -> Agent:
    """Reset circuit breaker to closed."""
    agent.circuit = CircuitState.CLOSED
    agent.circuit_opened_at = None
    agent.circuit_reason = None
    save_agent(agent)
    return agent


def _budget_pct(project: Project) -> float:
    spend = compute_spend(project.id, "month")
    return spend.budget_pct


def _check_thresholds(project: Project, agent: Agent, call: ApiCall) -> list[Alert]:
    """Check budget and anomaly thresholds, fire alerts + circuit breakers."""
    alerts: list[Alert] = []
    spend = compute_spend(project.id, "month")
    pct = spend.budget_pct / 100.0

    # Budget alerts
    if pct >= BUDGET_HARD:
        alert = Alert(
            project_id=project.id,
            agent_id=agent.id,
            alert_type=AlertType.BUDGET_100,
            level=AlertLevel.CRITICAL,
            message=f"Budget EXCEEDED: {spend.budget_pct:.1f}% of ${project.budget_monthly:.2f}",
        )
        alerts.append(alert)
        save_alert(alert)

        # Auto-open circuit if hard limit set
        if project.hard_limit and spend.total_cost >= project.hard_limit:
            open_circuit(agent, f"Hard limit ${project.hard_limit} exceeded")
            _fire_webhook(project, WebhookEvent.CIRCUIT_OPEN, {
                "agent": agent.name,
                "reason": f"Hard limit ${project.hard_limit} exceeded",
                "spend": spend.total_cost,
            })

    elif pct >= BUDGET_CRITICAL:
        alert = Alert(
            project_id=project.id,
            agent_id=agent.id,
            alert_type=AlertType.BUDGET_90,
            level=AlertLevel.CRITICAL,
            message=f"Budget at {spend.budget_pct:.1f}% — approaching limit",
        )
        alerts.append(alert)
        save_alert(alert)

    elif pct >= BUDGET_WARN:
        alert = Alert(
            project_id=project.id,
            agent_id=agent.id,
            alert_type=AlertType.BUDGET_80,
            level=AlertLevel.WARNING,
            message=f"Budget at {spend.budget_pct:.1f}%",
        )
        alerts.append(alert)
        save_alert(alert)

    # Cost spike detection (hourly)
    _check_cost_spike(project, agent, alerts)

    # Fire webhook for any alerts
    for alert in alerts:
        _fire_webhook(project, WebhookEvent.ALERT, {
            "alert_type": alert.alert_type.value,
            "level": alert.level.value,
            "message": alert.message,
            "agent": agent.name,
        })

    return alerts


def _check_cost_spike(project: Project, agent: Agent, alerts: list[Alert]) -> None:
    """Detect cost spikes in the last hour vs average."""
    now = datetime.now(timezone.utc)
    hour_ago = now - timedelta(hours=1)
    day_ago = now - timedelta(days=1)

    recent = get_calls(project.id, agent_id=agent.id, since=hour_ago)
    baseline = get_calls(project.id, agent_id=agent.id, since=day_ago)

    if len(baseline) < 10:
        return  # Not enough data

    recent_cost = sum(c.cost for c in recent)
    hours_baseline = max((now - day_ago).total_seconds() / 3600, 1)
    avg_hourly_cost = sum(c.cost for c in baseline) / hours_baseline

    if avg_hourly_cost > 0 and recent_cost > avg_hourly_cost * COST_SPIKE_MULTIPLIER:
        alert = Alert(
            project_id=project.id,
            agent_id=agent.id,
            alert_type=AlertType.COST_SPIKE,
            level=AlertLevel.CRITICAL,
            message=f"Cost spike: ${recent_cost:.4f}/hr vs ${avg_hourly_cost:.4f}/hr avg ({recent_cost/avg_hourly_cost:.1f}x)",
        )
        alerts.append(alert)
        save_alert(alert)

    # Volume spike
    recent_vol = len(recent)
    avg_hourly_vol = len(baseline) / hours_baseline

    if avg_hourly_vol > 0 and recent_vol > avg_hourly_vol * VOLUME_SPIKE_MULTIPLIER:
        alert = Alert(
            project_id=project.id,
            agent_id=agent.id,
            alert_type=AlertType.VOLUME_SPIKE,
            level=AlertLevel.WARNING,
            message=f"Volume spike: {recent_vol} calls/hr vs {avg_hourly_vol:.0f}/hr avg ({recent_vol/avg_hourly_vol:.1f}x)",
        )
        alerts.append(alert)
        save_alert(alert)


def _fire_webhook(project: Project, event: WebhookEvent, payload: dict) -> None:
    """Send webhook notification (fire-and-forget)."""
    if not project.webhook_url:
        return
    if event not in project.webhook_events:
        return

    body = {
        "event": event.value,
        "project_id": project.id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "data": payload,
    }

    try:
        headers = {"Content-Type": "application/json", "User-Agent": "CostGuard/0.1"}
        with httpx.Client(timeout=5.0) as client:
            client.post(project.webhook_url, json=body, headers=headers)
    except Exception as e:
        logger.warning(f"Webhook failed for {project.webhook_url}: {e}")
