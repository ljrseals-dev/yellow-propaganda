"""Command-line REPL."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .bot import YellowBot
from .memory import Conversation
from .prompts import MODES
from .providers import ProviderError, make_provider

BANNER = """\
========================================================================
  THE YELLOW PRESS  ·  v0.2.0
  Mythic front page  +  cited record  ·  any model, or none
========================================================================
  Ask anything about the Chitlin' Circuit, its food, its music.  /help
========================================================================"""

HELP = """\
Talk normally. Every answer has two registers: THE FRONT PAGE (figurative) and THE RECORD (cited facts).

  /mode both|front|record   choose what you get
  /heat 1-5                 1 restrained and wry ... 5 full oracular tabloid
  /story [topic]            a front page piece
  /check <claim>            test a claim you have heard against the record
  /facts [id]               list vetted facts, or show one with its source
  /more  (or just "more")   new material on the same thread
  /prompt                   print the master system prompt (paste into any chat UI)
  /save [file] /load [file] /export [file]   conversation to JSON / Markdown
  /reset                    clear the conversation
  /status                   backend, mode, heat
  /quit
"""

DEFAULT_SAVE = Path.home() / ".yellowbot" / "session.json"


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="yellowbot", description="The Yellow Press chatbot")
    p.add_argument("--provider", help="offline (default), anthropic, openai, openrouter, groq, ollama, lmstudio, compat")
    p.add_argument("--model")
    p.add_argument("--base-url")
    p.add_argument("--mode", choices=MODES, default="both")
    p.add_argument("--heat", type=int, default=3, choices=range(1, 6))
    p.add_argument("--temperature", type=float, default=0.8)
    p.add_argument("--load", metavar="FILE", help="resume a saved conversation")
    p.add_argument("--seed", type=int, help="make offline output deterministic")
    p.add_argument("--once", metavar="TEXT", help="answer one message and exit")
    p.add_argument("--print-prompt", action="store_true", help="print the master system prompt and exit")
    return p


def _show(reply) -> None:
    print()
    print(reply.text)
    for w in reply.warnings:
        print(f"\n  ! {w}")
    print("-" * 72)


def handle_command(bot: YellowBot, line: str) -> bool:
    """Return False to quit."""
    cmd, _, arg = line.partition(" ")
    cmd, arg = cmd.lower(), arg.strip()
    try:
        if cmd in ("/quit", "/exit"):
            print("The stage lights cool. Listen closer next time.")
            return False
        if cmd in ("/help", "/?"):
            print(HELP)
        elif cmd == "/mode":
            bot.set_mode(arg)
            print(f"mode = {bot.mode}")
        elif cmd == "/heat":
            bot.set_heat(int(arg))
            print(f"heat = {bot.heat}")
        elif cmd == "/story":
            _show(bot.story(arg))
        elif cmd == "/check":
            _show(bot.check(arg))
        elif cmd == "/more":
            _show(bot.ask("more"))
        elif cmd == "/facts":
            if arg:
                f = bot.kb.by_id.get(arg.upper())
                print(f"{f.tagged()}\n  source: {f.source}" if f else f"No fact {arg}.")
            else:
                for f in bot.kb.facts:
                    print(f"{f.id} [{f.confidence:6}] {f.text[:80]}{'...' if len(f.text) > 80 else ''}")
        elif cmd == "/prompt":
            print(bot.system_prompt(bot.conv.last_topic))
        elif cmd == "/save":
            print(f"saved to {bot.conv.save(arg or DEFAULT_SAVE)}")
        elif cmd == "/load":
            bot.conv = Conversation.load(arg or DEFAULT_SAVE)
            print(f"loaded {len(bot.conv.turns)} messages")
        elif cmd == "/export":
            p = Path(arg or "transcript.md")
            p.write_text(bot.conv.to_markdown(), encoding="utf-8")
            print(f"exported to {p}")
        elif cmd == "/reset":
            bot.conv.reset()
            print("conversation cleared")
        elif cmd == "/status":
            prov = getattr(bot.provider, "name", "offline")
            model = getattr(bot.provider, "model", "-")
            print(f"backend={prov} model={model} mode={bot.mode} heat={bot.heat} turns={len(bot.conv.turns)//2}")
        else:
            print(f"Unknown command {cmd}. Try /help.")
    except (ValueError, OSError) as e:
        print(f"  ! {e}")
    return True


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        provider = make_provider(args.provider, args.model, args.base_url, args.temperature)
    except ProviderError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    bot = YellowBot(provider=provider, mode=args.mode, heat=args.heat, seed=args.seed)
    if args.load:
        try:
            bot.conv = Conversation.load(args.load)
        except (OSError, ValueError) as e:
            print(f"error: could not load {args.load}: {e}", file=sys.stderr)
            return 2
    if args.print_prompt:
        print(bot.system_prompt())
        return 0
    if args.once:
        _show(bot.ask(args.once))
        return 0

    print(BANNER)
    print(f"  backend: {getattr(provider, 'name', 'offline')}   mode: {bot.mode}   heat: {bot.heat}\n")
    while True:
        try:
            line = input("You > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nThe lights dim. The frequency remains open.")
            return 0
        if not line:
            continue
        if line.startswith("/"):
            if not handle_command(bot, line):
                return 0
            continue
        _show(bot.ask(line))


if __name__ == "__main__":
    raise SystemExit(main())
