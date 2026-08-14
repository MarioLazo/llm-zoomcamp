"""LLM layer: Gemini primary (free tier), Claude Haiku/Sonnet fallback.

Returns (text, tokens_in, tokens_out, model) so the monitoring layer can log
cost. If the primary provider errors (or its key is missing), we fall back to
the other provider so the app degrades gracefully.

Gemini's free tier caps at 5 requests/minute per model — well within what a
human clicking through the UI would ever hit, but eval scripts that fire many
calls back-to-back (eval/llm_eval.py, eval/integrity_checks.py) need to pace
themselves AND retry-with-backoff on a transient 429, rather than immediately
burning the (unconfigured, placeholder-key) Claude fallback. `_is_rate_limit`
matches on message content since google-generativeai doesn't always raise a
distinct exception subclass we can rely on across versions.
"""
from __future__ import annotations

import time

from . import config

MAX_RETRIES = 3
RETRY_BACKOFF_SECONDS = 20


def _is_rate_limit(exc: Exception) -> bool:
    msg = str(exc).lower()
    return "429" in msg or "quota" in msg or "rate limit" in msg


def _claude(system: str, prompt: str, smart: bool = False):
    import anthropic

    client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
    model = config.CLAUDE_SMART_MODEL if smart else config.CLAUDE_FAST_MODEL
    resp = client.messages.create(
        model=model,
        max_tokens=1024,
        system=system,
        messages=[{"role": "user", "content": prompt}],
    )
    text = "".join(block.text for block in resp.content if block.type == "text")
    return text, resp.usage.input_tokens, resp.usage.output_tokens, model


def _gemini(system: str, prompt: str, smart: bool = False):
    import google.generativeai as genai

    genai.configure(api_key=config.GEMINI_API_KEY)
    model = genai.GenerativeModel(config.GEMINI_MODEL, system_instruction=system)
    resp = model.generate_content(prompt)
    usage = getattr(resp, "usage_metadata", None)
    tin = getattr(usage, "prompt_token_count", 0) if usage else 0
    tout = getattr(usage, "candidates_token_count", 0) if usage else 0
    return resp.text, tin, tout, config.GEMINI_MODEL


def generate(system: str, prompt: str, smart: bool = False):
    """Generate with the configured primary provider, retrying on transient
    rate limits before falling back to the other provider."""
    primary, fallback = (_claude, _gemini) if config.PRIMARY_LLM == "claude" else (_gemini, _claude)

    last_err = None
    for attempt in range(MAX_RETRIES):
        try:
            return primary(system, prompt, smart=smart)
        except Exception as e:  # noqa: BLE001
            last_err = e
            if _is_rate_limit(e) and attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_BACKOFF_SECONDS)
                continue
            break

    try:
        return fallback(system, prompt, smart=smart)
    except Exception:
        raise RuntimeError(f"Both LLM providers failed; primary error: {last_err}")
