# Owner Pricing Sandbox Apply Plan

Sandbox plan only. This file is not an import result and does not mutate live pricing data.

## Plan Metadata

- Generated at: `2026-06-29T14:58:57+00:00`
- Source CSV path: `examples\owner_pricing\fake_owner_pricing.csv`
- Baseline pricing path: `examples\owner_pricing\fake_current_pricing.csv`
- Dry-run report reference: `examples\owner_pricing\fake_preview_report.md (1955 bytes read)`
- Markdown sandbox output target: `examples\owner_pricing\fake_sandbox_apply_plan.md`
- JSON sandbox output target: `not requested`

## Summary

| Metric | Count |
| --- | ---: |
| Total rows read | 7 |
| Valid rows | 3 |
| Invalid rows | 4 |
| Duplicate keys | 1 |
| Add candidates | 1 |
| Update candidates | 1 |
| Unchanged rows | 1 |
| Skipped rows | 4 |

## Warnings

- Sandbox plan only; live import remains disabled.
- Invalid rows exist; future apply is not recommended until they are fixed.
- Duplicate material keys exist; owner/G2 review is required.

## Duplicate Material Keys

| Material key | CSV rows |
| --- | --- |
| `sample_rebar` | 3, 5 |

## Add Candidates

| Material key | Material name | Unit | Current price | New price | Changed fields |
| --- | --- | --- | ---: | ---: | --- |
| `sample_sand` | Demo Sand | m3 | - | 42.00 | - |

## Update Candidates

| Material key | Material name | Unit | Current price | New price | Changed fields |
| --- | --- | --- | ---: | ---: | --- |
| `sample_concrete` | Demo Concrete | bags | 120.00 | 125.50 | unit_price |

## Unchanged Rows

| Material key | Material name | Unit | Current price | New price | Changed fields |
| --- | --- | --- | ---: | ---: | --- |
| `sample_unchanged` | Demo Unchanged | kg | 30.00 | 30.00 | - |

## Skipped Rows

| CSV row | Material key | Reason |
| ---: | --- | --- |
| 3 | `sample_rebar` | duplicate material_key requires manual review |
| 5 | `sample_rebar` | duplicate material_key requires manual review |
| 6 | `sample_missing_unit` | missing required fields: unit |
| 7 | `sample_bad_price` | price format issue: unit_price must be a plain decimal number |

## Confirmation Checklist Before Any Future Apply

- [ ] Owner confirms the source CSV is the intended file.
- [ ] Owner confirms no real pricing sample is committed to the repository.
- [ ] G2 reviews invalid rows, duplicate keys, and skipped rows.
- [ ] G2 confirms add/update/unchanged candidates match the dry-run report.
- [ ] A future apply command, if approved, writes to sandbox output only.
- [ ] Rollback approach is documented before any production import is considered.

## Sandbox Boundaries

- This plan does not import owner pricing into live JSON.
- This plan does not update production pricing data.
- This plan is intended for owner/G2 review before any future apply command exists.
- Any future apply must use a separate reviewed command and an explicit sandbox output path.
