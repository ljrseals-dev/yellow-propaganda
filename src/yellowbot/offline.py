"""Offline engine: no model, no network. Same two-register contract as the LLM path.

Every literal claim comes straight from retrieved record entries. The FRONT PAGE flourishes are
figurative and avoid new names, dates, numbers or events.
"""

from __future__ import annotations

import random
import re
import textwrap

from .knowledge import Fact, KnowledgeBase, tokenize

HEADLINES = [
    "THE HIDDEN SCHOOL THAT FED ON {food} AND BIRTHED {music}",
    "WHY {music} WAS NEVER JUST MUSIC: THE ROAD KEPT A SCHOOL IN SESSION",
    "SENSATIONAL REPORT: THE {circuit} RAN LIKE A MYSTERY SCHOOL IN PLAIN SIGHT",
    "THE ROAD OF {food} AND RHYTHM: A SEGREGATED NATION COULD NOT KILL THE SIGNAL",
    "EXCLUSIVE: {food} KEPT THE SECRET LONGER THAN ANY ARCHIVE",
    "{circuit} NEVER CLOSED. IT ONLY CHANGED KEY",
]
FOODS = ["CHITTERLINGS", "A POT OF GREENS", "SOUL FOOD", "THE HOG'S LEAVINGS"]
MUSICS = ["ROCK AND ROLL", "THE BLUES", "R&B", "AMERICAN MUSIC"]
CIRCUITS = ["THE CHITLIN' CIRCUIT", "THE OLD ROAD", "THE GREAT BLACK ROAD"]

OPENERS = [
    "The smell arrives before the music does: vinegar, pepper, pork, a pot that has been working since the afternoon.",
    "Heat from the stage lights, smoke in the back-room kitchen, and a hall that is about to learn something.",
    "Forget the official academies. This curriculum ran on sweat, grease and the blues scale.",
    "The odor is a warning and an invitation. Only the committed stay for the second verse.",
    "Before the cameras, the road already knew.",
]
BRIDGES = [
    "Call it the School of Night, if you like: knowledge traveling in costume.",
    "As in the old mystery plays, the deepest lessons rode in under entertainment.",
    "The meal was the sacrament, the stage the altar, the song the lecture.",
    "What was discarded became nourishment. That is the oldest alchemy there is.",
    "Think of every club as a node and every bandleader as a courier, and the map lights up like a nervous system.",
    "Every call-and-response is a handshake across a dark room.",
]
RHETORICAL = [
    "And who keeps the curriculum when the schoolhouse is a bus?",
    "What is a signal, if not a song that refuses to be stopped?",
    "Who taught the teachers? The road did.",
]
CLOSERS = [
    "The circuit never died. It only changed key. Listen closer.",
    "The stage lights are still hot. The signal is still in the air.",
    "Turn it up. The school is still in session.",
    "The pot is still on the stove. The road is still open.",
]
FRONT_NO_RECORD = [
    "The lamp swings across the archive and finds no page on that.",
    "The archive is quiet on this one. Even a Mystery School keeps its limits.",
]
GREETINGS = {"hi", "hello", "hey", "greetings", "yo", "good evening", "good morning"}
MORE = {"more", "go on", "continue", "and", "and?", "keep going", "tell me more", "next"}
FIGURE_TRIGGERS = {
    "encrypt": "G3", "code": "G3", "decode": "G3", "cipher": "G3", "secret": "G1", "mystery": "G1",
    "school": "G1", "intelligence": "G2", "spy": "G2", "covert": "G2", "network": "G2",
    "sacrament": "G4", "labyrinth": "G4", "pilgrimage": "G5",
}
QUESTION_START = re.compile(r"^(who|what|when|where|why|how|did|does|do|is|was|were|are|can|could)\b", re.I)


def _wrap(s: str) -> str:
    return "\n".join(textwrap.fill(p, 88) if p and not p.startswith("-") else p for p in s.split("\n"))


def _record_lines(facts: list[Fact]) -> str:
    return "\n".join(f"- {f.text} [{f.id}, {f.confidence}]" for f in facts)


