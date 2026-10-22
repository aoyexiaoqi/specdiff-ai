"""Optional AI enhancement hook.

SpecDiff AI is deterministic by design: extraction, alignment and
classification never need a network call.  This module defines the one
place where an LLM *may* help -- normalising messy clause wording before
comparison -- and it is a no-op unless the environment variable
``SPECDIFF_LLM_ENDPOINT`` points at an HTTP endpoint accepting
``{"text": ...}`` and returning ``{"text": ...}``.

Any failure (no endpoint, timeout, bad response) silently falls back to
the original text: an unavailable AI must never break an offline diff.
"""

from __future__ import annotations

import json
import os
import urllib.request
from typing import List

from .extract import Clause
from .params import extract_params

ENV_VAR = "SPECDIFF_LLM_ENDPOINT"


def llm_enabled() -> bool:
    return bool(os.environ.get(ENV_VAR))


def enhance_text(text: str, timeout: float = 5.0) -> str:
    """Return LLM-normalised *text*, or *text* unchanged when unavailable."""
    endpoint = os.environ.get(ENV_VAR)
    if not endpoint:
        return text
    try:
        payload = json.dumps({"text": text}).encode("utf-8")
        request = urllib.request.Request(
            endpoint, data=payload, headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(request, timeout=timeout) as response:
            data = json.loads(response.read().decode("utf-8"))
        enhanced = data.get("text")
        if isinstance(enhanced, str) and enhanced.strip():
            return enhanced
    except Exception:
        pass
    return text


def maybe_enhance(clauses: List[Clause]) -> List[Clause]:
    """Apply :func:`enhance_text` to every clause (no-op by default)."""
    if not llm_enabled():
        return clauses
    for clause in clauses:
        enhanced = enhance_text(clause.text)
        if enhanced != clause.text:
            clause.text = enhanced
            clause.params = extract_params(enhanced)
    return clauses
