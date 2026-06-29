# Owner Pricing Final Import Audit Schema

This schema describes the audit log a future owner pricing final import command
must write. G1-027 does not implement audit log writing and does not run final
import.

## Storage Rule

Real audit logs must stay in ignored local paths:

- `output/owner_pricing/`
- `outputs/owner_pricing/`
- `owner_pricing_private/`

Audit logs generated from real owner data must never be committed.

## Required JSON Shape

The future audit log must be a JSON object with these top-level fields:

```json
{
  "audit_type": "owner_pricing_final_import_attempt",
  "schema_version": 1,
  "attempt_id": "fake-attempt-id",
  "status": "aborted",
  "generated_at": "2026-06-29T00:00:00+00:00",
  "operator": {
    "role": "G1",
    "label": "local operator"
  },
  "command": {
    "name": "asset-factory owner-pricing-final-import",
    "version": "future",
    "enable_production_import": false,
    "final_confirmation_present": false
  },
  "paths": {
    "sandbox_output": "examples/owner_pricing/fake_sandbox_pricing_output.json",
    "approval_record": "examples/owner_pricing/fake_owner_pricing_approval_record.json",
    "preflight_report": "examples/owner_pricing/fake_final_import_preflight_report.json",
    "production_target": "not-used-in-fake-sample",
    "backup_output": "not-written-in-g1-027",
    "audit_log": "outputs/owner_pricing/future_audit_log.json"
  },
  "checksums": {
    "sandbox_output_sha256": "fake",
    "approval_record_sha256": "fake",
    "pre_import_production_sha256": null,
    "backup_sha256": null,
    "post_import_production_sha256": null,
    "restored_production_sha256": null
  },
  "approval": {
    "approval_type": "owner_pricing_sandbox_output_approval",
    "approved_by": "local owner / manual owner",
    "sandbox_checksum_matched": false,
    "g0_final_import_approval_record": null,
    "g0_final_confirmation_matched": false
  },
  "preflight": {
    "status": "not_run",
    "report_sha256": null,
    "blockers": []
  },
  "counts": {
    "added_materials": 0,
    "updated_materials": 0,
    "unchanged_materials": 0,
    "retained_baseline_materials": 0,
    "skipped_rows": 0,
    "sandbox_materials_written": 0,
    "production_materials_before": null,
    "production_materials_after": null
  },
  "validation_results": [],
  "safety_flags": {
    "sandbox_only_input": true,
    "final_import_enabled_input": false,
    "production_write_performed": false,
    "backup_written": false,
    "live_json_mutated": false,
    "production_pricing_mutated": false
  },
  "rollback": {
    "required": false,
    "approved_by_g0": false,
    "executed": false,
    "backup_verified_before_restore": false,
    "restore_verified": false,
    "report_path": null
  },
  "blockers": [],
  "warnings": [],
  "next_safe_step": "Design gate review only."
}
```

## Status Values

The future command must use one of these status values:

- `aborted`: stopped before production write.
- `failed_before_write`: failed after command start but before production write.
- `backup_verified`: backup was written and checksum verified, but production
  write has not happened yet.
- `import_written`: production target was written and post-write validation is
  still pending.
- `passed`: production write and post-import validation passed.
- `rollback_required`: post-import validation failed or G0 requested rollback.
- `rollback_passed`: rollback restore completed and verification passed.
- `rollback_failed`: rollback restore or restore verification failed.

## Required Validation Result Shape

Each validation result must be an object:

```json
{
  "check": "approval checksum matches sandbox output",
  "status": "PASS",
  "detail": "computed checksum matched approval record"
}
```

Allowed validation statuses:

- `PASS`
- `FAIL`
- `WARN`
- `NOT_RUN`

Any `FAIL` before production write must abort. Any `FAIL` after production write
must trigger rollback review.

## Required Safety Flags

The audit log must always include:

- `production_write_performed`
- `backup_written`
- `live_json_mutated`
- `production_pricing_mutated`

These flags must be factual. A future command must never set production flags to
success values before the action actually occurs.

## Checksum Requirements

The future audit log must record SHA-256 checksums for:

- Sandbox output bytes.
- Approval record bytes.
- Pre-import production target bytes.
- Backup bytes.
- Post-import production target bytes.
- Restored production target bytes when rollback runs.

Checksum fields that do not apply because execution stopped early must be
`null`, not guessed or invented.

## Audit Write Timing

The future implementation must write audit state at these points:

1. Attempt started.
2. Input validation complete.
3. Backup created.
4. Backup verified.
5. Production write started.
6. Production write completed.
7. Post-import validation completed.
8. Rollback started, when applicable.
9. Rollback completed, when applicable.
10. Final owner report generated.

The audit log must fail closed before production write. If audit writing fails
before production write, no production write may occur.

## Review Requirements

G2 must review the audit schema implementation for:

- Required fields present.
- Status transitions are monotonic and evidence-based.
- No real owner data is committed.
- Failure paths create useful audit evidence without exposing private data.
- Rollback evidence is traceable to the exact backup used.
