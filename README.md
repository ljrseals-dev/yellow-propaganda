# The Yellow Press (v0.2)

A mythic-tabloid chatbot about the Chitlin' Circuit, its food and its music, built on a **master, model-agnostic prompt**. It runs fully offline with no dependencies, or on any LLM you point it at.

The idea: the oracular "Yellow Propaganda" voice is compelling, but a voice that blends legend and fact misleads people. So every answer comes in **two registers**:

```
## THE FRONT PAGE     figurative, mythic, tabloid: the performance
## THE RECORD         plain, cited, confidence-tagged: [F04, high]
```

The front page may be extravagant but may not introduce literal claims. The record is where facts live, each traceable to a vetted entry in `src/yellowbot/data/knowledge.json`. If the record has nothing on a topic, the bot says so instead of improvising.

## Quick start

```bash
cd yellow-propaganda-chatbot
pip install -e .            # or just: PYTHONPATH=src python -m yellowbot
yellowbot                   # offline engine, no key needed
yellowbot --once "Who were the Ferguson brothers?" --heat 2
```

## Use any model

```bash
export ANTHROPIC_API_KEY=...   && yellowbot --provider anthropic            # default model claude-sonnet-5-5
export OPENAI_API_KEY=...      && yellowbot --provider openai --model gpt-4o-mini
yellowbot --provider ollama --model llama3.1                                 # local, no key
YB_BASE_URL=http://host:8000/v1 YB_MODEL=my-model yellowbot --provider compat # vLLM, llama.cpp, etc.
```

Providers: `offline`, `anthropic`, `openai`, `openrouter`, `groq`, `ollama`, `lmstudio`, `compat`. If a backend call fails, the bot says so and answers offline. If a model cites a record ID that does not exist, the CLI warns you.

## Or just paste the prompt

`MASTER_PROMPT.md` is the fully assembled system prompt. It is plain text with no provider syntax, so you can paste it into any chat UI or API as the system message. `/prompt` regenerates it with whatever the current question retrieves. Source pieces live in `src/yellowbot/prompts/`:

- `master.md`: the truth-seeking core (your original prompt) plus the two-register operating frame
- `persona_yellow.md`: the voice. Add `persona_*.md` files to make new characters on the same core.

## Commands

| | |
|---|---|
| `/mode both\|front\|record` | what you get back |
| `/heat 1-5` | restrained and wry up to full oracular tabloid |
| `/story [topic]` | a front-page piece |
| `/check <claim>` | test a claim you have heard against the record |
| `/facts [id]` | browse vetted facts and their sources |
| `more` | new material on the same thread |
| `/save` `/load` `/export` `/reset` `/status` `/prompt` | session tools |

## Layout

```
src/yellowbot/
  bot.py         retrieval -> prompt -> backend -> verification -> memory
  knowledge.py   fact store + dependency-free retrieval
  prompts.py     master prompt assembly, citation check
  providers.py   Anthropic + OpenAI-compatible backends (stdlib only)
  offline.py     no-model engine with the same two-register contract
  memory.py      multi-turn state, save/load/export
  cli.py         REPL
  data/knowledge.json   21 vetted facts (high/medium/low) + 5 figurative frames
tests/           27 tests (pytest)
research/ docs/ samples/   original research archive, style guide, v0.1 samples
```

## Honest limits

- The knowledge base is only as good as `research/`. Two entries are flagged: **F18** (documentary distribution date) is single-sourced and **F19** (Beyonce tour reference) is unverified. Confirm both before relying on them.
- The offline engine can retrieve and label, but it cannot judge whether a claim is true. `/check` offline says so. Use a model backend for real comparisons.
- Retrieval is keyword-based, so unusual phrasing can miss. Tags in `knowledge.json` help.

MIT licensed. *The circuit never died. It only changed key.*
