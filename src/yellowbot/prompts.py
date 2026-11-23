"""Assemble the master, model-agnostic system prompt."""

from __future__ import annotations

import re
from pathlib import Path

from .knowledge import Fact, Figure

PROMPT_DIR = Path(__file__).parent / "prompts"
MODES = ("both", "front", "record")
CITE_RE = re.compile(r"\[(F\d{2,3})(?:[,\]\s])")


def _read(name: str) -> str:
    return (PROMPT_DIR / name).read_text(encoding="utf-8").strip()


def build_system_prompt(
    facts: list[Fact],
    figures: list[Figure],
    mode: str = "both",
    heat: int = 3,
    persona: str = "persona_yellow.md",
) -> str:
    if mode not in MODES:
        raise ValueError(f"mode must be one of {MODES}")
    heat = max(1, min(5, int(heat)))
    record = "\n".join(f"- {f.tagged()}" for f in facts) or (
        "(Nothing in the vetted record matches this turn. Say so plainly. Do not improvise facts.)"
    )
    fig_text = "\n".join(f"- ({g.id}) {g.label}: {g.text}" for g in figures)
    out = _read("master.md")
    for key, val in {
        "{{persona}}": _read(persona),
        "{{mode}}": mode,
        "{{heat}}": str(heat),
        "{{record}}": record,
        "{{figures}}": fig_text,
    }.items():
        out = out.replace(key, val)
    return out


def unknown_citations(text: str, known_ids: set[str]) -> set[str]:
    """IDs cited in a model reply that are not in the knowledge base (possible fabrication)."""
    return {m for m in CITE_RE.findall(text) if m not in known_ids}
