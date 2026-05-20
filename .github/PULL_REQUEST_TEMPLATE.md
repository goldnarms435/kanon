## Summary

<!-- Brief description of this PR -->

## Case submission checklist

Confirm every item from [CONTRIBUTING.md](../CONTRIBUTING.md):

- [ ] `id` follows pattern `<category>-NNN` and is unique
- [ ] `prompt` is self-contained
- [ ] `reference_answer` cites a public source in `references`
- [ ] No content from paid training material (Cisco Press, INE, CBT Nuggets, etc.)
- [ ] `reviewed_by` entry from a credentialed reviewer (CCIE / JNCIE / equivalent)
- [ ] `common_wrong_answers` populated where models are known to fail
- [ ] If rubric scoring: criteria are objective, weights sum to `max_score`

## Reviewer (CCIE/JNCIE)

<!-- Name or handle of credentialed reviewer who validated the answer key -->

## Validation

- [ ] `python scripts/validate_cases.py` passes locally

## Related issues

<!-- Link case proposal or answer-dispute issues, if any -->
