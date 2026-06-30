# Metrics Baseline

G1-032 creates the first lightweight metrics baseline for the owner-pricing
workflow and the AI-assisted engineering process. This layer is measurement,
documentation, and tooling only. It does not change owner-pricing production
behavior, add production import behavior, mutate live JSON, or add real owner
pricing data.

## Source File

The baseline CSV is:

```text
examples/metrics/owner_pricing_pr_metrics.csv
```

The initial rows cover PR #13, #14, #15, #17, #18, #20, #21, and #23. Mechanical
fields came from GitHub PR metadata and PR bodies. When a metric was not visible
in the PR metadata or PR body, the value is `unknown` or `missing`.

## Tracked Fields

| Field | Meaning |
| --- | --- |
| `pr_number` | GitHub pull request number. |
| `task_id` | G1 task identifier, such as `G1-030` or `G1-030-FIX`. |
| `title` | Pull request title. |
| `branch` | Head branch used for the pull request. |
| `workflow_category` | Broad category, such as owner-pricing or AI engineering. |
| `workflow_stage` | More specific workflow step or stage. |
| `changed_files_count` | Count reported by GitHub PR metadata. |
| `additions` / `deletions` | Line additions and deletions reported by GitHub PR metadata. |
| `changed_files` | Semicolon-separated file list reported by GitHub PR metadata. |
| `unit_test_count` | Reported full unit test count, `not_run`, or `unknown`. |
| `owner_pricing_test_count` | Reported owner-pricing-specific test count, or `unknown`. |
| `ci_status` | `pass`, `fail`, `pending`, or `unknown`. |
| `safety_gate_status` | Owner-pricing safety gate result when available. |
| `g2_review_status` | `PASS`, `REQUEST_CHANGES`, `missing`, or `unknown`. |
| `merge_status` | Merge state recorded for the PR. |
| `merge_commit` | Merge commit SHA when merged. |
| `docs_changed` | `yes` when documentation surfaces changed. |
| `tests_changed` | `yes` when files under `tests/` changed. |
| `src_changed` | `yes` when files under `src/` changed. |
| `workflow_changed` | `yes` when CI, scripts, packaging config, or fixture policy changed. |
| `examples_changed` | `yes` when files under `examples/` changed. |
| `production_behavior_changed` | Defaults to `no` unless G0 explicitly approves otherwise. |
| `notes` | Short review note for context that does not fit a strict field. |

## Status Rules

- Use `unknown` instead of guessing a value.
- Use `missing` for G2 review status when no durable G2 review evidence is
  linked in the PR metadata, PR body, or committed project documentation.
- Use `not_applicable` for the owner-pricing safety gate before that gate
  existed.
- Keep `production_behavior_changed` as `no` unless G0 explicitly approves and
  the PR body names the production behavior change.
- If a PR changes source code but only adds read-only, fake-only, safety, or
  documentation tooling, production behavior is still `no`.

## Update Procedure

1. Add or update rows in `examples/metrics/owner_pricing_pr_metrics.csv`.
2. Keep the row tied to durable evidence: PR metadata, PR body, CI status, or a
   committed review artifact.
3. If exact test counts are not visible, write `unknown`.
4. If a future G2 review happens outside GitHub review UI, link the review
   artifact in the PR body or commit it before marking `g2_review_status`.
5. Run:

```bash
py -3.12 -B scripts/collect_pr_metrics.py --validate
py -3.12 -B -m unittest tests.test_metrics_baseline
```

## Safety Boundary

This baseline must remain read-only. It must not:

- Add production import behavior.
- Add real owner-pricing data.
- Mutate live JSON.
- Weaken the owner-pricing safety gate.
- Require network access from tests.
- Add non-standard-library runtime dependencies.
