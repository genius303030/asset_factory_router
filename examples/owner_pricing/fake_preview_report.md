# Owner Pricing Import Dry-run Preview

Dry-run only. No live JSON or production pricing data was mutated.

## Input

- Owner pricing CSV: `examples\owner_pricing\fake_owner_pricing.csv`
- Current pricing snapshot: `examples\owner_pricing\fake_current_pricing.csv`

## Summary

| Metric | Count |
| --- | ---: |
| CSV rows read | 7 |
| Valid rows | 3 |
| Invalid rows | 4 |
| Current pricing records read | 3 |
| Duplicate material keys | 1 |
| Missing required field rows | 1 |
| Price format issue rows | 1 |
| Materials that would be added | 1 |
| Materials that would be updated | 1 |
| Materials that would be unchanged | 1 |

## Duplicate Material Keys

| Material key | CSV rows |
| --- | --- |
| `sample_rebar` | 3, 5 |

## Missing Required Fields

| CSV row | Material key | Missing fields |
| ---: | --- | --- |
| 6 | `sample_missing_unit` | unit |

## Price Format Issues

| CSV row | Material key | Value | Issue |
| ---: | --- | --- | --- |
| 7 | `sample_bad_price` | `abc` | unit_price must be a plain decimal number |

## Materials That Would Be Added

| Material key | Material name | Unit | Current price | New price | Changed fields |
| --- | --- | --- | ---: | ---: | --- |
| `sample_sand` | Demo Sand | m3 | - | 42.00 | - |

## Materials That Would Be Updated

| Material key | Material name | Unit | Current price | New price | Changed fields |
| --- | --- | --- | ---: | ---: | --- |
| `sample_concrete` | Demo Concrete | bags | 120.00 | 125.50 | unit_price |

## Materials That Would Be Unchanged

| Material key | Material name | Unit | Current price | New price | Changed fields |
| --- | --- | --- | ---: | ---: | --- |
| `sample_unchanged` | Demo Unchanged | kg | 30.00 | 30.00 | - |

## Safety Notes

- This command writes only this preview report.
- This command does not import rows into live JSON.
- This command does not modify production pricing data.
- Keep real owner pricing CSV files outside Git-tracked sample paths.
