# Owner Pricing Fake Implementation Evidence Packet

G1-036 defines the fake-only evidence packet a future owner-pricing final
application implementation would need before G2/G0 review. This is planning,
documentation, and test-contract work only. It does not implement runtime
behavior, does not register a parser, does not add CLI flags to code, does not
change safety gate code, and does not touch real owner data.

## Evidence Packet Boundary

The evidence packet must be fake-only. It may use committed sample fixtures
under `examples/owner_pricing/` or generated fake local outputs under ignored
paths. It must not include real customer, job, material pricing, owner private
pricing, credentials, tokens, or production data.

The packet does not approve production import. It only proves that a future
implementation has enough fake evidence for G2 and G0 to evaluate the workflow
shape.

## Required Fake Input Artifacts

| Artifact | Required Evidence | Review Rule |
| --- | --- | --- |
| Fake owner pricing CSV | Fake material rows with valid, invalid, duplicate, add, update, and unchanged coverage. | Must use clearly sample values only. |
| Fake current pricing baseline | Fake existing pricing target used for comparison and backup rehearsal. | Must be checksum-reviewed when downstream reports reference it. |
| Fake sandbox output | Structured output from fake sandbox apply path. | Must keep sandbox-only and no-production markers intact. |
| Fake approval record | Owner approval-shaped record for the fake sandbox output. | Must match sandbox output checksum and remain separate from final approval. |
| Fake preflight evidence | PASS and failure-shaped preflight evidence for fake artifacts. | Must prove current artifact packet, not stale paths. |
| Fake G0 approval packet | Metadata-only approval packet for fake evidence review. | Must not include private owner values. |

## Required Fake Output Artifacts

| Artifact | Required Evidence | Review Rule |
| --- | --- | --- |
| Fake production target before attempt | Starting target used to prove backup and restore behavior. | Must be fake and checksum-sensitive. |
| Fake production target after successful attempt | Expected fake output after applying approved sandbox data. | Must match approved fake counts and schema. |
| Fake aborted output state | Evidence that no write happened before blocked gates. | Must show production write status as false. |
| Fake rollback-required output state | Evidence from a simulated post-write validation failure. | Must preserve the failed output for review. |
| Fake rollback-restored output state | Evidence that restore used the verified backup. | Must match backup checksum and schema. |

These outputs may be committed only if they are curated fake golden artifacts.
Generated local outputs stay ignored unless G0 explicitly asks for a fake golden
update.

## Required Fake Audit Artifacts

Future fake audit evidence must cover:

- Attempt created.
- Artifact packet validated.
- Pre-write abort.
- Backup created.
- Backup verified.
- Fake write started.
- Fake write passed.
- Fake write failed.
- Rollback required.
- Rollback passed.
- Rollback failed.

Each audit artifact must include an attempt ID, fake artifact paths, checksum
fields, validation statuses, write status, rollback status, and next safe step.

## Required Fake Owner Report Artifacts

The packet must include fake owner report examples for:

- Successful fake application.
- Aborted attempt before backup.
- Aborted attempt after backup and before fake write.
- Rollback-required attempt.
- Rollback-passed attempt.
- Rollback-failed attempt.

Each report must be human-readable, must match the structured fake audit
artifact, and must state that real production import remains blocked.

## Required Fake Rollback Artifacts

Rollback evidence must include:

- Fake backup file.
- Fake rollback request metadata.
- Fake rollback approval metadata.
- Fake restored target.
- Fake rollback report.
- Fake rollback audit state.

Rollback must use only the verified fake backup as restore source. It must not
use owner CSV, sandbox output, manual edits, or regenerated pricing data as the
restore source.

## Required Checksum Evidence

The packet must document checksums for:

- Fake owner pricing CSV when referenced by reports.
- Fake current pricing baseline.
- Fake sandbox output.
- Fake approval record.
- Fake preflight JSON.
- Fake production target before attempt.
- Fake backup.
- Fake production target after fake write.
- Fake restored target after rollback.
- Fake audit JSON.

Checksum-sensitive files under `examples/owner_pricing/` must remain
LF-normalized. Downstream checksum references must be updated in the same PR or
the PR must explicitly document why they are unchanged.

## Required Metrics Evidence

The future implementation evidence packet must update or schedule the metrics
row for the implementation PR. Metrics evidence must include:

- PR number.
- Task ID.
- Branch.
- Changed files.
- Unit test count when visible.
- Owner-pricing-specific test count when visible.
- CI status.
- Safety gate status.
- G2 review status.
- Merge status when known.
- Docs/tests/src/workflow/examples change flags.
- Production behavior status.

Use `unknown` when a value is not backed by durable evidence.

## Required Fixture Registry Updates

Before a future fake implementation evidence packet can be reviewed, the fixture
registry must list each committed fake artifact and mark:

- Workflow stage.
- Artifact kind.
- Golden role.
- Git status.
- Checksum-sensitive status.
- G2 review rule.

Generated local fake artifacts must stay under ignored output paths unless they
are intentionally curated into committed golden fixtures.

## Required Golden Report Updates

Golden report documentation must explain:

- Which fake reports are canonical.
- Which structured JSON or audit artifacts each report must match.
- Which checksums are embedded.
- Which upstream fixture changes require downstream regeneration.
- Which local generated artifacts must remain ignored.

Markdown reports and structured JSON/audit files must agree on attempt ID,
paths, checksums, counts, validation statuses, rollback status, and next safe
step.

## G2 Review Checklist

G2 should verify:

- The packet is fake-only.
- No parser registration was added.
- No CLI flags were added to code.
- No owner-pricing runtime behavior changed.
- Safety gate code was not changed.
- No real owner, customer, job, or material pricing data was added.
- Fake input, output, audit, owner report, rollback, checksum, metrics,
  fixture, and golden-report evidence are all present or explicitly blocked.
- Checksum-sensitive artifacts were reviewed in LF-normalized form.
- Metrics evidence uses `unknown` instead of invented values.
- Local generated outputs remain ignored and unstaged.

## G0 Approval Checklist

Before G0 can approve a future fake implementation evidence packet, G0 must
confirm:

- Implementation issue and PR are identified.
- Fake evidence packet version is identified.
- G2 review verdict is PASS.
- CI and local validation are green.
- Fixture registry updates are present or explicitly scheduled.
- Golden report updates are present or explicitly scheduled.
- Metrics updates are present or explicitly scheduled.
- Rollback and audit evidence are reviewable.
- Real production import remains blocked.

## No-Go Conditions

Do not approve or merge a future implementation evidence packet if:

- Any real owner, customer, job, or material pricing data is present.
- Parser registration is added without a separate approved implementation task.
- CLI flags are added to code.
- Runtime behavior changes.
- Safety gate code is weakened or bypassed.
- Existing owner-pricing checks are removed.
- Fake rollback does not use the verified fake backup.
- Checksum evidence is missing for checksum-sensitive fake artifacts.
- Metrics evidence is missing or invented.
- Fixture registry or golden-report updates are missing for committed fake
  artifacts.
- G2 review is missing or request-changes.

G1-036 stops at this fake evidence plan. Runtime implementation remains blocked.
