#!/usr/bin/env python3
"""Validate Kanon case YAML files under cases/."""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

REQUIRED_FIELDS = (
    "id",
    "version_introduced",
    "category",
    "difficulty",
    "tags",
    "prompt",
    "scoring",
    "reference_answer",
    "author",
    "created_at",
)

VALID_SCORING_TYPES = {
    "multiple_choice",
    "exact_match",
    "structured",
    "rubric",
}


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def validate_case(path: Path, data: object) -> list[str]:
    errors: list[str] = []

    if not isinstance(data, dict):
        return [f"{path}: root must be a mapping"]

    for field in REQUIRED_FIELDS:
        if field not in data:
            errors.append(f"{path}: missing required field '{field}'")

    case_id = data.get("id")
    expected_id = path.stem
    if isinstance(case_id, str) and case_id != expected_id:
        errors.append(
            f"{path}: id '{case_id}' does not match filename '{expected_id}'"
        )

    scoring = data.get("scoring")
    if scoring is None:
        return errors

    if not isinstance(scoring, dict):
        errors.append(f"{path}: scoring must be a mapping")
        return errors

    scoring_type = scoring.get("type")
    if scoring_type not in VALID_SCORING_TYPES:
        errors.append(
            f"{path}: scoring.type must be one of "
            f"{sorted(VALID_SCORING_TYPES)}, got {scoring_type!r}"
        )

    return errors


def main() -> int:
    cases_dir = repo_root() / "cases"
    yaml_files = sorted(cases_dir.rglob("*.yaml"))

    if not yaml_files:
        print("No case files found; validation passed.")
        return 0

    all_errors: list[str] = []

    for path in yaml_files:
        try:
            with path.open(encoding="utf-8") as handle:
                data = yaml.safe_load(handle)
        except yaml.YAMLError as exc:
            all_errors.append(f"{path}: invalid YAML: {exc}")
            continue
        except OSError as exc:
            all_errors.append(f"{path}: could not read file: {exc}")
            continue

        all_errors.extend(validate_case(path, data))

    if all_errors:
        print("Case validation failed:\n")
        for error in all_errors:
            print(f"  - {error}")
        return 1

    print(f"Validated {len(yaml_files)} case file(s); all passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
