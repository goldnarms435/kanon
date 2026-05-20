from __future__ import annotations

from pathlib import Path

from runner.adapters import DEFAULT_SYSTEM_PROMPT, build_case_messages
from runner.cases import Case


def make_case(scoring_type: str = "multiple_choice") -> Case:
    return Case(
        path=Path("cases/test/test-001.yaml"),
        data={
            "id": "test-001",
            "category": "test",
            "prompt": "Which route wins?",
            "reference_answer": "B",
            "scoring": {"type": scoring_type, "choices": {"A": "A", "B": "B"}},
        },
    )


def test_build_case_messages_uses_default_system_prompt() -> None:
    messages = build_case_messages(make_case())

    assert messages[0]["role"] == "system"
    assert messages[0]["content"] == DEFAULT_SYSTEM_PROMPT
    assert "single best choice letter" in messages[1]["content"]


def test_build_case_messages_accepts_agent_profile_prompt() -> None:
    profile = "You are a CCIE-level networking SME."

    messages = build_case_messages(make_case("rubric"), system_prompt=profile)

    assert messages[0]["content"] == profile
    assert "Answer concisely" in messages[1]["content"]
