# Owner Pricing Final Import Fake Rehearsal

G1-028 adds a fake-fixture-only rehearsal for final-import-adjacent mechanics.
It does not add `asset-factory owner-pricing-final-import`, does not write real
production pricing, does not mutate live JSON, and does not use real owner
pricing data.

## Purpose

The fake rehearsal proves infrastructure that a future production import would
need, but only against fake fixtures and explicit fake output paths:

- Fake production target read.
- Fake backup creation.
- Fake backup checksum verification.
- Fake output write from approved sandbox output.
- Post-write schema, count, and key validation.
- Rollback restore from the verified fake backup.
- Restore checksum and schema/count/key validation.
- Audit log state writing for success and failure paths.

Production import remains blocked after a successful fake rehearsal.

## Command

```bash
asset-factory owner-pricing-final-import-fake-rehearsal \
  --sandbox-output examples/owner_pricing/fake_sandbox_pricing_output.json \
  --approval-record examples/owner_pricing/fake_owner_pricing_approval_record.json \
  --preflight-report examples/owner_pricing/fake_final_import_rehearsal_preflight_report.json \
  --fake-production-target examples/owner_pricing/fake_final_import_rehearsal_production_target.csv \
  --fake-production-output outputs/owner_pricing/fake_final_import_rehearsal_output.csv \
  --backup-output outputs/owner_pricing/fake_final_import_rehearsal_backup.csv \
  --audit-log outputs/owner_pricing/fake_final_import_rehearsal_audit.json \
  --report outputs/owner_pricing/fake_final_import_rehearsal_report.md
```

The command name intentionally includes `fake-rehearsal`. The reserved
production command remains absent:

```bash
asset-factory owner-pricing-final-import
```

## Required Inputs

- `--sandbox-output`: fake sandbox output JSON.
- `--approval-record`: fake owner approval record JSON.
- `--preflight-report`: fake final import preflight JSON with PASS status.
- `--fake-production-target`: fake local production-pricing fixture.
- `--fake-production-output`: fake output path to write and restore.
- `--backup-output`: fake backup output path.
- `--audit-log`: fake audit log output path.
- `--report`: fake markdown report output path.

All input and output paths must be fake fixtures or local output paths. Unsafe
path parts such as `src`, `config`, `data`, `live`, `prod`, and `production`
are refused.

## What The Rehearsal Does

1. Validates sandbox output, approval record, and preflight report.
2. Verifies approval checksum against sandbox output bytes.
3. Verifies preflight checksums against sandbox, approval, and fake production
   target bytes.
4. Writes an audit log before fake write.
5. Copies the fake production target to the fake backup path.
6. Verifies fake backup checksum equals fake pre-import checksum.
7. Writes fake output from sandbox materials.
8. Validates fake output schema, counts, duplicate keys, and skipped-row
   exclusion.
9. Restores fake output from the verified fake backup.
10. Verifies restore checksum, schema, counts, and duplicate keys.

## What The Rehearsal Does Not Do

- It does not add the reserved production command.
- It does not write real production pricing.
- It does not write backups outside explicit fake/local output paths.
- It does not mutate live JSON.
- It does not mutate production pricing data.
- It does not approve future production import.
- It does not weaken dry-run, sandbox, approval, preflight, or design-gate
  boundaries.

## Audit States

The fake audit log records state transitions. Covered states include:

- `started`
- `aborted`
- `failed_before_write`
- `backup_verified`
- `fake_write_completed`
- `passed`
- `rollback_required`
- `rollback_passed`
- `rollback_failed`

The success path ends at `rollback_passed` because the rehearsal intentionally
restores the fake output from the fake backup after proving the fake write.

## Failure Rehearsal Flags

The command includes fake-only simulation flags:

- `--simulate-post-write-validation-failure`
- `--simulate-rollback-verification-failure`

These are for testing rollback-required and rollback-failed audit paths. They
must not exist on any future real production import command without separate G0
approval and G2 review.

## Fake Examples

Committed fake examples:

- `examples/owner_pricing/fake_final_import_rehearsal_production_target.csv`
- `examples/owner_pricing/fake_final_import_rehearsal_preflight_report.md`
- `examples/owner_pricing/fake_final_import_rehearsal_preflight_report.json`
- `examples/owner_pricing/fake_final_import_rehearsal_report.md`
- `examples/owner_pricing/fake_final_import_rehearsal_audit.json`

Generated local fake output and fake backup files should remain under ignored
paths such as `outputs/owner_pricing/`.

## Next Safe Step

G2 reviews the fake rehearsal implementation and evidence. A real final import
still requires a separate G0-approved task, implementation PR, rollback
verification, audit log implementation, and G2 review.
