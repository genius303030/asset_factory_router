# Owner Pricing Final Import Fake Rehearsal Report

Fake-fixture-only rehearsal. No real production import command was invoked.

## Status

- Result: `rollback_passed`
- Generated at: `2026-06-29T17:36:43+00:00`
- Next safe step: Review fake rehearsal evidence; real final import remains blocked.

## Safety Statement

- No `asset-factory owner-pricing-final-import` command was added or invoked.
- No real production write was performed.
- No live JSON was mutated.
- No production pricing data was mutated.
- Backup writing is limited to the explicit fake backup path.

## Paths

- Sandbox output: `examples\owner_pricing\fake_sandbox_pricing_output.json`
- Approval record: `examples\owner_pricing\fake_owner_pricing_approval_record.json`
- Preflight report: `examples\owner_pricing\fake_final_import_rehearsal_preflight_report.json`
- Fake production target: `examples\owner_pricing\fake_final_import_rehearsal_production_target.csv`
- Fake production output: `outputs\owner_pricing\fake_final_import_rehearsal_output.csv`
- Fake backup output: `outputs\owner_pricing\fake_final_import_rehearsal_backup.csv`
- Audit log: `examples\owner_pricing\fake_final_import_rehearsal_audit.json`

## Checksums

- Sandbox output SHA-256: `797a1164dcb965ac190bf5300f8ad3531b2f744874f8e4f8d1b8975743da07ce`
- Approval record SHA-256: `c4b83d890a984d401af9e2ec0cca7ebd5e369c6c04710daf1aba03046dba052b`
- Preflight report SHA-256: `0859a953c384c4154cedf7a7775262c6f51d466fb4fea20f3f3942ab8882eed7`
- Pre-import fake production SHA-256: `de7d89a1c7001ba4a9178598c06a734db1764980f65d94fdb4e39af2eea38a41`
- Fake backup SHA-256: `de7d89a1c7001ba4a9178598c06a734db1764980f65d94fdb4e39af2eea38a41`
- Post-write fake production SHA-256: `aac3af21d66b994135a7f795588d807d9a18919e0b8709ce26f06ae190458c35`
- Restored fake production SHA-256: `de7d89a1c7001ba4a9178598c06a734db1764980f65d94fdb4e39af2eea38a41`

## State History

| Status | Detail |
| --- | --- |
| started | fake rehearsal started |
| backup_verified | fake backup checksum matched pre-import fake production checksum |
| fake_write_completed | fake production output path was written |
| passed | fake write and post-write validation passed |
| rollback_passed | fake rollback restored and verified the fake output path |

## Input Validation

| Check | Status | Detail |
| --- | --- | --- |
| sandbox output remains sandbox-only | PASS | sandbox_only is true |
| sandbox output final import remains disabled | PASS | final_import_enabled is false |
| sandbox output live JSON mutation flag remains false | PASS | live_json_mutated is false |
| sandbox output production mutation flag remains false | PASS | production_pricing_mutated is false |
| approval record type is owner sandbox approval | PASS | approval record type is expected |
| approval checksum matches sandbox output | PASS | approval checksum matches sandbox output bytes |
| approval record references intended sandbox output | PASS | approval record references intended sandbox output |
| approval record final import flag remains false | PASS | approval final_import_enabled is false |
| preflight report type is expected | PASS | preflight type is expected |
| preflight status is PASS | PASS | preflight status is PASS |
| preflight references sandbox output | PASS | preflight references intended sandbox output |
| preflight references approval record | PASS | preflight references intended approval record |
| preflight references fake production target | PASS | preflight references intended fake production target |
| preflight references fake backup output | PASS | preflight references intended fake backup output |
| preflight sandbox checksum matches | PASS | preflight sandbox checksum matches |
| preflight approval checksum matches | PASS | preflight approval checksum matches |
| preflight production target checksum matches fake target | PASS | preflight fake production checksum matches |
| preflight reports no production write | PASS | preflight production_write_performed is false |
| preflight reports no backup written | PASS | preflight backup_written is false |
| sandbox material keys are unique | PASS | sandbox material keys are unique |
| skipped invalid rows are absent from sandbox materials | PASS | skipped invalid rows are absent from materials |
| sandbox summary counts match materials | PASS | sandbox summary counts match material lists |

## Post-write Validation

| Check | Status | Detail |
| --- | --- | --- |
| post-write fake production output material count matches | PASS | material count is 4 |
| post-write fake production output material keys match | PASS | material keys match expected set |
| post-write fake production output material keys are unique | PASS | material keys are unique |
| post-write fake production output has no skipped invalid rows | PASS | skipped invalid rows are absent |
| post-write fake production output schema is valid | PASS | schema is valid |

## Restore Validation

| Check | Status | Detail |
| --- | --- | --- |
| restored fake production output material count matches | PASS | material count is 3 |
| restored fake production output material keys match | PASS | material keys match expected set |
| restored fake production output material keys are unique | PASS | material keys are unique |
| restored fake production output has no skipped invalid rows | PASS | skipped invalid rows are absent |
| restored fake production output schema is valid | PASS | schema is valid |

## Blockers

- None.

## Warnings

- None.
