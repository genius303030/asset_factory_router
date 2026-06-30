# Owner Pricing Fake Evidence Packet Artifacts

FAKE_ONLY

This document defines the static artifact set added for G1-037. The artifact
set is a fake-only review packet for a future owner-pricing final application
path. It is not an implementation PR and does not add executable final
application behavior.

## Safety Boundary

This PR must remain inside these boundaries:

- No formal final application command is added.
- No parser registration is added.
- No new formal CLI flags are added to code.
- No owner-pricing runtime behavior changes.
- No safety gate code changes.
- No live JSON or sandbox JSON mutation.
- No real owner, customer, job, material, vendor, or pricing data.
- All committed packet data uses `FAKE_ONLY` and obvious fake identifiers.

## Packet Location

The fake packet lives under:

```text
examples/owner_pricing_fake_evidence_packet/
```

The committed artifacts are:

| Artifact | Purpose |
| --- | --- |
| `README.md` | Packet inventory and review boundary. |
| `input/fake_owner_pricing_final_application_input.csv` | Fake input rows for future evidence review. |
| `output/fake_owner_pricing_final_application_output.json` | Fake no-write structured output shape. |
| `audit/fake_owner_pricing_audit_log.json` | Fake event trail and safety state. |
| `owner_report/fake_owner_pricing_owner_report.md` | Fake owner-facing report. |
| `rollback/fake_owner_pricing_rollback_plan.md` | Fake rollback expectations. |
| `checksums/SHA256SUMS.txt` | SHA-256 evidence for packet artifacts. |
| `metrics/fake_owner_pricing_metrics_summary.json` | Fake metrics summary for future review. |
| `fixtures/fake_fixture_registry.json` | Fake fixture registry for the packet. |
| `golden/fake_owner_pricing_golden_report.md` | Deterministic fake golden report. |

## Fake Data Model

The packet intentionally uses only fake identifiers:

- Owner: `FAKE_OWNER_ALPHA`
- Job: `FAKE_JOB_001`
- Materials: `FAKE_MATERIAL_TEST_A`, `FAKE_MATERIAL_TEST_B`,
  `FAKE_MATERIAL_TEST_C`
- Vendor: `FAKE_VENDOR_TEST`

Fake numeric amounts are sample review values only. They are not customer data,
quoted data, bid data, cost data, or owner pricing data.

## Checksum Evidence

`checksums/SHA256SUMS.txt` records SHA-256 hashes for the packet artifacts,
excluding the checksum file itself. G2 should recompute hashes from the checked
out bytes and compare them before accepting packet changes.

`.gitattributes` pins the packet path to LF line endings so checksum evidence
stays stable across Windows and GitHub Actions.

## Metrics Evidence

`metrics/fake_owner_pricing_metrics_summary.json` records:

- task ID: `G1-037`
- workflow category: `owner-pricing`
- workflow stage: `fake_evidence_packet_artifacts`
- docs/tests/examples change flags
- production behavior changed: false
- safety gate changed: false
- live JSON mutated: false
- sandbox JSON mutated: false
- G2/G0/merge status placeholders

## Fixture And Golden Report Evidence

`fixtures/fake_fixture_registry.json` maps each packet artifact to its review
kind and checksum requirement. `golden/fake_owner_pricing_golden_report.md`
provides the deterministic comparison report for G2.

Do not add generated timestamps, machine-specific paths, random IDs, or
environment-dependent output to the golden report.

## G2 Review Focus

G2 should verify:

1. Every packet artifact exists and contains `FAKE_ONLY`.
2. Every checksum in `SHA256SUMS.txt` matches the committed packet bytes.
3. The fake report, output, audit, rollback, metrics, fixture registry, and
   golden report agree on no-write status.
4. No real owner, customer, job, material, vendor, or pricing data is present.
5. No source, parser, CLI, workflow, safety gate, live JSON, or sandbox JSON
   behavior changed.
6. The README link, docs link, and test contract remain current.

## No-Go Conditions

Stop review and return to G0 if a future update:

- Adds executable final application behavior.
- Adds parser registration or formal CLI flags.
- Touches `scripts/check_owner_pricing_safety.py`.
- Mutates live JSON or sandbox JSON.
- Adds real owner, customer, job, material, vendor, or pricing data.
- Updates checksums without a matching artifact change.
- Makes the golden report non-deterministic.
