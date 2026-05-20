# Kanon

**The networking knowledge benchmark for LLMs and agents.**

Status: v0.1 — seed release (15 cases, BGP path-selection + EVPN focus).
Owner: Epikuru Technology.
License: Apache-2.0.

## What this is

Kanon measures how well an LLM (or LLM-powered agent) can reason about real, operator-grade networking problems: BGP best-path traps, EVPN control-plane troubleshooting, route-type semantics, and the kinds of edge cases that separate a CCIE from a confident generalist.

Every case has:
- A canonical answer key.
- A scoring contract (multiple-choice, exact-match, structured, or rubric).
- A category, difficulty, and tags for slicing the leaderboard.
- References to RFCs and public vendor docs (never paid material).

## Why "Kanon"

The Epicurean **Kanon** (κανών) was Epicurus's term for *the criterion of true knowledge* — the standard by which a claim is judged. A benchmark is, literally, a kanon. Epikuru Technology takes its name from the same root (Epíkouros — "helper, defender"), and this benchmark is the kanon for networking expertise in LLMs.

## Why it exists

Generalist LLMs are mediocre at networking depth. They confabulate `show` output, mis-walk the BGP decision process, hallucinate EVPN behavior, and confidently propose wrong configs. None of the existing public LLM benchmarks measure this domain rigorously.

Kanon is designed to be **published first** — before any networking agent ships against it — so the scoreboard exists independently of any particular implementation, and contributors compete on a shared, reproducible bar.

## Repository layout

```
/spec/                   Eval format spec and schema.
/cases/<category>/       One YAML per case.
/rubrics/                Judge prompts for rubric-scored cases.
/runner/                 (v0.1.x) Python harness for scoring models.
/leaderboard/            (v0.1.x) Versioned baseline runs.
```

## v0.1 seed contents

**15 cases:**
- 10 BGP path-selection cases (`/cases/bgp/bgp-001.yaml` through `bgp-010.yaml`)
- 5 EVPN cases (`/cases/evpn/evpn-001.yaml` through `evpn-005.yaml`)

## Reading order for reviewers

1. `spec/eval-format-v0.1.md` — the format contract.
2. `cases/bgp/bgp-001.yaml` — minimal multiple-choice example.
3. `cases/bgp/bgp-009.yaml` — rubric-scored example.
4. `cases/evpn/evpn-005.yaml` — full troubleshooting case with diagnostic ordering.
5. `rubrics/standard-rubric-v0.1.md` — judge prompt for rubric cases.

## Roadmap to v0.1 public release

- [ ] CCIE editor validation pass on the 15 seed cases.
- [ ] Expand to 60–80 cases (~45 BGP, ~25 EVPN, ~10 mixed troubleshooting).
- [ ] Hold back ~25% as private contamination set.
- [ ] Build runner (Python, OpenAI-compatible endpoint adapter).
- [ ] Run baselines: Claude (Opus/Sonnet), GPT frontier, Llama-70B.
- [ ] Publish leaderboard + format spec PR template + contribution guide.

## Contributing

See `spec/eval-format-v0.1.md` § "Contributor checklist."