class OfflineEngine:
    def __init__(self, kb: KnowledgeBase, rng: random.Random | None = None):
        self.kb = kb
        self.rng = rng or random.Random()

    # ---- front page -------------------------------------------------------------------
    def _headline(self, heat: int) -> str:
        h = self.rng.choice(HEADLINES).format(
            food=self.rng.choice(FOODS), music=self.rng.choice(MUSICS), circuit=self.rng.choice(CIRCUITS)
        )
        return h if heat >= 3 else h.title().replace("'S", "'s")

    def front_page(self, facts: list[Fact], heat: int, is_question: bool) -> str:
        if not facts:
            return self.rng.choice(FRONT_NO_RECORD)
        out = [f"**{self._headline(heat)}**"]
        if is_question:
            out.append(f"The plain answer first: {facts[0].text}")
        body = [self.rng.choice(OPENERS)]
        body += self.rng.sample(BRIDGES, {1: 1, 2: 1, 3: 2, 4: 2, 5: 3}[heat])
        if not is_question:
            body.append(f"Strip the costume and the fact stands. {facts[0].text}")
        if heat >= 4:
            body.append(self.rng.choice(RHETORICAL))
        out.append(" ".join(body))
        out.append(self.rng.choice(CLOSERS))
        return "\n\n".join(out)

    # ---- record -----------------------------------------------------------------------
    def record(self, facts: list[Fact]) -> str:
        if facts:
            return _record_lines(facts)
        topics = ", ".join(["Bobby Rush", "the Fergusons", "venues", "chitterlings", "the 1966 term origin"])
        return (
            "- Nothing in the vetted record covers that. That means unrecorded here, which is not the same as false.\n"
            f"Open questions: try asking about {topics}."
        )

    # ---- main -------------------------------------------------------------------------
    def reply(self, user_text: str, facts: list[Fact], mode: str, heat: int, first_turn: bool = False) -> str:
        text = user_text.strip()
        low = text.lower().strip("!?. ")
        if low in GREETINGS:
            return (
                "The lights are already warm and the pot is on the stove.\n"
                "Ask about the Circuit, the food, the music or the elders, or hand me a topic and I will "
                "spin it into a front page and set the record beside it. Try /help."
            )
        is_question = bool(QUESTION_START.match(text)) or text.endswith("?")
        sections = []
        if mode in ("both", "front"):
            sections.append("## THE FRONT PAGE\n" + self.front_page(facts, heat, is_question))
        if mode in ("both", "record"):
            sections.append("## THE RECORD\n" + self.record(facts))
        if facts and facts[0].confidence == "low":
            sections.append("Open questions: the leading item is unconfirmed. Treat it as a lead, not a fact.")
        elif facts:
            sections.append("Next thread: ask for \"more\", or try /check with a claim you have heard.")
        return "\n\n".join(_wrap(s) for s in sections)

    # ---- fact check -------------------------------------------------------------------
    def check(self, claim: str) -> str:
        facts = self.kb.search(claim, k=3)
        q = set(tokenize(claim))
        figs = {self.kb_fig(g) for stem, g in FIGURE_TRIGGERS.items() if any(t.startswith(stem) for t in q)}
        figs.discard(None)
        lines = ["## THE RECORD", f"Claim: {claim}"]
        if figs:
            lines.append("Verdict: FIGURATIVE (at least in part). The wording matches an interpretive frame, not a documented event.")
            lines += [f"- {g.label} ({g.id}): {g.text}" for g in sorted(figs, key=lambda g: g.id)]
        elif facts:
            lines.append("Verdict: the offline matcher cannot judge truth. These are the closest vetted entries; compare them yourself, or run with a model backend for a real comparison.")
        else:
            lines.append("Verdict: UNSUPPORTED BY THE RECORD. That is not the same as false. It means nothing vetted here covers it.")
        lines += [f"- {f.text} [{f.id}, {f.confidence}]" for f in facts]
        return "\n".join(lines)

    def kb_fig(self, gid: str):
        return next((g for g in self.kb.figures if g.id == gid), None)

    # ---- story (explicit) -------------------------------------------------------------
    def story_seed(self, topic: str) -> list[Fact]:
        return self.kb.search(topic, k=3) if topic else self.rng.sample(self.kb.facts, 3)
