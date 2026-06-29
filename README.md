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

## Owner Pricing Safety Workflow

Final import is still not implemented. G1-025 adds final import planning docs,
rollback planning, and a checklist. G1-026 adds a read-only final import
preflight checker. The current safe workflow remains:

1. Dry-run preview.
2. Sandbox apply plan.
3. Sandbox apply output.
4. Approval gate.
5. Final import planning.
6. Final import preflight checker.

## Testing
```bash
python -m unittest discover tests
```
