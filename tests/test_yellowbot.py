import json

import pytest

from yellowbot import KnowledgeBase, YellowBot
from yellowbot.memory import Conversation
from yellowbot.prompts import build_system_prompt, unknown_citations
from yellowbot.providers import ProviderError, make_provider


@pytest.fixture
def kb():
    return KnowledgeBase.load()


class FakeProvider:
    name = "fake"
    model = "fake-1"

    def __init__(self, reply="## THE RECORD\n- Fergusons. [F04, high]"):
        self.reply, self.calls = reply, []

    def chat(self, system, messages):
        self.calls.append((system, messages))
        return self.reply


class BrokenProvider:
    name = "broken"

    def chat(self, system, messages):
        raise ProviderError("boom")


# knowledge ---------------------------------------------------------------------------
def test_kb_integrity(kb):
    ids = [f.id for f in kb.facts]
    assert len(ids) == len(set(ids))
    assert all(f.confidence in {"high", "medium", "low"} for f in kb.facts)


def test_search_finds_ferguson(kb):
    assert kb.search("Who were the Ferguson brothers?")[0].id == "F04"


def test_search_plural_and_apostrophe(kb):
    assert any(f.id == "F02" for f in kb.search("why are they called chitlins?"))


def test_search_nothing(kb):
    assert kb.search("quantum computing") == []
    assert kb.search("") == []


# prompt ------------------------------------------------------------------------------
def test_prompt_fills_every_placeholder(kb):
    p = build_system_prompt(kb.search("Bobby Rush"), kb.figures, "both", 4)
    assert "{{" not in p
    assert "truth-seeking" in p and "[F17, medium]" in p and "(G3)" in p
    assert "HEAT: 4 of 5" in p


def test_prompt_empty_record_says_so(kb):
    assert "Nothing in the vetted record" in build_system_prompt([], kb.figures)


def test_prompt_rejects_bad_mode(kb):
    with pytest.raises(ValueError):
        build_system_prompt([], kb.figures, mode="loud")


def test_unknown_citations(kb):
    assert unknown_citations("ok [F04, high] bad [F99, high]", kb.known_ids()) == {"F99"}


# offline bot -------------------------------------------------------------------------
def test_offline_has_both_registers_and_cites(kb):
    r = YellowBot(kb, seed=1).ask("Who were the Ferguson brothers?")
    assert "## THE FRONT PAGE" in r.text and "## THE RECORD" in r.text and "[F04, high]" in r.text


def test_offline_modes(kb):
    b = YellowBot(kb, seed=1)
    assert "FRONT PAGE" not in b.ask("Apollo", mode="record").text
    assert "THE RECORD" not in b.ask("Apollo", mode="front").text


def test_offline_does_not_invent_outside_record(kb):
    r = YellowBot(kb, seed=1).ask("tell me about quantum computing")
    assert "Nothing in the vetted record" in r.text and r.fact_ids == []


def test_heat_changes_length(kb):
    lo = YellowBot(kb, heat=1, seed=5).ask("Bobby Rush", mode="front").text
    hi = YellowBot(kb, heat=5, seed=5).ask("Bobby Rush", mode="front").text
    assert len(hi) > len(lo)


def test_more_gives_new_facts(kb):
    b = YellowBot(kb, seed=1)
    first = b.ask("Bobby Rush").fact_ids
    second = b.ask("more").fact_ids
    assert not set(first) & set(second)


def test_check_flags_figurative(kb):
    out = YellowBot(kb).check("the blues was encrypted code").text
    assert "FIGURATIVE" in out and "G3" in out


def test_check_unsupported(kb):
    assert "UNSUPPORTED" in YellowBot(kb).check("quantum teleportation").text


def test_empty_input(kb):
    assert "empty" in YellowBot(kb).ask("   ").text


def test_input_truncated(kb):
    p = FakeProvider()
    YellowBot(kb, provider=p).ask("a" * 10_000)
    assert len(p.calls[0][1][-1]["content"]) == 2000


# llm path ----------------------------------------------------------------------------
def test_llm_gets_system_prompt_and_history(kb):
    p = FakeProvider()
    b = YellowBot(kb, provider=p)
    b.ask("Who were the Fergusons?")
    b.ask("and the Apollo?")
    system, msgs = p.calls[1]
    assert "[F07" in system  # retrieval ran for the second turn
    assert [m["role"] for m in msgs] == ["user", "assistant", "user"]


def test_llm_fabricated_citation_warns(kb):
    r = YellowBot(kb, provider=FakeProvider("Facts [F99, high]")).ask("Apollo")
    assert r.warnings and "F99" in r.warnings[0] and r.backend == "fake"


def test_llm_failure_falls_back_offline(kb):
    r = YellowBot(kb, provider=BrokenProvider(), seed=1).ask("Apollo")
    assert r.backend == "offline" and r.warnings and "THE RECORD" in r.text


# memory ------------------------------------------------------------------------------
def test_window_starts_on_user():
    c = Conversation(max_turns=1)
    for i in range(3):
        c.add_user(f"u{i}"), c.add_assistant(f"a{i}")
    assert c.window() == [{"role": "user", "content": "u2"}, {"role": "assistant", "content": "a2"}]


def test_save_load_roundtrip(tmp_path, kb):
    b = YellowBot(kb, seed=1)
    b.ask("Apollo")
    path = b.conv.save(tmp_path / "s.json")
    c = Conversation.load(path)
    assert c.turns == b.conv.turns and c.shown_fact_ids == b.conv.shown_fact_ids
    assert "Apollo" in c.to_markdown()
    json.loads(path.read_text())


# providers ---------------------------------------------------------------------------
def test_make_provider_offline_default(monkeypatch):
    monkeypatch.delenv("YB_PROVIDER", raising=False)
    assert make_provider() is None


def test_make_provider_requires_keys(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("YB_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(ProviderError):
        make_provider("anthropic")
    with pytest.raises(ProviderError):
        make_provider("openai")
    with pytest.raises(ProviderError):
        make_provider("nope")


def test_ollama_needs_no_key(monkeypatch):
    p = make_provider("ollama", model="x")
    assert p.base_url.endswith("11434/v1") and p.api_key is None


def test_openai_compat_request_shape(monkeypatch):
    from yellowbot import providers

    seen = {}

    def fake_post(url, headers, body, timeout):
        seen.update(url=url, headers=headers, body=body)
        return {"choices": [{"message": {"content": " hi "}}]}

    monkeypatch.setattr(providers, "_post", fake_post)
    out = providers.OpenAICompatProvider("t", "http://x/v1/", "k", "m").chat("SYS", [{"role": "user", "content": "q"}])
    assert out == "hi" and seen["url"] == "http://x/v1/chat/completions"
    assert seen["body"]["messages"][0] == {"role": "system", "content": "SYS"}


def test_anthropic_request_shape(monkeypatch):
    from yellowbot import providers

    seen = {}

    def fake_post(url, headers, body, timeout):
        seen.update(headers=headers, body=body)
        return {"content": [{"type": "text", "text": "yo"}]}

    monkeypatch.setattr(providers, "_post", fake_post)
    out = providers.AnthropicProvider("k", "m").chat("SYS", [{"role": "user", "content": "q"}])
    assert out == "yo" and seen["body"]["system"] == "SYS" and seen["headers"]["x-api-key"] == "k"
