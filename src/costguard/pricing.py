"""Model pricing database (per 1M tokens)."""

# {model_name: (input_per_1m, output_per_1m)}
MODEL_PRICING: dict[str, tuple[float, float]] = {
    # OpenAI
    "gpt-4o": (2.50, 10.00),
    "gpt-4o-mini": (0.15, 0.60),
    "gpt-4-turbo": (10.00, 30.00),
    "gpt-4.1": (2.00, 8.00),
    "gpt-4.1-mini": (0.40, 1.60),
    "gpt-4.1-nano": (0.10, 0.40),
    "o1": (15.00, 60.00),
    "o3": (10.00, 40.00),
    "o3-mini": (1.10, 4.40),
    "o4-mini": (1.10, 4.40),
    # Anthropic
    "claude-opus-4": (15.00, 75.00),
    "claude-sonnet-4": (3.00, 15.00),
    "claude-haiku-3.5": (0.80, 4.00),
    # Google
    "gemini-2.5-pro": (1.25, 10.00),
    "gemini-2.5-flash": (0.15, 0.60),
    "gemini-2.0-flash": (0.10, 0.40),
    # DeepSeek
    "deepseek-v3": (0.27, 1.10),
    "deepseek-r1": (0.55, 2.19),
    # Groq (hosted models — faster, different pricing)
    "llama-3.3-70b": (0.59, 0.79),
    "llama-3.1-8b": (0.05, 0.08),
    "mixtral-8x7b": (0.24, 0.24),
}

# Fallback for unknown models
DEFAULT_PRICING = (5.00, 15.00)


def estimate_cost(model: str, tokens_in: int, tokens_out: int) -> float:
    """Estimate cost for a model call."""
    price_in, price_out = MODEL_PRICING.get(model, DEFAULT_PRICING)
    cost = (tokens_in * price_in + tokens_out * price_out) / 1_000_000
    return round(cost, 6)
