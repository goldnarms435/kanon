from __future__ import annotations

from pathlib import Path

from runner.cases import Case
from runner.scorers import (
    parse_rubric_judge_result,
    score_exact_match,
    score_multiple_choice,
    score_structured,
)


def make_case(case_id: str, scoring: dict) -> Case:
    return Case(
        path=Path(f"cases/test/{case_id}.yaml"),
        data={
            "id": case_id,
            "category": "test",
            "prompt": "prompt",
            "reference_answer": "reference",
            "scoring": scoring,
        },
    )


def test_multiple_choice_extracts_first_choice_letter() -> None:
    case = make_case(
        "bgp-999",
        {
            "type": "multiple_choice",
            "choices": {"A": "wrong", "B": "right"},
            "correct": "B",
        },
    )

    result = score_multiple_choice(case, "B. Route B wins on AS-path.")

    assert result.passed is True
    assert result.score == 1.0
    assert result.details["predicted"] == "B"


def test_exact_match_substring_case_insensitive() -> None:
    case = make_case(
        "evpn-999",
        {
            "type": "exact_match",
            "accepted_answers": ["MAC/IP advertisement"],
            "case_sensitive": False,
            "match": "substring",
        },
    )

    result = score_exact_match(case, "This is a mac/ip advertisement route.")

    assert result.passed is True
    assert result.details["matched_answer"] == "MAC/IP advertisement"


def test_exact_match_regex() -> None:
    case = make_case(
        "theory-999",
        {
            "type": "exact_match",
            "accepted_answers": [r"type[- ]?2"],
            "case_sensitive": False,
            "match": "regex",
        },
    )

    result = score_exact_match(case, "Answer: Type 2.")

    assert result.passed is True


def test_structured_sums_field_weights() -> None:
    case = make_case(
        "evpn-998",
        {
            "type": "structured",
            "required_fields": [
                {"field": "route_type", "accepted": ["Type-2"], "weight": 20},
                {"field": "esi", "accepted": ["single-homed"], "weight": 30},
                {"field": "missing", "accepted": ["not present"], "weight": 50},
            ],
            "pass_threshold": 50,
        },
    )

    result = score_structured(case, "It is Type-2 and the all-zero ESI is single-homed.")

    assert result.score == 50
    assert result.max_score == 100
    assert result.passed is True


def test_parse_rubric_judge_result_accepts_json_wrapped_in_text() -> None:
    case = make_case(
        "bgp-998",
        {"type": "rubric", "max_score": 100, "pass_threshold": 70},
    )

    result = parse_rubric_judge_result(
        case,
        'Here is the result: {"score": 80, "max_score": 100, "passed": true, '
        '"rationale": "solid", "criteria": {"x": {"score": 80}}}',
    )

    assert result.score == 80
    assert result.passed is True
    assert result.details["rationale"] == "solid"
