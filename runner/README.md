# Kanon Runner

The runner executes Kanon YAML cases, collects model responses, scores them, and
writes reproducible JSONL outputs for leaderboard ingestion.

Status: milestone M5 initial implementation.

## Install

```bash
python -m pip install -e ".[dev]"
```

## Validate Cases

```bash
python scripts/validate_cases.py
```

## Score Pre-Generated Responses

Use this mode when another harness has already called a model:

```bash
python -m runner \
  --model manual-baseline \
  --cases cases/bgp \
  --responses-jsonl responses.jsonl \
  --out leaderboard/runs
```

`responses.jsonl` rows must look like:

```json
{"case_id": "bgp-001", "response": "B. Route B wins on shorter AS-path."}
```

For multiple-choice cases, the runner scores the first valid choice letter it can
extract from the response. Model prompts require the first line to contain
exactly one choice letter so runs measure the case answer rather than prose
formatting.

## Run an OpenAI-Compatible Model

The runner calls `/chat/completions` on the configured base URL:

```bash
OPENAI_API_KEY=... python -m runner \
  --model gpt-4.1 \
  --base-url https://api.openai.com/v1 \
  --cases cases \
  --out leaderboard/runs
```

Compatible local or hosted gateways can be used by changing `--base-url`.

## Run with the CCIE Agent Profile

Kanon includes a first-pass CCIE networking SME agent profile at
`agents/ccie-network-sme-v0.1.md`. Use it as the system prompt for benchmark
runs:

```bash
OPENAI_API_KEY=... python -m runner \
  --model gpt-4.1 \
  --system-prompt-file agents/ccie-network-sme-v0.1.md \
  --cases cases \
  --out leaderboard/runs
```

## Rubric Scoring

Rubric cases require a judge model. Without one, the runner records the model
response and marks rubric scores as unscored.

```bash
OPENAI_API_KEY=... KANON_JUDGE_API_KEY=... python -m runner \
  --model gpt-4.1 \
  --judge-model claude-opus-4-5 \
  --cases cases \
  --out leaderboard/runs
```

If the judge uses a different endpoint:

```bash
KANON_JUDGE_BASE_URL=https://example.com/v1
```

## Dry Run

Smoke-test discovery, deterministic scorers, and output writing without calling
any external model:

```bash
python -m runner --dry-run --model reference-answer --cases cases --out leaderboard/runs
```

Rubric cases are intentionally unscored in dry-run mode unless a judge is
configured.

## Pass Thresholds

- `multiple_choice`: pass if the extracted letter equals `scoring.correct`.
- `exact_match`: pass if one accepted answer matches under the case's declared
  match mode.
- `structured`: pass if the weighted score is at least `pass_threshold`; when a
  case omits `pass_threshold`, the default is `70%` of summed field weights.
- `rubric`: pass/fail comes from the judge JSON, typically using the case's
  `pass_threshold`.

## Outputs

Each run writes:

- `<run-id>.jsonl` — one row per case, including response and score details
- `<run-id>-summary.json` — aggregate counts and score percentage for scored cases

By default outputs go to `leaderboard/runs/`, which is ignored by Git until the
leaderboard milestone defines which runs should be committed.
