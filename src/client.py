"""DeepSeek client for the literature search system.

Thin wrapper around the shared adapter in the research idea system,
configured for survey-generation (lower temperature than idea generation).
"""
from __future__ import annotations
import sys
from pathlib import Path

# Reuse the proven client from the research idea system
_IDEA_SYS = Path(__file__).resolve().parents[1].parent / "研究想法系统"
sys.path.insert(0, str(_IDEA_SYS))

from idea_system.deepseek import DeepSeekClient, DeepSeekError  # noqa: F401,E402


def create_client(config: dict) -> DeepSeekClient:
    d = config["deepseek"]
    return DeepSeekClient(
        model_name=d["model"],
        secret_path=d["secret_path"],
        timeout_seconds=d["timeout_seconds"],
        transient_retries=d["transient_retries"],
        max_tokens=d["max_tokens"],
        temperature=d["temperature"],
    )


class FakeClient:
    """Deterministic stand-in for dry runs."""

    def __init__(self):
        self.model_name = "fake-model"
        self.temperature = 0.7
        self.last_usage = None
        self.last_model = "fake-model"
        self.last_content = None
        self.history = type("H", (), {"records": [], "totals": lambda self: {}})()

    def chat(self, system, user, stage="chat", **kwargs):
        self.last_content = '{"queries": ["sample query 1", "sample query 2"]}'
        return self.last_content

    def chat_json(self, system, user, stage="chat_json", **kwargs):
        import json
        return json.loads('{"findings": [{"finding": "sample finding", "citations": ["S1"]}], "clusters": [{"name": "Sample Cluster", "papers": ["S1"], "summary": "A sample cluster."}], "report_markdown": "# Sample Report\\n\\nThis is a dry run."}')
