"""Cost Guard SDK — drop-in monitoring for AI agent API calls.

Usage (5-minute setup):

    from costguard.sdk import CostGuard

    guard = CostGuard(api_key="cg_...", base_url="http://localhost:8000")

    # Wrap your OpenAI/Anthropic client
    guard.wrap_openai(openai_client)
    guard.wrap_anthropic(anthropic_client)

    # Or manually log calls
    result = guard.log(
        agent_name="my-agent",
        provider="openai",
        model="gpt-4o",
        tokens_in=500,
        tokens_out=200,
    )
    if result.circuit_state == "open":
        print("BLOCKED — circuit breaker tripped!")
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

import httpx

logger = logging.getLogger("costguard.sdk")


@dataclass
class LogResult:
    call_id: str
    cost: float
    circuit_state: str
    budget_pct: float
    alerts: list[dict]
    blocked: bool


class CostGuardError(Exception):
    pass


class CircuitOpenError(CostGuardError):
    """Raised when the circuit breaker is open and the call should be blocked."""


class CostGuard:
    """Cost Guard SDK client."""

    def __init__(
        self,
        api_key: str,
        base_url: str = "http://localhost:8000",
        agent_name: str = "default",
        block_on_open: bool = True,
        timeout: float = 2.0,
    ):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.agent_name = agent_name
        self.block_on_open = block_on_open
        self._client = httpx.Client(
            base_url=self.base_url,
            headers={"X-API-Key": api_key},
            timeout=timeout,
        )

    def log(
        self,
        agent_name: str | None = None,
        provider: str = "openai",
        model: str = "gpt-4o",
        tokens_in: int = 0,
        tokens_out: int = 0,
        cost: float | None = None,
        latency_ms: int = 0,
        cached: bool = False,
        metadata: dict | None = None,
    ) -> LogResult:
        """Log an API call to Cost Guard."""
        payload = {
            "agent_name": agent_name or self.agent_name,
            "provider": provider,
            "model": model,
            "tokens_in": tokens_in,
            "tokens_out": tokens_out,
            "latency_ms": latency_ms,
            "cached": cached,
            "metadata": metadata or {},
        }
        if cost is not None:
            payload["cost"] = cost

        try:
            resp = self._client.post("/v1/ingest", json=payload)
            resp.raise_for_status()
            data = resp.json()
        except httpx.HTTPStatusError as e:
            logger.warning(f"Cost Guard API error: {e.response.status_code}")
            # Fail open — don't block the caller's work
            return LogResult(
                call_id="error",
                cost=0.0,
                circuit_state="unknown",
                budget_pct=0.0,
                alerts=[],
                blocked=False,
            )
        except Exception as e:
            logger.warning(f"Cost Guard unreachable: {e}")
            return LogResult(
                call_id="error",
                cost=0.0,
                circuit_state="unknown",
                budget_pct=0.0,
                alerts=[],
                blocked=False,
            )

        result = LogResult(
            call_id=data["call_id"],
            cost=data["cost"],
            circuit_state=data["circuit_state"],
            budget_pct=data["budget_pct"],
            alerts=data.get("alerts", []),
            blocked=data["circuit_state"] == "open",
        )

        if result.blocked and self.block_on_open:
            raise CircuitOpenError(
                f"Circuit breaker is OPEN for agent '{agent_name or self.agent_name}'. "
                f"Budget at {result.budget_pct:.1f}%."
            )

        return result

    def get_spend(self, period: str = "month") -> dict:
        """Get spend summary."""
        resp = self._client.get("/v1/spend", params={"period": period})
        resp.raise_for_status()
        return resp.json()

    def get_alerts(self) -> list[dict]:
        """Get active alerts."""
        resp = self._client.get("/v1/alerts", params={"resolved": False})
        resp.raise_for_status()
        return resp.json().get("alerts", [])

    def open_circuit(self, agent_id: str, reason: str = "Manual") -> dict:
        """Emergency: open circuit breaker for an agent."""
        resp = self._client.post(
            f"/v1/agents/{agent_id}/circuit",
            json={"action": "open", "reason": reason},
        )
        resp.raise_for_status()
        return resp.json()

    def close_circuit(self, agent_id: str) -> dict:
        """Reset circuit breaker for an agent."""
        resp = self._client.post(
            f"/v1/agents/{agent_id}/circuit",
            json={"action": "close"},
        )
        resp.raise_for_status()
        return resp.json()

    # --- Framework Wrappers ---

    def wrap_openai(self, client: Any) -> Any:
        """Monkey-patch an OpenAI client to auto-log calls.

        Usage:
            from openai import OpenAI
            client = OpenAI()
            guard.wrap_openai(client)
            # All chat completions now auto-logged to Cost Guard
        """
        original_create = client.chat.completions.create

        def patched_create(*args: Any, **kwargs: Any) -> Any:
            import time
            start = time.monotonic()
            result = original_create(*args, **kwargs)
            elapsed = int((time.monotonic() - start) * 1000)

            model = kwargs.get("model", getattr(result, "model", "unknown"))
            usage = getattr(result, "usage", None)
            tokens_in = getattr(usage, "prompt_tokens", 0) if usage else 0
            tokens_out = getattr(usage, "completion_tokens", 0) if usage else 0

            self.log(
                provider="openai",
                model=model,
                tokens_in=tokens_in,
                tokens_out=tokens_out,
                latency_ms=elapsed,
            )
            return result

        client.chat.completions.create = patched_create
        return client

    def wrap_anthropic(self, client: Any) -> Any:
        """Monkey-patch an Anthropic client to auto-log calls.

        Usage:
            from anthropic import Anthropic
            client = Anthropic()
            guard.wrap_anthropic(client)
        """
        original_create = client.messages.create

        def patched_create(*args: Any, **kwargs: Any) -> Any:
            import time
            start = time.monotonic()
            result = original_create(*args, **kwargs)
            elapsed = int((time.monotonic() - start) * 1000)

            model = kwargs.get("model", getattr(result, "model", "unknown"))
            usage = getattr(result, "usage", None)
            tokens_in = getattr(usage, "input_tokens", 0) if usage else 0
            tokens_out = getattr(usage, "output_tokens", 0) if usage else 0

            self.log(
                provider="anthropic",
                model=model,
                tokens_in=tokens_in,
                tokens_out=tokens_out,
                latency_ms=elapsed,
            )
            return result

        client.messages.create = patched_create
        return client

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> CostGuard:
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()
