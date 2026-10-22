import urllib.request

from specdiff_ai import llm
from specdiff_ai.extract import parse_lines


def test_noop_without_env(monkeypatch):
    monkeypatch.delenv("SPECDIFF_LLM_ENDPOINT", raising=False)
    assert llm.llm_enabled() is False
    assert llm.enhance_text("原文 8.5 kA") == "原文 8.5 kA"
    clauses = parse_lines(["2.1 电流 8.5 kA。"], "d")
    assert llm.maybe_enhance(clauses) is clauses


def test_fallback_when_endpoint_unreachable(monkeypatch):
    monkeypatch.setenv("SPECDIFF_LLM_ENDPOINT", "http://127.0.0.1:9/llm")

    def boom(*args, **kwargs):
        raise OSError("connection refused")

    monkeypatch.setattr(urllib.request, "urlopen", boom)
    assert llm.enhance_text("原文") == "原文"
