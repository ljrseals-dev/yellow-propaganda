"""Multi-turn conversation state with save / load / export."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path


@dataclass
class Conversation:
    max_turns: int = 12  # user+assistant pairs sent to the model
    turns: list[dict] = field(default_factory=list)  # {"role": "user"|"assistant", "content": str}
    shown_fact_ids: set[str] = field(default_factory=set)
    last_topic: str = ""

    def add_user(self, text: str) -> None:
        self.turns.append({"role": "user", "content": text})

    def add_assistant(self, text: str, fact_ids: list[str] | None = None) -> None:
        self.turns.append({"role": "assistant", "content": text})
        self.shown_fact_ids.update(fact_ids or [])

    def window(self) -> list[dict]:
        """Last max_turns exchanges, always starting on a user message."""
        msgs = self.turns[-self.max_turns * 2 :]
        while msgs and msgs[0]["role"] != "user":
            msgs = msgs[1:]
        return msgs

    def reset(self) -> None:
        self.turns.clear()
        self.shown_fact_ids.clear()
        self.last_topic = ""

    def save(self, path: str | Path) -> Path:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(
            json.dumps(
                {
                    "saved": datetime.now().isoformat(timespec="seconds"),
                    "turns": self.turns,
                    "shown_fact_ids": sorted(self.shown_fact_ids),
                    "last_topic": self.last_topic,
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        return p

    @classmethod
    def load(cls, path: str | Path, max_turns: int = 12) -> "Conversation":
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls(
            max_turns=max_turns,
            turns=list(raw.get("turns", [])),
            shown_fact_ids=set(raw.get("shown_fact_ids", [])),
            last_topic=raw.get("last_topic", ""),
        )

    def to_markdown(self) -> str:
        lines = [f"# Yellow Press transcript ({datetime.now():%Y-%m-%d %H:%M})", ""]
        for t in self.turns:
            who = "You" if t["role"] == "user" else "Yellow Press"
            lines += [f"**{who}**", "", t["content"], ""]
        return "\n".join(lines)
