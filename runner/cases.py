"""Case loading utilities for Kanon YAML cases."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class Case:
    """A single Kanon evaluation case loaded from YAML."""

    path: Path
    data: dict[str, Any]

    @property
    def id(self) -> str:
        return str(self.data["id"])

    @property
    def prompt(self) -> str:
        return str(self.data["prompt"])

    @property
    def category(self) -> str:
        return str(self.data["category"])

    @property
    def scoring(self) -> dict[str, Any]:
        return self.data["scoring"]


def discover_case_paths(paths: list[Path]) -> list[Path]:
    """Expand files/directories into a sorted list of case YAML paths."""

    discovered: list[Path] = []
    for path in paths:
        if path.is_dir():
            discovered.extend(path.rglob("*.yaml"))
        elif path.is_file() and path.suffix in {".yaml", ".yml"}:
            discovered.append(path)
        else:
            raise FileNotFoundError(f"No case file or directory found at {path}")
    return sorted(set(discovered))


def load_case(path: Path) -> Case:
    with path.open(encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path}: case root must be a mapping")
    return Case(path=path, data=data)


def load_cases(paths: list[Path]) -> list[Case]:
    return [load_case(path) for path in discover_case_paths(paths)]
