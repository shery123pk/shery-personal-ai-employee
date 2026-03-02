"""Shared OpenAI API gateway with retry, logging, and cost tracking.

Provides a single entry point for all LLM calls. Supports DEV_MODE
for synthetic responses without API calls.

Cost tracking is written to LOGS_DIR/.llm_usage.json.
"""

import json
import time
from pathlib import Path

import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import (
    DEV_MODE,
    LOGS_DIR,
    OPENAI_API_KEY,
    OPENAI_MAX_TOKENS,
    OPENAI_MODEL,
)
from logger import log_to_vault, setup_console_logger

logger = setup_console_logger("llm_gateway")

# Cost per 1M tokens for gpt-4o-mini (as of 2025)
_COST_PER_1M_INPUT = 0.15
_COST_PER_1M_OUTPUT = 0.60

_USAGE_FILE = LOGS_DIR / ".llm_usage.json"


def _load_usage() -> dict:
    """Load cumulative LLM usage stats."""
    if _USAGE_FILE.exists():
        try:
            return json.loads(_USAGE_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    return {"total_calls": 0, "total_input_tokens": 0, "total_output_tokens": 0, "total_cost_estimate": 0.0}


def _save_usage(usage: dict) -> None:
    """Persist cumulative LLM usage stats."""
    _USAGE_FILE.parent.mkdir(parents=True, exist_ok=True)
    _USAGE_FILE.write_text(json.dumps(usage, indent=2), encoding="utf-8")


def call_openai(
    system_prompt: str,
    user_prompt: str,
    model: str | None = None,
    max_tokens: int | None = None,
) -> dict:
    """Call OpenAI API with retry logic and cost tracking.

    Args:
        system_prompt: System message for the LLM.
        user_prompt: User message / task description.
        model: Model ID (defaults to config OPENAI_MODEL).
        max_tokens: Max output tokens (defaults to config OPENAI_MAX_TOKENS).

    Returns:
        {"text": str, "tokens_used": int, "cost_estimate": float}
    """
    model = model or OPENAI_MODEL
    max_tokens = max_tokens or OPENAI_MAX_TOKENS

    # DEV_MODE: return synthetic response without API call
    if DEV_MODE or not OPENAI_API_KEY:
        synthetic = (
            f"[DEV_MODE] Synthetic response for: {user_prompt[:100]}... "
            f"System context: {system_prompt[:80]}..."
        )
        logger.info("DEV_MODE: returning synthetic response (no API call)")
        return {"text": synthetic, "tokens_used": 0, "cost_estimate": 0.0}

    # Live API call with retry
    import openai

    client = openai.OpenAI(api_key=OPENAI_API_KEY)
    last_error = None

    for attempt in range(3):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                max_tokens=max_tokens,
                temperature=0.7,
            )

            text = response.choices[0].message.content or ""
            input_tokens = response.usage.prompt_tokens if response.usage else 0
            output_tokens = response.usage.completion_tokens if response.usage else 0
            total_tokens = input_tokens + output_tokens

            cost = (input_tokens * _COST_PER_1M_INPUT + output_tokens * _COST_PER_1M_OUTPUT) / 1_000_000

            # Track cumulative usage
            usage = _load_usage()
            usage["total_calls"] += 1
            usage["total_input_tokens"] += input_tokens
            usage["total_output_tokens"] += output_tokens
            usage["total_cost_estimate"] = round(usage["total_cost_estimate"] + cost, 6)
            _save_usage(usage)

            log_to_vault(
                action="llm_call",
                source=model,
                result="success",
                tokens=str(total_tokens),
                cost=f"${cost:.6f}",
            )

            return {"text": text, "tokens_used": total_tokens, "cost_estimate": cost}

        except Exception as exc:
            last_error = exc
            wait = 2 ** attempt
            logger.warning("LLM call attempt %d failed: %s — retrying in %ds", attempt + 1, exc, wait)
            time.sleep(wait)

    # All retries exhausted
    logger.error("LLM call failed after 3 attempts: %s", last_error)
    log_to_vault("llm_call_failed", model, "error", detail=str(last_error))
    return {"text": f"[ERROR] LLM call failed: {last_error}", "tokens_used": 0, "cost_estimate": 0.0}


def get_usage_summary() -> dict:
    """Return cumulative LLM usage statistics."""
    return _load_usage()
