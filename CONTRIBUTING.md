# Contributing to Kanon

Thank you for helping build the public networking knowledge benchmark for LLMs.

## About Kanon

The Epicurean **Kanon** (κανών) was Epicurus's term for *the criterion of true knowledge* — the standard by which a claim is judged. Epikuru Technology takes its name from the same Greek root (Epíkouros — "helper, defender"). Kanon is that criterion applied to networking expertise in large language models: a reproducible, credentialed bar for BGP path-selection, EVPN semantics, fabric design, and operator-grade troubleshooting — published independently of any single agent or vendor implementation.

## How to propose a new case

1. Read the format spec: [`spec/eval-format-v0.1.md`](spec/eval-format-v0.1.md).
2. Open a **[Case Proposal](.github/ISSUE_TEMPLATE/case-proposal.yml)** issue with a draft YAML, or submit a pull request directly if the case is ready for review.
3. Place the file at `cases/<category>/<id>.yaml` following the naming rules in the spec.

## Case submission checklist

Before opening a case PR, confirm every item below:

- [ ] `id` follows pattern `<category>-NNN` and is unique
- [ ] `prompt` is self-contained
- [ ] `reference_answer` cites a public source in `references`
- [ ] No content from paid training material (Cisco Press, INE, CBT Nuggets, etc.)
- [ ] `reviewed_by` entry from a credentialed reviewer (CCIE / JNCIE / equivalent)
- [ ] `common_wrong_answers` populated where models are known to fail
- [ ] If rubric scoring: criteria are objective, weights sum to `max_score`

See also the contributor checklist in [`spec/eval-format-v0.1.md`](spec/eval-format-v0.1.md).

## Running the runner locally

**Coming in v0.1.** The Python harness under `runner/` will ship in milestone M5. Until then, case validation is available via:

```bash
python scripts/validate_cases.py
```

## Answer key disputes

If you believe a published answer key is incorrect, open an **[Answer Dispute](.github/ISSUE_TEMPLATE/answer-key-dispute.yml)** issue with the case ID, your proposed correction, and an RFC or vendor-doc citation.

## Code of conduct

This project follows the [Contributor Covenant Code of Conduct, version 2.1](https://www.contributor-covenant.org/version/2/1/code_of_conduct.html). By participating, you agree to uphold it.

## License

By contributing to this repository, you agree that your contributions are licensed under the [Apache License, Version 2.0](LICENSE), matching the project license.
