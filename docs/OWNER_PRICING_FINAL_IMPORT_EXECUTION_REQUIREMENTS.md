# Owner Pricing Final Import Execution Requirements

This document defines execution requirements for a possible future owner
pricing final import command. G1-027 does not implement that command and does
not perform production writes.

## Execution Sequence

A future final import must run in this order:

1. Parse required flags.
2. Validate no unrelated dirty files exist.
3. Validate sandbox output JSON.
4. Validate approval record JSON.
5. Validate approval checksum against sandbox output bytes.
6. Validate preflight report status and checksum, if required by the future
   implementation.
7. Validate production target path.
8. Read production target bytes and compute pre-import checksum.
9. Validate backup output path.
10. Write initial audit log state.
11. Create backup from the production target.
12. Verify backup checksum equals pre-import production checksum.
13. Write audit state showing backup verification.
14. Write production target from approved sandbox output.
15. Validate production target schema and counts.
16. Verify no duplicate material keys and no skipped invalid rows imported.
17. Record post-import production checksum.
18. Write final audit log and owner report.

Any failed step before production write must abort with no production write.
Any failed step after production write must enter rollback review.

## Production Write Requirements

The future command may write production pricing only after:

- G0 approved the implementation PR.
- G2 reviewed the implementation PR.
- Required flags are present.
- `--enable-production-import` is present.
- Final confirmation phrase exactly matches the future required phrase.
- Approval checksum matches sandbox output bytes.
- Preflight status is PASS.
- Backup is created and verified.
- Audit log is writable.

The production write must be atomic where practical. If the target platform does
not support atomic replacement, the implementation must document the partial
write risk and rollback behavior before merge.

## Backup Creation Requirements

The future backup must:

- Be written before production import.
- Be copied from the exact production target bytes.
- Use an explicit path supplied by flag.
- Refuse unsafe path parts such as `src`, `config`, `data`, `live`, `prod`, and
  `production`.
- Refuse overwrite unless a separate future overwrite design is approved.
- Record source path, destination path, byte size, timestamp, and checksum.

If backup creation fails, production import must not start.

## Backup Verification Requirements

After writing the backup and before production write:

1. Read production target bytes again.
2. Read backup bytes.
3. Compute SHA-256 for both.
4. Confirm backup checksum equals pre-import production checksum.
5. Confirm production target did not change between initial read and backup
   verification.
6. Record verification result in audit log.

If checksums differ, stop. Do not retry automatically. G0 must decide whether
the production target changed legitimately or whether the import attempt should
be abandoned.

## Post-import Validation Requirements

After a future production write:

- Production target exists.
- Production target parses as the expected CSV or JSON format.
- Required material fields are present.
- Material keys are unique.
- No skipped invalid rows from sandbox output appear in production materials.
- Added, updated, unchanged, retained, skipped, and total counts match approved
  sandbox output expectations.
- Post-import checksum is recorded.
- Backup still exists and checksum still matches audit metadata.
- Owner report is written.

Any failed post-import validation must mark the audit log as
`rollback_required`.

## Rollback Execution Requirements

Rollback must restore the exact verified backup created immediately before the
failed import attempt.

Rollback must run in this order:

1. Stop further import attempts.
2. Record rollback reason.
3. Confirm G0 rollback approval unless emergency rollback was pre-authorized.
4. Confirm backup path exists.
5. Confirm backup checksum matches audit metadata.
6. Copy backup bytes over the production target.
7. Read restored production target bytes.
8. Confirm restored checksum equals backup checksum.
9. Validate restored production target schema.
10. Confirm restored material count equals pre-import count.
11. Confirm no duplicate material keys.
12. Write rollback report.
13. Mark audit log `rollback_passed` or `rollback_failed`.

Rollback must not use owner CSV, sandbox output, or manually edited data as the
restore source.

## Restore Verification Requirements

Restore verification must include:

- Backup checksum.
- Restored production checksum.
- Schema validation result.
- Material count before import.
- Material count after restore.
- Duplicate key check result.
- G0 rollback approval reference.
- G2 rollback review status.

If restore verification fails, stop and escalate to G0. Do not run another
restore attempt without explicit G0 direction.

## Emergency Stop Conditions

Stop before production write when:

- Required inputs are missing.
- Approval record is stale or checksum mismatched.
- Preflight report is missing or failing.
- Production target path is unsafe.
- Backup path is unsafe.
- Backup path already exists.
- Backup cannot be written.
- Backup checksum does not match pre-import production checksum.
- Repository has unrelated dirty files.
- Audit log cannot be written.
- G0 withdraws approval.

Stop after production write and enter rollback review when:

- Production target cannot be parsed.
- Material count differs from approved sandbox output.
- Duplicate material keys appear.
- Skipped invalid rows were imported.
- Post-import checksum cannot be recorded.
- Owner report cannot be written.
- G0 requests rollback.

## G2 Evidence Packet

Before a future implementation PR can be considered merge-ready, G2 must see:

- Command help output.
- Unit tests for every required failure mode.
- Fake fixture proving backup creation and verification.
- Fake fixture proving rollback restore and restore verification.
- Audit log examples for aborted, passed, and rollback-required states.
- `git diff --check` result.
- Full test suite result.
- Confirmation that no real owner CSV or production pricing data is committed.
