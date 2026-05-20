"""Model adapters for the Kanon runner."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any

from .cases import Case
from .scorers import ScoreResult, parse_rubric_judge_result, rubric_prompt


class AdapterError(RuntimeError):
    """Raised when a model adapter call fails."""


@dataclass(frozen=True)
class OpenAICompatibleClient:
    """Minimal OpenAI-compatible chat completions client.

    Works with OpenAI-compatible APIs that expose `/chat/completions`, including
    many local gateways and hosted inference providers.
    """

    base_url: str
    api_key: str
    model: str
    timeout: int = 120
    temperature: float = 0.0

    def complete(self, messages: list[dict[str, str]]) -> str:
        url = self.base_url.rstrip("/") + "/chat/completions"
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
        }
        request = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                data = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise AdapterError(f"model call failed with HTTP {exc.code}: {body}") from exc
        except OSError as exc:
            raise AdapterError(f"model call failed: {exc}") from exc

        try:
            return str(data["choices"][0]["message"]["content"])
        except (KeyError, IndexError, TypeError) as exc:
            raise AdapterError(f"unexpected chat completion response: {data}") from exc


class OpenAICompatibleJudge:
    def __init__(self, client: OpenAICompatibleClient) -> None:
        self.client = client

    def score_rubric(self, case: Case, response: str) -> ScoreResult:
        raw = self.client.complete(
            [
                {
                    "role": "system",
                    "content": "You are a strict benchmark judge. Return JSON only.",
                },
                {"role": "user", "content": rubric_prompt(case, response)},
            ]
        )
        return parse_rubric_judge_result(case, raw)


DEFAULT_SYSTEM_PROMPT = (
    "You are being evaluated on expert networking knowledge. "
    "Do not use external tools. Follow the requested output format."
)


def build_case_messages(case: Case, system_prompt: str | None = None) -> list[dict[str, str]]:
    scoring_type = case.scoring.get("type")
    if scoring_type == "multiple_choice":
        instruction = (
            "Your first line must contain exactly one choice letter and nothing "
            "else, for example: B. After that first line, include a concise "
            "one-sentence explanation."
        )
    else:
        instruction = "Answer concisely but include enough reasoning to be scored."
    return [
        {
            "role": "system",
            "content": system_prompt or DEFAULT_SYSTEM_PROMPT,
        },
        {"role": "user", "content": f"{case.prompt}\n\n{instruction}"},
    ]


def parse_answers_jsonl(path: str) -> dict[str, str]:
    answers: dict[str, str] = {}
    with open(path, encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            row: dict[str, Any] = json.loads(line)
            try:
                answers[str(row["case_id"])] = str(row["response"])
            except KeyError as exc:
                raise ValueError(
                    f"{path}:{line_number}: expected keys case_id and response"
                ) from exc
    return answers
