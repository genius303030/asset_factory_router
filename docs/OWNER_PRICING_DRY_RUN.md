# Owner Pricing Import Dry-run

This workflow validates an owner material pricing CSV and writes a preview
report. It is a dry-run only workflow: it does not import rows, does not mutate
live JSON, and does not update production pricing data.

## Command

```bash
asset-factory owner-pricing-dry-run --csv <owner-pricing.csv> --report <preview-report.md>
```

Optional read-only comparison snapshot:

```bash
asset-factory owner-pricing-dry-run \
  --csv <owner-pricing.csv> \
  --current-pricing <current-pricing.csv-or-json> \
  --report <preview-report.md>
```

## Required CSV Fields

The owner pricing CSV must include:

| Field | Purpose |
| --- | --- |
| `material_key` | Stable material identifier used for duplicate checks and comparison. |
| `material_name` | Human-readable material name for the report. |
| `unit` | Pricing unit, such as `kg`, `m3`, `pcs`, or `bags`. |
| `unit_price` | Plain decimal price, such as `120`, `120.00`, or `120.50`. |

## Preview Report Includes

- CSV rows read.
- Valid and invalid row counts.
- Duplicate material keys.
- Missing required fields.
- Price format issues.
- Materials that would be added.
- Materials that would be updated.
- Materials that would be unchanged.

## Fake Sample

The repository includes fake-only sample files:

- `examples/owner_pricing/fake_owner_pricing.csv`
- `examples/owner_pricing/fake_current_pricing.csv`
- `examples/owner_pricing/fake_preview_report.md`

Regenerate the fake preview report:

```bash
asset-factory owner-pricing-dry-run \
  --csv examples/owner_pricing/fake_owner_pricing.csv \
  --current-pricing examples/owner_pricing/fake_current_pricing.csv \
  --report examples/owner_pricing/fake_preview_report.md
```

## Safety Rules

- Do not commit real owner pricing CSV files.
- Keep real owner pricing files in ignored private paths, such as
  `owner_pricing_private/` or `input/owner_pricing/private/`.
- Use output paths under `output/` or `outputs/` for real local reports because
  those folders are ignored.
- This command writes only the requested markdown preview report.
- This command does not provide an import/apply mode.
