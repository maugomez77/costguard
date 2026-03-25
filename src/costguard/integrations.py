"""Pre-built framework integrations for LangChain, CrewAI, and AutoGen."""

from __future__ import annotations

import logging
from typing import Any

from .sdk import CostGuard

logger = logging.getLogger("costguard.integrations")


class LangChainCostGuard:
    """LangChain callback handler that auto-logs to Cost Guard.

    Usage:
        from costguard.integrations import LangChainCostGuard

        guard = LangChainCostGuard(api_key="cg_...", agent_name="my-chain")
        chain.invoke(input, config={"callbacks": [guard]})
    """

    def __init__(self, api_key: str, base_url: str = "http://localhost:8000", agent_name: str = "langchain"):
        self.guard = CostGuard(api_key=api_key, base_url=base_url, agent_name=agent_name, block_on_open=False)
        self._start_times: dict[str, float] = {}

    def on_llm_start(self, serialized: dict, prompts: list[str], *, run_id: Any, **kwargs: Any) -> None:
        import time
        self._start_times[str(run_id)] = time.monotonic()

    def on_llm_end(self, response: Any, *, run_id: Any, **kwargs: Any) -> None:
        import time
        elapsed = 0
        rid = str(run_id)
        if rid in self._start_times:
            elapsed = int((time.monotonic() - self._start_times.pop(rid)) * 1000)

        # Extract token usage from LangChain response
        llm_output = getattr(response, "llm_output", {}) or {}
        usage = llm_output.get("token_usage", {})
        model = llm_output.get("model_name", "unknown")

        # Detect provider from model name
        provider = "openai"
        if "claude" in model.lower():
            provider = "anthropic"
        elif "gemini" in model.lower():
            provider = "google"

        self.guard.log(
            provider=provider,
            model=model,
            tokens_in=usage.get("prompt_tokens", 0),
            tokens_out=usage.get("completion_tokens", 0),
            latency_ms=elapsed,
            metadata={"framework": "langchain"},
        )

    def on_llm_error(self, error: Exception, **kwargs: Any) -> None:
        pass


class CrewAICostGuard:
    """CrewAI step callback that auto-logs to Cost Guard.

    Usage:
        from costguard.integrations import CrewAICostGuard
        from crewai import Crew

        guard = CrewAICostGuard(api_key="cg_...", agent_name="my-crew")
        crew = Crew(agents=[...], tasks=[...], step_callback=guard.step_callback)
    """

    def __init__(self, api_key: str, base_url: str = "http://localhost:8000", agent_name: str = "crewai"):
        self.guard = CostGuard(api_key=api_key, base_url=base_url, agent_name=agent_name, block_on_open=False)

    def step_callback(self, step_output: Any) -> None:
        # CrewAI exposes token usage in step outputs
        usage = getattr(step_output, "token_usage", None)
        if not usage:
            return

        model = getattr(step_output, "model", "unknown")
        provider = "openai"
        if "claude" in str(model).lower():
            provider = "anthropic"

        self.guard.log(
            provider=provider,
            model=str(model),
            tokens_in=getattr(usage, "prompt_tokens", 0),
            tokens_out=getattr(usage, "completion_tokens", 0),
            metadata={"framework": "crewai", "agent": getattr(step_output, "agent", "unknown")},
        )


class AutoGenCostGuard:
    """AutoGen logging handler for Cost Guard.

    Usage:
        from costguard.integrations import AutoGenCostGuard

        guard = AutoGenCostGuard(api_key="cg_...", agent_name="my-autogen")

        # Register with AutoGen's logging
        import autogen
        autogen.runtime_logging.start(logger_type="costguard", config={"handler": guard})
    """

    def __init__(self, api_key: str, base_url: str = "http://localhost:8000", agent_name: str = "autogen"):
        self.guard = CostGuard(api_key=api_key, base_url=base_url, agent_name=agent_name, block_on_open=False)

    def log_event(self, source: str, event_name: str, data: dict) -> None:
        if event_name != "llm_call":
            return

        model = data.get("model", "unknown")
        usage = data.get("usage", {})
        provider = "openai"
        if "claude" in model.lower():
            provider = "anthropic"

        self.guard.log(
            provider=provider,
            model=model,
            tokens_in=usage.get("prompt_tokens", 0),
            tokens_out=usage.get("completion_tokens", 0),
            latency_ms=data.get("latency_ms", 0),
            metadata={"framework": "autogen", "source": source},
        )
