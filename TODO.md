# TODO

## Done in v0.2
- [x] Multi-turn memory, save/load/export
- [x] Provider-agnostic backend (offline, Anthropic, OpenAI-compatible incl. Ollama/LM Studio)
- [x] Master prompt + persona modules, fact/figure two-register contract
- [x] Retrieval over a vetted, confidence-tagged knowledge base
- [x] Citation verification (flags IDs a model invented)
- [x] pytest suite, pyproject, argparse CLI

## Next
- [ ] Streaming output
- [ ] Web UI (FastAPI or a single static page that calls the same `YellowBot`)
- [ ] More sources: add primary documents to `data/knowledge.json` (Ferguson papers, oral histories, Smithsonian)
- [ ] Verify F18 (documentary date) and F19 (Beyonce tour) against primary sources, then upgrade or drop them
- [ ] Embedding-based retrieval option
- [ ] Additional personas (`prompts/persona_*.md`) on the same master prompt
