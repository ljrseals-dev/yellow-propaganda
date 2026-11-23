"""Orchestrator: retrieval -> prompt -> backend -> verification -> memory."""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from .knowledge import KnowledgeBase, tokenize
from .memory import Conversation
from .offline import MORE, OfflineEngine
from .prompts import MODES, build_system_prompt, unknown_citations
from .providers import ProviderError

MAX_INPUT_CHARS = 2000


@dataclass
class Reply:
    text: str
    fact_ids: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    backend: str = "offline"


class YellowBot:
    def __init__(self, kb: KnowledgeBase | None = None, provider=None, mode: str = "both",
                 heat: int = 3, conversation: Conversation | None = None, seed: int | None = None):
        self.kb = kb or KnowledgeBase.load()
        self.provider = provider
        self.mode, self.heat = mode, heat
        self.conv = conversation or Conversation()
        self.offline = OfflineEngine(self.kb, random.Random(seed))

    # settings ---------------------------------------------------------------------------
    def set_mode(self, mode: str) -> None:
        if mode not in MODES:
            raise ValueError(f"mode must be one of: {', '.join(MODES)}")
        self.mode = mode

    def set_heat(self, heat: int) -> None:
        if not 1 <= heat <= 5:
            raise ValueError("heat must be 1 to 5")
        self.heat = heat

    def system_prompt(self, query: str = "") -> str:
        facts = self.kb.search(query, k=5) if query else self.kb.overview(5)
        return build_system_prompt(facts, self.kb.figures, self.mode, self.heat)

    # retrieval --------------------------------------------------------------------------
    def _retrieve(self, text: str):
        low = text.lower().strip("!?. ")
        is_more = low in MORE
        query = self.conv.last_topic if is_more else text
        # short follow-ups ("and the Apollo?") borrow the previous topic for context
        if not is_more and len(tokenize(text)) < 2 and self.conv.last_topic:
            query = f"{self.conv.last_topic} {text}"
        facts = self.kb.search(query, k=4, exclude=self.conv.shown_fact_ids if is_more else None)
        if not is_more and facts:
            self.conv.last_topic = text if len(tokenize(text)) >= 2 else query
        return facts, is_more

    # main entry -------------------------------------------------------------------------
    def ask(self, user_text: str, mode: str | None = None) -> Reply:
        text = user_text.strip()[:MAX_INPUT_CHARS]
        if not text:
            return Reply("The stage is empty. Speak, and the lamp will find you.")
        facts, is_more = self._retrieve(text)
        mode = mode or self.mode
        warnings: list[str] = []
        backend = "offline"
        out = None

        if self.provider is not None:
            try:
                sys_prompt = build_system_prompt(facts, self.kb.figures, mode, self.heat)
                msgs = [*self.conv.window(), {"role": "user", "content": text}]
                out = self.provider.chat(sys_prompt, msgs)
                backend = getattr(self.provider, "name", "model")
                bad = unknown_citations(out, self.kb.known_ids())
                if bad:
                    warnings.append(
                        "Model cited IDs that are not in the record: " + ", ".join(sorted(bad))
                        + ". Treat those claims as unverified."
                    )
            except ProviderError as e:
                warnings.append(f"Backend failed ({e}). Answered offline instead.")
                out = None

        if out is None:
            if is_more and not facts:
                out = "The archive has nothing further on that thread. Try a new topic, or /facts to browse."
            else:
                out = self.offline.reply(text, facts, mode, self.heat)
            backend = "offline"

        self.conv.add_user(text)
        self.conv.add_assistant(out, [f.id for f in facts])
        return Reply(out, [f.id for f in facts], warnings, backend)

    def check(self, claim: str) -> Reply:
        claim = claim.strip()[:MAX_INPUT_CHARS]
        if not claim:
            return Reply("Give me a claim to check, e.g. /check the circuit ran on encrypted blues scales")
        if self.provider is None:
            out = self.offline.check(claim)
            self.conv.add_user(f"/check {claim}")
            self.conv.add_assistant(out)
            return Reply(out)
        return self.ask(
            "Fact-check this claim. Label it SUPPORTED, PARTLY SUPPORTED, UNSUPPORTED or FIGURATIVE "
            f"and explain in two to four lines, citing record IDs only: {claim}",
            mode="record",
        )

    def story(self, topic: str = "") -> Reply:
        facts = self.offline.story_seed(topic)
        prompt = f"Write a front page story about: {topic}" if topic else "Write a front page story from any thread in the record."
        if self.provider is None:
            out = self.offline.reply(topic or "the circuit", facts, self.mode, self.heat)
            self.conv.add_user(prompt)
            self.conv.add_assistant(out, [f.id for f in facts])
            return Reply(out, [f.id for f in facts])
        return self.ask(prompt)
