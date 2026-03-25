"""Stripe billing integration for Cost Guard SaaS tiers."""

from __future__ import annotations

import os
from dataclasses import dataclass
from enum import Enum

STRIPE_KEY = os.getenv("STRIPE_SECRET_KEY", "")


class Plan(str, Enum):
    STARTER = "starter"   # $29/mo — 10 agents, 100k calls/mo
    PRO = "pro"           # $79/mo — 50 agents, 1M calls/mo
    BUSINESS = "business"  # $199/mo — unlimited agents, 10M calls/mo


@dataclass(frozen=True)
class PlanLimits:
    max_agents: int
    max_calls_monthly: int
    max_webhooks: int
    predictions_enabled: bool
    priority_support: bool
    price_monthly: float


PLAN_LIMITS: dict[Plan, PlanLimits] = {
    Plan.STARTER: PlanLimits(
        max_agents=10,
        max_calls_monthly=100_000,
        max_webhooks=2,
        predictions_enabled=False,
        priority_support=False,
        price_monthly=29.0,
    ),
    Plan.PRO: PlanLimits(
        max_agents=50,
        max_calls_monthly=1_000_000,
        max_webhooks=10,
        predictions_enabled=True,
        priority_support=False,
        price_monthly=79.0,
    ),
    Plan.BUSINESS: PlanLimits(
        max_agents=999999,
        max_calls_monthly=10_000_000,
        max_webhooks=50,
        predictions_enabled=True,
        priority_support=True,
        price_monthly=199.0,
    ),
}


def check_plan_limits(plan: Plan, current_agents: int, current_calls: int) -> dict:
    """Check if usage is within plan limits."""
    limits = PLAN_LIMITS[plan]
    return {
        "agents": {
            "current": current_agents,
            "limit": limits.max_agents,
            "ok": current_agents < limits.max_agents,
        },
        "calls": {
            "current": current_calls,
            "limit": limits.max_calls_monthly,
            "ok": current_calls < limits.max_calls_monthly,
            "pct": round(current_calls / limits.max_calls_monthly * 100, 1),
        },
        "plan": plan.value,
        "price": limits.price_monthly,
    }


def create_checkout_session(plan: Plan, project_id: str, success_url: str, cancel_url: str) -> dict:
    """Create a Stripe checkout session for plan subscription."""
    if not STRIPE_KEY:
        return {"error": "Stripe not configured", "plan": plan.value, "price": PLAN_LIMITS[plan].price_monthly}

    import stripe
    stripe.api_key = STRIPE_KEY

    # Price IDs would be created in Stripe dashboard
    price_ids = {
        Plan.STARTER: os.getenv("STRIPE_PRICE_STARTER", "price_starter"),
        Plan.PRO: os.getenv("STRIPE_PRICE_PRO", "price_pro"),
        Plan.BUSINESS: os.getenv("STRIPE_PRICE_BUSINESS", "price_business"),
    }

    session = stripe.checkout.Session.create(
        mode="subscription",
        line_items=[{"price": price_ids[plan], "quantity": 1}],
        success_url=success_url,
        cancel_url=cancel_url,
        metadata={"project_id": project_id},
    )

    return {"checkout_url": session.url, "session_id": session.id}
