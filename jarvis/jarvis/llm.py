"""Minimal Claude Messages API client using only the standard library."""

from __future__ import annotations

import json
import urllib.request
from typing import Any, Callable

API_URL = "https://api.anthropic.com/v1/messages"
API_VERSION = "2023-06-01"


class LLMError(Exception):
    """Raised when the API call fails or returns an unexpected payload."""


def build_payload(model: str, system: str, messages: list[dict], max_tokens: int = 1024) -> dict:
    return {"model": model, "max_tokens": max_tokens, "system": system, "messages": messages}


def extract_text(response: dict[str, Any]) -> str:
    blocks = response.get("content")
    if not isinstance(blocks, list):
        raise LLMError("Unexpected response from the Claude API.")
    return "".join(b.get("text", "") for b in blocks if b.get("type") == "text")


def send(
    api_key: str,
    payload: dict,
    opener: Callable[..., Any] = urllib.request.urlopen,
    timeout: int = 60,
) -> str:
    """POST a Messages request and return the assistant's text."""
    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        API_URL,
        data=body,
        method="POST",
        headers={
            "content-type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": API_VERSION,
        },
    )
    try:
        with opener(request, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception as exc:  # network, HTTP error, or bad JSON
        raise LLMError(f"Claude API request failed: {exc}") from exc
    if isinstance(data, dict) and data.get("type") == "error":
        raise LLMError(data.get("error", {}).get("message", "unknown API error"))
    return extract_text(data)
