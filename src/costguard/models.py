"""Data models for Cost Guard."""

from __future__ import annotations

import hashlib
import time
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


def _make_id(prefix: str) -> str:
    ts = int(time.time())
    h = hashlib.md5(f"{ts}{time.monotonic_ns()}".encode()).hexdigest()[:8]
    return f"{prefix}-{ts}-{h}"


# --- Enums ---

class Provider(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    AWS = "aws"
    DEEPSEEK = "deepseek"
    GROQ = "groq"
    CUSTOM = "custom"


class AlertLevel(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class AlertType(str, Enum):
    BUDGET_80 = "budget_80"
    BUDGET_90 = "budget_90"
    BUDGET_100 = "budget_100"
    COST_SPIKE = "cost_spike"
    VOLUME_SPIKE = "volume_spike"
    CIRCUIT_OPEN = "circuit_open"
    ZOMBIE_AGENT = "zombie_agent"


class CircuitState(str, Enum):
    CLOSED = "closed"       # Normal: requests flow through
    OPEN = "open"           # Tripped: requests blocked
    HALF_OPEN = "half_open" # Testing: limited requests allowed


class WebhookEvent(str, Enum):
    ALERT = "alert"
    CIRCUIT_OPEN = "circuit_open"
    CIRCUIT_CLOSE = "circuit_close"
    BUDGET_EXCEEDED = "budget_exceeded"
    COST_SPIKE = "cost_spike"
    DAILY_SUMMARY = "daily_summary"


# --- Core Models ---

class Project(BaseModel):
    id: str = Field(default_factory=lambda: _make_id("proj"))
    name: str
    api_key: str = Field(default_factory=lambda: f"cg_{hashlib.md5(f'{time.time()}{time.monotonic_ns()}'.encode()).hexdigest()}")
    budget_monthly: float = 500.0
    budget_daily: Optional[float] = None
    hard_limit: Optional[float] = None  # Absolute max — circuit opens here
    webhook_url: Optional[str] = None
    webhook_events: list[WebhookEvent] = Field(default_factory=lambda: list(WebhookEvent))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Agent(BaseModel):
    id: str = Field(default_factory=lambda: _make_id("agent"))
    project_id: str
    name: str
    framework: str = "custom"  # langchain, crewai, autogen, custom
    providers: list[Provider] = Field(default_factory=list)
    budget_monthly: Optional[float] = None  # Per-agent override
    circuit: CircuitState = CircuitState.CLOSED
    circuit_opened_at: Optional[datetime] = None
    circuit_reason: Optional[str] = None
    last_seen: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ApiCall(BaseModel):
    id: str = Field(default_factory=lambda: _make_id("call"))
    project_id: str
    agent_id: str
    provider: Provider
    model: str
    tokens_in: int = 0
    tokens_out: int = 0
    cost: float = 0.0
    latency_ms: int = 0
    cached: bool = False
    metadata: dict = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Alert(BaseModel):
    id: str = Field(default_factory=lambda: _make_id("alert"))
    project_id: str
    agent_id: Optional[str] = None
    alert_type: AlertType
    level: AlertLevel
    message: str
    resolved: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class WebhookConfig(BaseModel):
    url: str
    events: list[WebhookEvent] = Field(default_factory=lambda: list(WebhookEvent))
    secret: Optional[str] = None  # For HMAC signature verification


# --- API Request/Response ---

class IngestRequest(BaseModel):
    agent_name: str
    provider: Provider
    model: str
    tokens_in: int = 0
    tokens_out: int = 0
    cost: Optional[float] = None  # Auto-calculated if omitted
    latency_ms: int = 0
    cached: bool = False
    metadata: dict = Field(default_factory=dict)


class IngestResponse(BaseModel):
    call_id: str
    cost: float
    circuit_state: CircuitState
    budget_pct: float
    alerts: list[Alert] = Field(default_factory=list)


class SpendSummary(BaseModel):
    project_id: str
    period: str
    total_cost: float
    total_calls: int
    burn_rate_daily: float
    by_provider: dict[str, float] = Field(default_factory=dict)
    by_model: dict[str, float] = Field(default_factory=dict)
    by_agent: dict[str, float] = Field(default_factory=dict)
    budget_monthly: float
    budget_pct: float
    projected_monthly: float


class CircuitAction(BaseModel):
    action: str  # open, close, half_open
    reason: Optional[str] = None
