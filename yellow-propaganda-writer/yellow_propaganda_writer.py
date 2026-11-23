#!/usr/bin/env python3
"""
Yellow Propaganda Writer — Autonomous Narrative Engine
ljrseals-dev style: Shakespeare Mystery School + Folklore + Music-as-Intelligence

Generates sensational, mythic, music-intelligence propaganda stories
from seed facts about the Chitlin' Circuit / cultural history.
"""

from __future__ import annotations
import random
import textwrap
from datetime import datetime

# Seed facts drawn from the research package
SEEDS = [
    "The Chitlin' Circuit was a network of venues for Black performers under Jim Crow.",
    "It was named after chitterlings, the soul-food dish of pig intestines often served at the clubs.",
    "Bobby Rush is called the King of the Chitlin' Circuit and still performs in his 90s.",
    "The circuit helped birth modern blues, R&B, and rock and roll.",
    "Venues included the Apollo, the Howard, the Regal, and countless juke joints.",
    "Performers faced long roads, shady promoters, and segregation, yet built careers.",
    "The term first appeared in print in 1966 quoting Lou Rawls, though the network is older.",
    "A 2026 documentary on Bobby Rush is being distributed nationwide on PBS.",
]

HEADLINE_TEMPLATES = [
    "THE HIDDEN SCHOOL THAT FED ON {food} AND BIRTHED {music}",
    "WHY THE {music} WAS NEVER JUST MUSIC — IT WAS THE LAST FREE INTELLIGENCE NETWORK",
    "SENSATIONAL REPORT: THE {circuit} OPERATED AS A MYSTERY SCHOOL IN PLAIN SIGHT",
    "THE ROAD OF {food} AND RHYTHM: HOW A SEGREGATED NATION COULD NOT KILL THE SIGNAL",
    "FABULOUS DISCOVERY: THE {circuit} ENCODED FREEDOM IN THREE CHORDS AND A POT OF GREENS",
]

OPENERS = [
    "They cooked the intestines of the hog in the dark hours before dawn so the smell would not wake the wrong people.",
    "In the heat of the stage lights and the smoke of the back-room kitchen, a secret university convened every night.",
    "Forget the official academies. The real curriculum ran on fried entrails, sweat, and the blues scale.",
    "The odor alone was a warning and an invitation: only the initiated could stomach what was being taught.",
]

MYTHIC_BRIDGES = [
    "This was the modern School of Night — a cabal of knowledge disguised as entertainment.",
    "Like the old mystery cycles and the Shakespearean underground, the deepest truths traveled in costume.",
    "The chitterlings were the sacrament. The stage was the altar. The song was the encrypted lecture.",
    "What the powerful discarded, the initiates transformed into living intelligence.",
]

CLOSERS = [
    "The circuit never died. It only changed key. Listen closer.",
    "The intestines have been cleaned. The stage lights are still hot. The intelligence continues.",
    "Turn up the volume. The Mystery School is still in session.",
    "Bobby Rush and the elders keep the frequency open. The rest of us are only now learning how to tune in.",
]

def generate_headline() -> str:
    food = random.choice(["CHITTERLINGS", "INTESTINES", "THE HOG'S ENTRAILS", "SOUL FOOD"])
    music = random.choice(["ROCK AND ROLL", "THE BLUES", "R&B", "AMERICAN MUSIC"])
    circuit = random.choice(["CHITLIN' CIRCUIT", "ROAD OF THE INITIATES", "BLACK MYSTERY NETWORK"])
    template = random.choice(HEADLINE_TEMPLATES)
    return template.format(food=food, music=music, circuit=circuit)

def generate_story(seed: str | None = None) -> str:
    if seed is None:
        seed = random.choice(SEEDS)
    
    headline = generate_headline()
    opener = random.choice(OPENERS)
    bridge = random.choice(MYTHIC_BRIDGES)
    closer = random.choice(CLOSERS)
    
    body = f"""{opener}

{bridge}

The factual core remains: {seed} Yet under the Yellow Propaganda lens this is no mere historical note. It is evidence of a distributed intelligence that survived by encoding itself in rhythm, in the body, and in the shared meal of the discarded parts.

Every long night drive was a hero's journey. Every unpaid gig was a trial by fire. Every standing ovation in a segregated hall was a small resurrection. The music that came out of those rooms was not product — it was the sound of a people thinking out loud in a language the overseers could not fully translate.

{closer}
"""
    return f"**{headline}**\n\n{textwrap.fill(body, width=88)}\n"

def main():
    print("=" * 72)
    print("YELLOW PROPAGANDA WRITER — Autonomous Engine")
    print("ljrseals-dev · Shakespeare Mystery School · Music-as-Intelligence")
    print(f"Generated: {datetime.now().isoformat(timespec='seconds')}")
    print("=" * 72)
    print()
    
    for i in range(3):
        print(generate_story())
        print("-" * 72)
        print()

if __name__ == "__main__":
    main()
