# Owner Pricing Sandbox Apply Output

This workflow writes a sandbox-only pricing output file from an owner pricing
CSV. It is still not a live import workflow and it does not update production
pricing data.

## What This Command Does

`asset-factory owner-pricing-apply-sandbox-output` reads an owner pricing CSV,
optionally compares it with a current pricing CSV or JSON snapshot, optionally
references the sandbox apply plan from G1-022, and writes a sandbox pricing JSON
output to an explicit path.

The sandbox output includes:

- Source CSV path.
- Baseline pricing path, when provided.
- Sandbox apply plan reference, when provided.
- Generated timestamp.
- Added materials.
- Updated materials.
- Unchanged materials.
- Retained baseline-only materials.
- Skipped invalid rows.
- Duplicate material key warnings.
- A clear sandbox-only notice.

## What This Command Does Not Do

- It does not mutate live JSON.
- It does not mutate production pricing data.
- It does not write to live, prod, production, config, data, or src paths.
- It does not overwrite an existing output unless `--overwrite` is provided.
- It does not enable owner approval or final import.

## Difference From Dry-run And Plan

The dry-run command answers what would change:

```bash
asset-factory owner-pricing-dry-run \
  --csv <owner-pricing.csv> \
  --current-pricing <current-pricing.csv-or-json> \
  --report output/owner_pricing_dry_run_preview.md
```

The sandbox apply plan answers what needs review before an apply step:

```bash
asset-factory owner-pricing-plan-sandbox-apply \
  --csv <owner-pricing.csv> \
  --current-pricing <current-pricing.csv-or-json> \
  --plan output/owner_pricing_sandbox_apply_plan.md
```

The sandbox apply output writes the reviewed sandbox artifact, but still only to
a sandbox path:

```bash
asset-factory owner-pricing-apply-sandbox-output \
  --csv <owner-pricing.csv> \
  --current-pricing <current-pricing.csv-or-json> \
  --sandbox-apply-plan output/owner_pricing_sandbox_apply_plan.md \
  --output output/owner_pricing_sandbox_output.json \
  --summary-report output/owner_pricing_sandbox_output_summary.md
```

Optional machine-readable summary:

```bash
asset-factory owner-pricing-apply-sandbox-output \
  --csv <owner-pricing.csv> \
  --current-pricing <current-pricing.csv-or-json> \
  --sandbox-apply-plan output/owner_pricing_sandbox_apply_plan.md \
  --output output/owner_pricing_sandbox_output.json \
  --summary-json output/owner_pricing_sandbox_output_summary.json
```

## Where Sandbox Output Should Go

Use ignored local sandbox folders for real owner data:

- `output/owner_pricing/`
- `outputs/owner_pricing/`
- `owner_pricing_private/`

Do not write sandbox output into:

- `src/`
- `config/`
- `data/`
- `live/`
- `prod/`
- `production/`

Do not name the sandbox output like a live pricing file, such as
`pricing.json`, `material_pricing.json`, or `owner_pricing.json`.

## Owner Inspection Checklist

- Confirm the source CSV path is the intended owner file.
- Confirm the baseline path is the intended current pricing snapshot.
- Review every added material.
- Review every updated material and changed field.
- Review unchanged materials for accidental no-op rows.
- Review skipped invalid rows.
- Review duplicate material keys before any future import discussion.
- Confirm the sandbox output path is not a live or production path.

## Fake Sample

The repository includes fake-only sample inputs and output:

- `examples/owner_pricing/fake_owner_pricing.csv`
- `examples/owner_pricing/fake_current_pricing.csv`
- `examples/owner_pricing/fake_sandbox_apply_plan.md`
- `examples/owner_pricing/fake_sandbox_pricing_output.json`

Regenerate the fake sandbox output:

```bash
asset-factory owner-pricing-apply-sandbox-output \
  --csv examples/owner_pricing/fake_owner_pricing.csv \
  --current-pricing examples/owner_pricing/fake_current_pricing.csv \
  --sandbox-apply-plan examples/owner_pricing/fake_sandbox_apply_plan.md \
  --output examples/owner_pricing/fake_sandbox_pricing_output.json \
  --overwrite
```

## Why Final Import Is Still Disabled

G1-023 produces a sandbox output file only. The final owner approval gate and
production import are intentionally left for a future G0-approved task. This
keeps owner review, QA review, rollback planning, and production mutation as
separate decisions.
