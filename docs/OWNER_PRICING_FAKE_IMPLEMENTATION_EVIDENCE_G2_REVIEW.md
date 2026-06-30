# Owner Pricing Fake Implementation Evidence G2 Review

This checklist defines how G2 should review G1-036 and any future fake
implementation evidence packet for the owner-pricing final application path.

## G1-036 Review Checklist

G2 should confirm this PR:

- Adds docs and documentation tests only.
- Is a fake evidence plan only.
- Does not add parser registration.
- Does not add CLI flags to code.
- Does not change owner-pricing runtime behavior.
- Does not change safety gate code.
- Does not touch real owner data.
- Does not add real customer, job, or material pricing data.
- Documents required fake input artifacts.
- Documents required fake output artifacts.
- Documents required fake audit artifacts.
- Documents required fake owner report artifacts.
- Documents required fake rollback artifacts.
- Documents checksum, metrics, fixture registry, and golden report evidence.
- Documents G2 review, G0 approval, and no-go conditions.

## Future Evidence Packet Review Checklist

For a future fake evidence packet PR, G2 must verify:

| Area | Required Review |
| --- | --- |
| Scope | Packet is fake-only and tied to the approved implementation issue. |
| Inputs | Fake owner pricing, fake baseline, fake sandbox, fake approval, fake preflight, and fake G0 approval artifacts are present. |
| Outputs | Fake before, after, aborted, rollback-required, and restored outputs are present or explicitly blocked. |
| Audit | Fake audit evidence covers abort, pass, fail, rollback-required, rollback-passed, and rollback-failed states. |
| Owner report | Markdown reports match structured audit evidence and state real production remains blocked. |
| Rollback | Restore uses only the verified fake backup and validates restored output. |
| Checksums | Checksum-sensitive fake artifacts have matching downstream references. |
| Metrics | Metrics row is updated or explicitly scheduled with durable evidence. |
| Fixture registry | Every committed fake artifact is listed with stage, type, role, Git status, checksum status, and G2 rule. |
| Golden reports | Markdown and JSON/audit golden files agree on IDs, paths, checksums, counts, status, rollback, and next safe step. |
| Safety | No parser, runtime, safety gate, or real-data boundary is weakened. |

## Required Evidence Before PASS

G2 cannot mark a future fake implementation evidence packet PASS until it sees:

- Full unit test result.
- Owner-pricing-specific unit test result.
- Safety gate result.
- Metrics validation result.
- Ruff result.
- Diff whitespace checks.
- GitHub Actions success.
- Fixture registry update or explicit blocked status.
- Golden report update or explicit blocked status.
- Fake checksum evidence.
- Fake rollback evidence.
- Fake audit evidence.
- G0 approval packet or explicit G0 pending status.

## Review Questions

G2 should ask:

- Is every artifact fake?
- Are any private paths, customer details, job details, or material prices real?
- Does any file imply production import is approved?
- Does rollback use only the verified fake backup?
- Do checksum-sensitive files stay LF-stable?
- Do markdown reports match structured audit data?
- Are metrics values backed by durable evidence or marked `unknown`?
- Are local generated artifacts ignored and unstaged?
- Did the PR avoid parser, runtime, CLI flag, and safety gate changes?

## G2 Verdict Template

```text
Verdict: PASS / REQUEST_CHANGES
Reviewed PR:
Reviewed commit:
Evidence packet version:
Fake-only status:
Runtime behavior changed: no
Safety gate code changed: no
Real owner data present: no
Checksum evidence:
Metrics evidence:
Fixture registry status:
Golden report status:
Rollback evidence:
Audit evidence:
CI status:
Blocking issues:
Recommended next stop:
```

Use `REQUEST_CHANGES` if any required fake evidence, safety boundary, checksum,
metrics, fixture, golden-report, rollback, audit, or approval evidence is
missing.

## No-Go Findings

G2 must block the packet if:

- Real owner, customer, job, or material pricing data appears.
- Parser registration appears.
- CLI flags are added to code.
- Runtime behavior changes.
- Safety gate code changes without a separate approved safety-gate task.
- Existing owner-pricing checks are removed.
- Fake rollback relies on sandbox output or manual edits instead of backup.
- Checksum evidence is missing for checksum-sensitive artifacts.
- Metrics evidence is invented.
- Golden reports and structured audit data disagree.
