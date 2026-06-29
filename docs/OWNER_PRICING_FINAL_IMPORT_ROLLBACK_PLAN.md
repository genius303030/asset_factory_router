# Owner Pricing Final Import Rollback Plan

This rollback plan is for a possible future owner pricing final import. G1-025
does not implement final import, rollback execution, or production writes.

## Rollback Objective

Rollback must restore production pricing to the exact state captured immediately
before the future final import. The backup is the source of truth for rollback,
not the owner CSV, not a regenerated sandbox output, and not an edited manual
file.

## Backup Source

The backup source is the production pricing target before import. The future
final import must record:

- Production target path.
- Production target format.
- Pre-import production checksum.
- Production target byte size.
- Backup creation timestamp.

If the production target does not exist before import, the future workflow must
record that as a first-time creation case and G0 must explicitly approve it.

## Backup Destination

Backup destination must be explicit and separate from the production target.

Allowed local backup locations:

- `output/owner_pricing/backups/`
- `outputs/owner_pricing/backups/`
- `owner_pricing_private/backups/`

Blocked backup locations:

- `src/`
- `config/`
- `data/`
- `live/`
- `prod/`
- `production/`

The future import must fail if backup destination is missing, unsafe, or cannot
be written before production import.

## Backup Verification

After creating backup and before import:

1. Read the backup file as bytes.
2. Compute SHA-256 checksum.
3. Compare backup checksum with pre-import production checksum.
4. Abort import if the checksums differ.
5. Record backup checksum in the audit log.

## Restore Procedure

Rollback restore must be deliberate and owner-visible:

1. Stop further owner pricing import attempts.
2. Record rollback reason in an audit log.
3. Confirm the backup path and checksum.
4. Confirm G0 approval for rollback.
5. Copy the backup file over the production target.
6. Read the restored production target as bytes.
7. Compute restored checksum.
8. Confirm restored checksum equals backup checksum.
9. Run production pricing schema validation.
10. Check material count and duplicate material keys.
11. Write rollback completion report.
12. Send final rollback report to owner/G0.

## Verify Restored Pricing

After restore:

- Production target exists.
- Restored checksum equals backup checksum.
- Schema validation passes.
- Material count equals the pre-import count.
- No duplicate material keys exist.
- No invalid rows are present.
- Audit log references the backup path and restored checksum.

## Partial Import Failure

If import partially fails:

- Stop immediately.
- Do not retry import in place.
- Preserve the partially written production target for investigation if G0
  requests it and a safe copy path exists.
- Restore from backup.
- Verify restored pricing.
- Mark the final import attempt as failed in audit log.
- Require a new G0-approved task before another import attempt.

## Checksum Mismatch

If sandbox output checksum does not match approval record:

- Abort before import.
- Do not create or update production pricing.
- Do not reuse the approval record.
- Regenerate or reselect the intended sandbox output.
- Generate a new approval record after owner review.
- Record the mismatch in audit log.

If backup checksum does not match pre-import production checksum:

- Abort before import.
- Do not write production pricing.
- Investigate whether production target changed during backup.
- Regenerate backup only after G0 confirms the current production target is the
  correct source.

If restored checksum does not match backup checksum:

- Stop and escalate to G0 immediately.
- Preserve current production target and backup.
- Do not run another restore attempt without G0 approval.

## Stale Approval Record

An approval record is stale when:

- Its sandbox output checksum does not match the sandbox output file.
- Its sandbox output path points to a different artifact than the proposed
  import.
- Its approval record predates a G0-defined approval expiration rule.
- Owner or G0 withdraws approval.
- The sandbox output was regenerated after approval.

If approval record is stale:

- Abort before import.
- Do not write production pricing.
- Generate a new sandbox output if needed.
- Generate a new approval record after owner review.

## Rollback Approval

Rollback requires G0 approval unless production data loss is actively in
progress and G0 has previously authorized emergency rollback rules.

Roles:

- G0 / Owner approves rollback and final restored state.
- G1 executes only the approved rollback procedure in a future implementation.
- G2 reviews rollback report, validation evidence, and follow-up risks.

## Rollback Report Contents

The rollback report must include:

- Rollback reason.
- Production target path.
- Backup path.
- Backup checksum.
- Restored checksum.
- Pre-import checksum.
- Failed post-import checksum, if any.
- Validation results.
- Material count before import.
- Material count after restore.
- Duplicate key check result.
- G0 approval reference.
- Remaining risks.

## Do Not Do

- Do not rollback from owner CSV.
- Do not rollback from sandbox output.
- Do not edit production pricing manually during rollback.
- Do not delete failed import evidence unless G0 explicitly approves cleanup.
- Do not retry final import without a new reviewed plan.
