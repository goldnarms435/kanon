"""Command-line runner for Kanon evaluations."""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .adapters import (
    OpenAICompatibleClient,
    OpenAICompatibleJudge,
    build_case_messages,
    parse_answers_jsonl,
)
from .cache import ResponseCache
from .cases import Case, load_cases
from .scorers import ScoreResult, score_case


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    cases = load_cases([Path(path) for path in args.cases])
    answers = parse_answers_jsonl(args.responses_jsonl) if args.responses_jsonl else {}
    cache = ResponseCache(Path(args.cache) if args.cache else None)
    system_prompt = load_text_file(args.system_prompt_file)

    client = None
    if not args.dry_run and not answers:
        api_key = args.api_key or os.environ.get("OPENAI_API_KEY")
        if not api_key:
            print(
                "error: OPENAI_API_KEY or --api-key is required unless using "
                "--responses-jsonl or --dry-run",
                file=sys.stderr,
            )
            return 2
        client = OpenAICompatibleClient(
            base_url=args.base_url,
            api_key=api_key,
            model=args.model,
            timeout=args.timeout,
            temperature=args.temperature,
        )

    judge = build_judge(args)
    run_id = args.run_id or datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output_dir = Path(args.out)
    output_dir.mkdir(parents=True, exist_ok=True)

    results = []
    for case in cases:
        response = get_response(case, args, answers, cache, client, system_prompt)
        score = score_case(case, response, judge)
        results.append(build_result_row(case, response, score, args.model, run_id))
        print(format_progress(case, score))

    result_path = output_dir / f"{run_id}.jsonl"
    summary_path = output_dir / f"{run_id}-summary.json"
    write_jsonl(result_path, results)
    summary = summarize_results(results, run_id, args.model)
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print(f"\nWrote {len(results)} result(s) to {result_path}")
    print(f"Wrote summary to {summary_path}")
    if summary["unscored"] > 0:
        print(
            f"warning: {summary['unscored']} rubric result(s) are unscored; "
            "configure --judge-* to score them",
            file=sys.stderr,
        )
    return 0


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Kanon benchmark cases.")
    parser.add_argument(
        "--cases",
        nargs="+",
        default=["cases"],
        help="Case YAML files or directories (default: cases)",
    )
    parser.add_argument("--out", default="leaderboard/runs", help="Output directory")
    parser.add_argument("--run-id", help="Stable run ID for output filenames")
    parser.add_argument("--model", default="manual", help="Model name for this run")
    parser.add_argument(
        "--system-prompt-file",
        help=(
            "Optional agent profile or system prompt file to use for model calls, "
            "for example agents/ccie-network-sme-v0.1.md"
        ),
    )
    parser.add_argument(
        "--base-url",
        default=os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1"),
        help="OpenAI-compatible API base URL",
    )
    parser.add_argument("--api-key", help="OpenAI-compatible API key")
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--timeout", type=int, default=120)
    parser.add_argument(
        "--cache",
        default=".kanon-cache/responses.json",
        help="JSON response cache path; set empty string to disable",
    )
    parser.add_argument(
        "--responses-jsonl",
        help="Use pre-generated responses with rows: {case_id, response}",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Do not call a model; use each case reference_answer as the response",
    )
    parser.add_argument("--judge-model", help="OpenAI-compatible model for rubric judge")
    parser.add_argument(
        "--judge-base-url",
        default=os.environ.get("KANON_JUDGE_BASE_URL"),
        help="Judge API base URL (defaults to --base-url if --judge-model is set)",
    )
    parser.add_argument(
        "--judge-api-key",
        default=os.environ.get("KANON_JUDGE_API_KEY"),
        help="Judge API key (defaults to --api-key if --judge-model is set)",
    )
    return parser.parse_args(argv)


def build_judge(args: argparse.Namespace) -> OpenAICompatibleJudge | None:
    if not args.judge_model:
        return None
    api_key = args.judge_api_key or args.api_key or os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise SystemExit("--judge-model requires --judge-api-key, --api-key, or OPENAI_API_KEY")
    client = OpenAICompatibleClient(
        base_url=args.judge_base_url or args.base_url,
        api_key=api_key,
        model=args.judge_model,
        timeout=args.timeout,
        temperature=0.0,
    )
    return OpenAICompatibleJudge(client)


def get_response(
    case: Case,
    args: argparse.Namespace,
    answers: dict[str, str],
    cache: ResponseCache,
    client: OpenAICompatibleClient | None,
    system_prompt: str | None,
) -> str:
    if case.id in answers:
        return answers[case.id]
    if args.dry_run:
        if case.scoring.get("type") == "multiple_choice":
            return str(case.scoring["correct"])
        return str(case.data.get("reference_answer", ""))
    if client is None:
        raise RuntimeError("model client was not configured")
    prompt_for_cache = f"{system_prompt or ''}\n\0\n{case.prompt}"
    key = cache.key(model=args.model, case_id=case.id, prompt=prompt_for_cache)
    cached = cache.get(key)
    if cached is not None:
        return cached
    response = client.complete(build_case_messages(case, system_prompt=system_prompt))
    cache.set(key, response)
    return response


def load_text_file(path: str | None) -> str | None:
    if not path:
        return None
    return Path(path).read_text(encoding="utf-8")


def build_result_row(
    case: Case, response: str, score: ScoreResult, model: str, run_id: str
) -> dict[str, Any]:
    return {
        "run_id": run_id,
        "model": model,
        "case_id": case.id,
        "case_path": str(case.path.as_posix()),
        "category": case.category,
        "difficulty": case.data.get("difficulty"),
        "tags": case.data.get("tags", []),
        "response": response,
        "score": score.to_dict(),
    }


def summarize_results(results: list[dict[str, Any]], run_id: str, model: str) -> dict[str, Any]:
    scored = [
        row
        for row in results
        if row["score"]["score"] is not None and row["score"]["max_score"] > 0
    ]
    total = sum(float(row["score"]["score"]) for row in scored)
    max_total = sum(float(row["score"]["max_score"]) for row in scored)
    passed = sum(1 for row in scored if row["score"]["passed"] is True)
    return {
        "run_id": run_id,
        "model": model,
        "cases": len(results),
        "scored": len(scored),
        "unscored": len(results) - len(scored),
        "passed": passed,
        "score": total,
        "max_score": max_total,
        "percent": (total / max_total * 100) if max_total else None,
    }


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def format_progress(case: Case, score: ScoreResult) -> str:
    if score.score is None:
        return f"{case.id}: unscored ({score.scoring_type})"
    status = "PASS" if score.passed else "FAIL"
    return f"{case.id}: {status} {score.score:g}/{score.max_score:g} ({score.scoring_type})"


if __name__ == "__main__":
    raise SystemExit(main())
