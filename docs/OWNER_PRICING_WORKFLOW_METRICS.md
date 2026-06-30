# Owner Pricing Workflow Metrics

This document summarizes the first owner-pricing metrics baseline from
`examples/metrics/owner_pricing_pr_metrics.csv`. It is intended for G0, G1, and
G2 review planning, not runtime behavior.

## Initial Baseline

| PR | Task | Stage | CI | Safety gate | G2 review | Merge |
| --- | --- | --- | --- | --- | --- | --- |
| #13 | G1-025 | Final import planning | unknown | not applicable | missing | merged |
| #14 | G1-026 | Read-only final import preflight | unknown | not applicable | missing | merged |
| #15 | G1-027 | Final import design gate | unknown | not applicable | missing | merged |
| #17 | G1-028 | Fake-fixture-only final import rehearsal | unknown | not applicable | missing | merged |
| #18 | G1-029 | Engineering CI foundation | fail | not applicable | missing | merged |
| #20 | G1-030 | Owner-pricing CI safety gate | fail | passed locally | missing | merged |
| #21 | G1-030-FIX | CI fixture portability fix | pass | passed locally | missing | merged |
| #23 | G1-031 | Fixture registry and golden reports | pass | passed locally | missing | merged |

## Baseline Observations

- CI became visible starting with the engineering workflow foundation.
- PR #18 and PR #20 show why merged-head CI status needs to be tracked
  separately from local validation.
- PR #21 is the first green owner-pricing CI recovery point in this baseline.
- PR #23 keeps the fixture and golden-report layer under CI and local safety
  gate validation.
- G2 review status is `missing` in the CSV when no durable review artifact is
  linked or committed. That status is a metrics signal, not a claim that review
  never happened.
- Every initial row keeps `production_behavior_changed` set to `no`.

## G2 Review Guidance

For future metrics updates, G2 should verify:

- Every added PR row has a PR number, task ID, title, branch, changed-file count,
  additions, deletions, merge status, and merge commit when merged.
- Test counts match the PR body, CI logs, or a committed validation report. If
  exact counts are not visible, the row uses `unknown`.
- CI status matches GitHub Actions at the PR head or merged head being measured.
- Safety gate status is backed by local validation output, CI output, or a
  committed report.
- G2 review status is only `PASS` or `REQUEST_CHANGES` when durable review
  evidence exists.
- `production_behavior_changed` remains `no` unless G0 approved a specific
  production behavior change in the PR scope.
- Metrics changes do not add real owner-pricing data or weaken fake-fixture,
  sandbox, approval, preflight, design-gate, fake-rehearsal, CI safety, fixture
  registry, or golden-report boundaries.

## Future Measurements

Useful follow-up metrics for later tasks:

- Time from PR open to CI pass.
- Time from CI pass to G2 review.
- Time from G2 review to G0 merge.
- Count of PRs that change source code while still preserving production
  behavior.
- Count of owner-pricing PRs with explicit safety gate evidence.
- Count of PRs with linked or committed G2 review evidence.
