# AI Asset Factory + Model Router V0.2_DEV

A core system for generating structured prompt packs and model routing plans for AI asset generation.

## Installation
```bash
pip install -e .
```

## CLI Commands
- `asset-factory demo`
- `asset-factory create --brief <path> --out <path>`
- `asset-factory route --task <type> --style <style> --quality <q> --budget <b> --speed <s>`
- `asset-factory validate --brief <path>`
- `asset-factory inspect --pack <path>`
- `asset-factory list-providers`
- `asset-factory owner-pricing-dry-run --csv <path> --report <path> [--current-pricing <path>]`
- `asset-factory owner-pricing-plan-sandbox-apply --csv <path> --plan <path> [--current-pricing <path>]`
- `asset-factory owner-pricing-apply-sandbox-output --csv <path> --output <path> [--current-pricing <path>]`
- `asset-factory owner-pricing-approve-sandbox-output --sandbox-output <path> --owner-approval <phrase> --approval-record <path>`
- `asset-factory owner-pricing-final-import-preflight --sandbox-output <path> --approval-record <path> --production-target <path> --backup-output <path> --report <path>`
- `asset-factory owner-pricing-final-import-fake-rehearsal --sandbox-output <path> --approval-record <path> --preflight-report <path> --fake-production-target <path> --fake-production-output <path> --backup-output <path> --audit-log <path> --report <path>`

## Owner Pricing Safety Workflow

Final import is still not implemented. G1-025 adds final import planning docs,
rollback planning, and a checklist. G1-026 adds a read-only final import
preflight checker. G1-027 adds the final import design gate before any future
production import implementation. G1-028 adds a fake-fixture-only final import
rehearsal; it is not production import. The current safe workflow remains:

1. Dry-run preview.
2. Sandbox apply plan.
3. Sandbox apply output.
4. Approval gate.
5. Final import planning.
6. Final import preflight checker.
7. Final import design gate.
8. Fake-fixture-only final import rehearsal.

## Testing
```bash
python -m unittest discover tests
```

## Engineering Validation

Pull requests run GitHub Actions on Python 3.12:

```bash
python -m pip install -e ".[dev]"
python -m unittest discover tests
python -m unittest discover tests -p "test_owner_pricing.py"
python scripts/check_owner_pricing_safety.py
ruff check .
```

Local recommended checks:

```bash
py -3.12 -m pip install -e ".[dev]"
py -3.12 -m unittest discover tests
py -3.12 -m unittest discover tests -p "test_owner_pricing.py"
py -3.12 scripts/check_owner_pricing_safety.py
ruff check .
git diff --check
```

Ruff is check-only in the current workflow foundation. It does not auto-fix or
enforce formatting yet. Optional pre-commit hooks are documented in
`docs/ENGINEERING_WORKFLOW.md`.

Owner-pricing-specific CI safety checks are documented in
`docs/OWNER_PRICING_CI_GATE.md`. The gate is read-only and exists to keep
dry-run, sandbox, approval, preflight, design-gate, and fake-rehearsal
boundaries machine-checked before review.

Owner-pricing fake fixtures and golden report update rules are documented in
`docs/OWNER_PRICING_FIXTURE_REGISTRY.md`,
`docs/OWNER_PRICING_GOLDEN_REPORTS.md`, and
`examples/owner_pricing/README.md`.

Owner-pricing and engineering process metrics are documented in
`docs/METRICS_BASELINE.md` and
`docs/OWNER_PRICING_WORKFLOW_METRICS.md`. The initial CSV baseline is
`examples/metrics/owner_pricing_pr_metrics.csv`.

Owner-pricing production import implementation plan v2 is documented in
`docs/OWNER_PRICING_PRODUCTION_IMPORT_IMPLEMENTATION_PLAN_V2.md`, with
approval and review checklists in
`docs/OWNER_PRICING_PRODUCTION_IMPORT_G0_APPROVAL_CHECKLIST.md` and
`docs/OWNER_PRICING_PRODUCTION_IMPORT_G2_REVIEW_CHECKLIST.md`.

Owner-pricing production import command contract and test-matrix planning are
documented in `docs/OWNER_PRICING_COMMAND_CONTRACT.md`,
`docs/OWNER_PRICING_TEST_MATRIX.md`, and
`docs/OWNER_PRICING_COMMAND_CONTRACT_G2_REVIEW.md`.

Owner-pricing fake implementation evidence packet planning is documented in
`docs/OWNER_PRICING_FAKE_IMPLEMENTATION_EVIDENCE_PACKET.md`, with G2 review
guidance in `docs/OWNER_PRICING_FAKE_IMPLEMENTATION_EVIDENCE_G2_REVIEW.md`.
