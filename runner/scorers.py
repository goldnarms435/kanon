"""Scoring engines for Kanon case types."""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from typing import Any, Protocol

from .cases import Case


@dataclass
class ScoreResult:
    case_id: str
    scoring_type: str
    score: float | None
    max_score: float
    passed: bool | None
    details: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class Judge(Protocol):
    def score_rubric(self, case: Case, response: str) -> ScoreResult:
        """Score a rubric case with an external judge."""


def score_case(case: Case, response: str, judge: Judge | None = None) -> ScoreResult:
    scoring_type = case.scoring.get("type")
    if scoring_type == "multiple_choice":
        return score_multiple_choice(case, response)
    if scoring_type == "exact_match":
        return score_exact_match(case, response)
    if scoring_type == "structured":
        return score_structured(case, response)
    if scoring_type == "rubric":
        if judge is None:
            max_score = float(case.scoring.get("max_score", 100))
            return ScoreResult(
                case_id=case.id,
                scoring_type="rubric",
                score=None,
                max_score=max_score,
                passed=None,
                details={
                    "error": "rubric scoring requires a judge; response captured but unscored"
                },
            )
        return judge.score_rubric(case, response)
    raise ValueError(f"{case.path}: unsupported scoring.type {scoring_type!r}")


def score_multiple_choice(case: Case, response: str) -> ScoreResult:
    scoring = case.scoring
    choices = scoring.get("choices", {})
    correct = str(scoring["correct"]).strip().upper()
    predicted = _extract_choice(response, set(choices.keys()))
    passed = predicted == correct
    return ScoreResult(
        case_id=case.id,
        scoring_type="multiple_choice",
        score=1.0 if passed else 0.0,
        max_score=1.0,
        passed=passed,
        details={"predicted": predicted, "correct": correct},
    )


def score_exact_match(case: Case, response: str) -> ScoreResult:
    scoring = case.scoring
    accepted = [str(item) for item in scoring.get("accepted_answers", [])]
    case_sensitive = bool(scoring.get("case_sensitive", False))
    match_mode = str(scoring.get("match", "substring"))

    candidate = response if case_sensitive else response.casefold()
    matched_answer: str | None = None
    for answer in accepted:
        needle = answer if case_sensitive else answer.casefold()
        if _matches(candidate, needle, match_mode):
            matched_answer = answer
            break

    passed = matched_answer is not None
    return ScoreResult(
        case_id=case.id,
        scoring_type="exact_match",
        score=1.0 if passed else 0.0,
        max_score=1.0,
        passed=passed,
        details={"matched_answer": matched_answer, "match": match_mode},
    )


def score_structured(case: Case, response: str) -> ScoreResult:
    response_folded = response.casefold()
    field_results: list[dict[str, Any]] = []
    score = 0.0
    max_score = 0.0

    for field in case.scoring.get("required_fields", []):
        name = str(field["field"])
        weight = float(field.get("weight", 1))
        accepted = [str(item) for item in field.get("accepted", [])]
        max_score += weight
        matched = [item for item in accepted if item.casefold() in response_folded]
        if matched:
            score += weight
        field_results.append(
            {
                "field": name,
                "weight": weight,
                "matched": matched,
                "passed": bool(matched),
            }
        )

    threshold = float(case.scoring.get("pass_threshold", max_score))
    return ScoreResult(
        case_id=case.id,
        scoring_type="structured",
        score=score,
        max_score=max_score,
        passed=score >= threshold,
        details={"fields": field_results, "pass_threshold": threshold},
    )


def rubric_prompt(case: Case, response: str) -> str:
    scoring = case.scoring
    criteria = json.dumps(scoring.get("criteria", []), indent=2)
    max_score = scoring.get("max_score", 100)
    return f"""You are scoring a Kanon networking benchmark response.

Return JSON only, with this exact shape:
{{
  "score": <number>,
  "max_score": {max_score},
  "passed": <true|false>,
  "rationale": "<brief explanation>",
  "criteria": {{"<criterion_id>": {{"score": <number>, "rationale": "<brief>"}}}}
}}

Case ID: {case.id}
Prompt:
{case.prompt}

Reference answer:
{case.data.get("reference_answer", "")}

Rubric criteria:
{criteria}

Candidate response:
{response}
"""


def parse_rubric_judge_result(case: Case, raw: str) -> ScoreResult:
    try:
        parsed = json.loads(_extract_json_object(raw))
    except json.JSONDecodeError as exc:
        return ScoreResult(
            case_id=case.id,
            scoring_type="rubric",
            score=None,
            max_score=float(case.scoring.get("max_score", 100)),
            passed=None,
            details={"error": f"judge returned invalid JSON: {exc}", "raw": raw},
        )

    score = float(parsed["score"])
    max_score = float(parsed.get("max_score", case.scoring.get("max_score", 100)))
    return ScoreResult(
        case_id=case.id,
        scoring_type="rubric",
        score=score,
        max_score=max_score,
        passed=bool(parsed.get("passed", score >= case.scoring.get("pass_threshold", 0))),
        details={
            "rationale": parsed.get("rationale", ""),
            "criteria": parsed.get("criteria", {}),
            "raw": raw,
        },
    )


def _extract_choice(response: str, choices: set[str]) -> str | None:
    normalized_choices = {choice.upper() for choice in choices}
    for token in re.findall(r"\b([A-Z])\b", response.upper()):
        if token in normalized_choices:
            return token
    compact = response.strip().upper()
    return compact if compact in normalized_choices else None


def _matches(candidate: str, needle: str, match_mode: str) -> bool:
    if match_mode == "equals":
        return candidate.strip() == needle.strip()
    if match_mode == "regex":
        return re.search(needle, candidate) is not None
    if match_mode == "substring":
        return needle in candidate
    raise ValueError(f"unsupported exact_match mode: {match_mode}")


def _extract_json_object(raw: str) -> str:
    stripped = raw.strip()
    if stripped.startswith("{") and stripped.endswith("}"):
        return stripped
    start = stripped.find("{")
    end = stripped.rfind("}")
    if start == -1 or end == -1 or end < start:
        return stripped
    return stripped[start : end + 1]
