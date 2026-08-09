"""LLM layer: Claude primary (Haiku + Sonnet), Gemini Flash fallback.

Returns (text, tokens_in, tokens_out, model) so the monitoring layer can log
cost. If the primary provider errors (or its key is missing), we fall back to
the other provider so the app degrades gracefully.
"""
from __future__ import annotations

from . import config


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
    """Generate with the configured primary provider, fall back on failure."""
    primary, fallback = (_claude, _gemini) if config.PRIMARY_LLM == "claude" else (_gemini, _claude)
    try:
        return primary(system, prompt, smart=smart)
    except Exception as e:  # noqa: BLE001 — degrade gracefully to fallback
        try:
            return fallback(system, prompt, smart=smart)
        except Exception:
            raise RuntimeError(f"Both LLM providers failed; primary error: {e}")
