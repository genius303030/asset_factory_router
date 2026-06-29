# Owner Pricing Final Import Preflight

This workflow runs a read-only preflight check before any future owner pricing
final import. It writes a preflight report only. It does not import production
pricing, does not write a backup, and does not mutate live JSON.

## What This Command Does

`asset-factory owner-pricing-final-import-preflight` reads:

- Sandbox output JSON from `owner-pricing-apply-sandbox-output`.
- Owner approval record JSON from `owner-pricing-approve-sandbox-output`.
- Explicit production target path, inspected read-only.
- Explicit future backup output path, validated but not written.
- Explicit markdown report output path.
- Optional JSON report output path.

The report includes:

- PASS / FAIL status.
- Checked file paths.
- Sandbox output checksum.
- Approval record checksum.
- Production target checksum.
- Expected backup path.
- Validation results.
- Blockers.
- Warnings.
- Next safe step.
- Explicit statement that no production write was performed.

## What This Command Does Not Do

- It does not add final import.
- It does not invoke a final import command.
- It does not mutate live JSON.
- It does not mutate production pricing data.
- It does not create a backup file.
- It does not approve production import.
- It does not weaken sandbox output or approval boundaries.

## Relationship To G1-025 Planning

G1-025 defined the future final import plan, rollback plan, and checklist. This
preflight checker implements the read-only validation layer from that plan, so
G2 and G0 can inspect whether the current sandbox output and approval record are
internally consistent before any future production-import implementation exists.

Final import remains disabled after a PASS.

## Required Checks

Preflight verifies:

- Sandbox output exists.
- Sandbox output is valid JSON.
- Sandbox output declares `sandbox_only: true`.
- Sandbox output declares `final_import_enabled: false`.
- Sandbox output declares `live_json_mutated: false`.
- Sandbox output declares `production_pricing_mutated: false`.
- Approval record exists.
- Approval record is valid JSON.
- Approval checksum matches sandbox output bytes.
- Approval record references the intended sandbox output.
- Production target path is explicit.
- Production target exists.
- Production target is inspected read-only.
- Production target path is not unsafe.
- Backup output path is explicit.
- Backup output path is not unsafe.
- Backup output does not already exist.
- Sandbox material keys are unique.
- Skipped invalid rows are not present in sandbox materials.
- Added, updated, unchanged, retained, skipped, and total counts match sandbox
  summary.
- No final import command is invoked.
- No production write occurs.

## Command

```bash
asset-factory owner-pricing-final-import-preflight \
  --sandbox-output output/owner_pricing_sandbox_output.json \
  --approval-record output/owner_pricing_approval_record.json \
  --production-target output/read_only_current_pricing.csv \
  --backup-output outputs/owner_pricing/future_backup.json \
  --report output/owner_pricing_final_import_preflight_report.md
```

Optional JSON report:

```bash
asset-factory owner-pricing-final-import-preflight \
  --sandbox-output output/owner_pricing_sandbox_output.json \
  --approval-record output/owner_pricing_approval_record.json \
  --production-target output/read_only_current_pricing.csv \
  --backup-output outputs/owner_pricing/future_backup.json \
  --report output/owner_pricing_final_import_preflight_report.md \
  --report-json output/owner_pricing_final_import_preflight_report.json
```

Use `--overwrite` only to replace an existing preflight report. It does not
allow production writes and it does not allow backup writes.

## How To Read PASS / FAIL

`PASS` means the files are internally consistent for planning review:

- Checksums match.
- Counts match.
- Paths are explicit and allowed.
- No production write occurred.

`PASS` does not mean final import is approved or implemented.

`FAIL` means at least one blocker exists. The owner should read the blocker list,
fix the source issue, regenerate the affected sandbox or approval artifact if
needed, and rerun preflight. Do not proceed to final import planning review while
preflight is failing.

## Production Protection

The preflight checker protects production by:

- Opening the production target only for read/checksum/schema inspection.
- Rejecting unsafe production target paths.
- Validating backup path without writing a backup.
- Writing only the requested preflight report files.
- Keeping `production_write_performed: false` in JSON report output.

## Safe Local Outputs

Real preflight reports should stay in ignored local paths:

- `output/owner_pricing/`
- `outputs/owner_pricing/`
- `owner_pricing_private/`

Do not commit reports generated from real owner pricing data.

## Fake Sample

The repository includes fake-only sample reports:

- `examples/owner_pricing/fake_final_import_preflight_report.md`
- `examples/owner_pricing/fake_final_import_preflight_report.json`

Regenerate the fake sample:

```bash
asset-factory owner-pricing-final-import-preflight \
  --sandbox-output examples/owner_pricing/fake_sandbox_pricing_output.json \
  --approval-record examples/owner_pricing/fake_owner_pricing_approval_record.json \
  --production-target examples/owner_pricing/fake_current_pricing.csv \
  --backup-output outputs/owner_pricing/fake_future_backup.json \
  --report examples/owner_pricing/fake_final_import_preflight_report.md \
  --report-json examples/owner_pricing/fake_final_import_preflight_report.json \
  --overwrite
```

## Why Final Import Is Still Disabled

Preflight only proves that planning artifacts are consistent enough for review.
It does not create the missing production import implementation, rollback
execution, or final owner sign-off. Any final import must still be a separate
G0-approved task with new implementation tests and G2 review.
