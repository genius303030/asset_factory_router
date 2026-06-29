# Owner Pricing Sandbox Apply Plan

This workflow turns owner pricing dry-run data into a reviewable sandbox apply
plan. It is still not a live import workflow.

## What This Command Does

`asset-factory owner-pricing-plan-sandbox-apply` reads an owner pricing CSV,
optionally compares it with a current pricing CSV or JSON snapshot, and writes a
markdown sandbox apply plan to an explicit output path.

The plan includes:

- Source CSV path.
- Baseline pricing path, when provided.
- Generated timestamp.
- Total rows read.
- Valid and invalid row counts.
- Duplicate material keys.
- Add, update, and unchanged candidates.
- Skipped rows.
- Warnings.
- Exact sandbox output target.
- Confirmation checklist before any future apply.

## What This Command Does Not Do

- It does not import owner pricing into live JSON.
- It does not mutate production pricing data.
- It does not create a production-ready apply file.
- It does not overwrite an existing plan unless `--overwrite` is provided.
- It does not enable formal import.

## Difference From Dry-run

The dry-run report answers: what rows are valid, invalid, added, updated, or
unchanged.

The sandbox apply plan answers: what would need owner/G2 review before a future
sandbox apply is even considered.

## Command

```bash
asset-factory owner-pricing-plan-sandbox-apply \
  --csv <owner-pricing.csv> \
  --current-pricing <current-pricing.csv-or-json> \
  --plan output/owner_pricing_sandbox_apply_plan.md
```

Optional dry-run report reference:

```bash
asset-factory owner-pricing-plan-sandbox-apply \
  --csv <owner-pricing.csv> \
  --current-pricing <current-pricing.csv-or-json> \
  --dry-run-report output/owner_pricing_dry_run_preview.md \
  --plan output/owner_pricing_sandbox_apply_plan.md
```

Optional JSON plan:

```bash
asset-factory owner-pricing-plan-sandbox-apply \
  --csv <owner-pricing.csv> \
  --current-pricing <current-pricing.csv-or-json> \
  --plan output/owner_pricing_sandbox_apply_plan.md \
  --plan-json output/owner_pricing_sandbox_apply_plan.json
```

If a plan file already exists, rerun only when intentionally replacing a local
sandbox output:

```bash
asset-factory owner-pricing-plan-sandbox-apply \
  --csv <owner-pricing.csv> \
  --current-pricing <current-pricing.csv-or-json> \
  --plan output/owner_pricing_sandbox_apply_plan.md \
  --overwrite
```

## Owner Review Checklist

- Confirm the source CSV is the intended file.
- Confirm the current pricing snapshot is the intended baseline.
- Review every invalid row.
- Review every duplicate material key.
- Review add and update candidates against the dry-run report.
- Confirm the plan output path is sandbox/private, not live or production.
- Keep live import disabled until a separate G0-approved task exists.

## Intentionally Blocked Actions

- Missing `--plan` output path.
- Writing plan output into known live or production-looking paths, such as
  `src/`, `config/`, `data/`, `prod/`, `production/`, or `live/`.
- Writing directly to common pricing filenames such as `pricing.json` or
  `material_pricing.json`.
- Overwriting existing plan files without `--overwrite`.

## Fake Sample

The repository includes fake sample inputs and output:

- `examples/owner_pricing/fake_owner_pricing.csv`
- `examples/owner_pricing/fake_current_pricing.csv`
- `examples/owner_pricing/fake_sandbox_apply_plan.md`

Regenerate the fake sample:

```bash
asset-factory owner-pricing-plan-sandbox-apply \
  --csv examples/owner_pricing/fake_owner_pricing.csv \
  --current-pricing examples/owner_pricing/fake_current_pricing.csv \
  --dry-run-report examples/owner_pricing/fake_preview_report.md \
  --plan examples/owner_pricing/fake_sandbox_apply_plan.md \
  --overwrite
```
