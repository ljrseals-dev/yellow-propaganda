"""Vetted fact store with small, dependency-free retrieval."""

from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass
from pathlib import Path

DATA_PATH = Path(__file__).parent / "data" / "knowledge.json"

_STOP = {
    "a", "an", "and", "are", "as", "at", "be", "by", "did", "do", "does", "for", "from", "how", "i",
    "in", "is", "it", "its", "me", "of", "on", "or", "tell", "that", "the", "their", "them", "there",
    "this", "to", "was", "were", "what", "when", "where", "which", "who", "why", "with", "you", "about",
    "more", "please", "story", "write", "give",
}


def tokenize(text: str) -> list[str]:
    words = re.findall(r"[a-z0-9&']+", text.lower().replace("’", "'"))
    out = []
    for w in words:
        w = w.strip("'")
        if len(w) > 3 and w.endswith("s") and not w.endswith("ss"):
            w = w[:-1]  # crude plural fold: chitlins -> chitlin
        if w and w not in _STOP:
            out.append(w)
    return out


@dataclass(frozen=True)
class Fact:
    id: str
    text: str
    confidence: str
    tags: tuple[str, ...]
    source: str

    def tagged(self) -> str:
        return f"[{self.id}, {self.confidence}] {self.text}"


@dataclass(frozen=True)
class Figure:
    id: str
    label: str
    text: str


class KnowledgeBase:
    def __init__(self, facts: list[Fact], figures: list[Figure]):
        self.facts = facts
        self.figures = figures
        self.by_id = {f.id: f for f in facts}
        self._tokens = {f.id: set(tokenize(f.text)) for f in facts}
        self._tag_tokens = {f.id: set(t for tag in f.tags for t in tokenize(tag)) for f in facts}
        df: dict[str, int] = {}
        for f in facts:
            for t in self._tokens[f.id] | self._tag_tokens[f.id]:
                df[t] = df.get(t, 0) + 1
        n = max(len(facts), 1)
        self._idf = {t: math.log(1 + n / c) for t, c in df.items()}

    @classmethod
    def load(cls, path: Path | str = DATA_PATH) -> "KnowledgeBase":
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
        facts = [
            Fact(d["id"], d["text"], d["confidence"], tuple(d.get("tags", ())), d.get("source", ""))
            for d in raw["facts"]
        ]
        figures = [Figure(d["id"], d["label"], d["text"]) for d in raw.get("figures", [])]
        return cls(facts, figures)

    def search(self, query: str, k: int = 4, exclude: set[str] | None = None) -> list[Fact]:
        """Return up to k facts with a positive match score, best first.

        Tag matches count double (tags are curated keywords). Returns [] when nothing
        matches, so callers can say so honestly instead of improvising.
        """
        q = set(tokenize(query))
        if not q:
            return []
        exclude = exclude or set()
        scored = []
        for f in self.facts:
            if f.id in exclude:
                continue
            body = q & self._tokens[f.id]
            tags = q & self._tag_tokens[f.id]
            score = sum(self._idf[t] for t in body) + 2 * sum(self._idf[t] for t in tags)
            if score > 0:
                scored.append((score, f.id, f))
        scored.sort(key=lambda s: (-s[0], s[1]))
        return [f for _, _, f in scored[:k]]

    def overview(self, k: int = 4) -> list[Fact]:
        """A stable, broad set of high-confidence facts for open-ended openers."""
        return [f for f in self.facts if f.confidence == "high"][:k]

    def known_ids(self) -> set[str]:
        return set(self.by_id)
