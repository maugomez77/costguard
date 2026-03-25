"""AI-powered cost prediction and optimization recommendations."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone

from anthropic import Anthropic

from .models import SpendSummary
from .store import compute_spend, get_calls, list_agents


def predict_costs(project_id: str) -> dict:
    """Use Claude to predict next month's costs and suggest optimizations."""
    spend = compute_spend(project_id, period="month")
    agents = list_agents(project_id)
    calls = get_calls(project_id)

    # Build context for Claude
    recent_calls = calls[-200:]  # Last 200 calls for pattern analysis
    model_usage: dict[str, dict] = {}
    for c in recent_calls:
        if c.model not in model_usage:
            model_usage[c.model] = {"calls": 0, "cost": 0.0, "avg_tokens": 0}
        model_usage[c.model]["calls"] += 1
        model_usage[c.model]["cost"] += c.cost
        model_usage[c.model]["avg_tokens"] += c.tokens_in + c.tokens_out
    for m in model_usage:
        if model_usage[m]["calls"] > 0:
            model_usage[m]["avg_tokens"] //= model_usage[m]["calls"]

    context = {
        "current_month_spend": spend.total_cost,
        "total_calls": spend.total_calls,
        "burn_rate_daily": spend.burn_rate_daily,
        "budget_monthly": spend.budget_monthly,
        "budget_pct": spend.budget_pct,
        "projected_monthly": spend.projected_monthly,
        "by_provider": spend.by_provider,
        "by_model": spend.by_model,
        "model_usage_patterns": model_usage,
        "num_agents": len(agents),
        "agent_names": [a.name for a in agents],
    }

    client = Anthropic()
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2000,
        messages=[{
            "role": "user",
            "content": f"""Analyze this AI agent cost data and provide:
1. Predicted cost for next month (with confidence level)
2. Top 3 cost optimization recommendations
3. Risk assessment (likelihood of budget overrun)

Data: {json.dumps(context, indent=2)}

Respond in JSON format:
{{
    "predicted_cost": float,
    "confidence": "low" | "medium" | "high",
    "optimizations": [
        {{"action": str, "estimated_savings": float, "effort": "low" | "medium" | "high"}}
    ],
    "risk_level": "low" | "medium" | "high",
    "risk_factors": [str],
    "summary": str
}}"""
        }],
    )

    try:
        text = response.content[0].text
        # Extract JSON from response
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0]
        elif "```" in text:
            text = text.split("```")[1].split("```")[0]
        return json.loads(text)
    except (json.JSONDecodeError, IndexError):
        return {
            "predicted_cost": spend.projected_monthly,
            "confidence": "low",
            "optimizations": [],
            "risk_level": "medium" if spend.budget_pct > 50 else "low",
            "risk_factors": [],
            "summary": f"Based on current burn rate of ${spend.burn_rate_daily:.2f}/day, projected monthly cost is ${spend.projected_monthly:.2f}.",
        }


def detect_zombie_agents(project_id: str, hours_threshold: int = 24) -> list[dict]:
    """Detect agents that are running up costs without producing results."""
    agents = list_agents(project_id)
    now = datetime.now(timezone.utc)
    zombies = []

    for agent in agents:
        if not agent.last_seen:
            continue

        calls = get_calls(project_id, agent_id=agent.id)
        if len(calls) < 10:
            continue

        recent = [c for c in calls if (now - c.timestamp).total_seconds() < hours_threshold * 3600]

        if not recent:
            continue

        # High call volume but repetitive patterns = zombie
        models_used = set(c.model for c in recent)
        total_cost = sum(c.cost for c in recent)
        avg_tokens = sum(c.tokens_out for c in recent) / len(recent)

        # Heuristic: lots of calls with very low output tokens = stuck in a loop
        if len(recent) > 50 and avg_tokens < 50:
            zombies.append({
                "agent_id": agent.id,
                "agent_name": agent.name,
                "calls_last_24h": len(recent),
                "cost_last_24h": round(total_cost, 4),
                "avg_output_tokens": round(avg_tokens, 1),
                "reason": "High call volume with minimal output — possible stuck loop",
            })

    return zombies
