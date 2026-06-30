# Owner Pricing Fake Evidence Packet Verifier

FAKE_ONLY

G1-038 adds a standalone verifier for the committed fake evidence packet under
`examples/owner_pricing_fake_evidence_packet/`. The verifier is documentation
and tooling only. It does not register an `asset-factory` CLI command, does not
add formal owner-pricing CLI flags, does not change owner-pricing runtime
behavior, does not touch live or sandbox JSON, and does not modify the
owner-pricing safety gate.

## Local Command

Run the verifier from the repository root:

```bash
py -3.12 -B scripts/verify_owner_pricing_fake_evidence_packet.py
```

The command exits `0` when the fake packet is valid and `1` when any check
fails. It verifies the repository packet by default.

## CI Wiring

G1-039 wires the standalone verifier into GitHub Actions as part of the Python
validation job. The CI step runs:

```bash
python scripts/verify_owner_pricing_fake_evidence_packet.py
```

The verifier runs after the owner-pricing safety gate and metrics baseline
validation, and before Ruff check-only lint. This keeps fake evidence packet
integrity in the regular PR validation chain without registering an
`asset-factory` CLI command, adding CLI flags, changing owner-pricing runtime
behavior, or changing the safety gate.

## Verifier Checks

The verifier checks:

- Required packet artifacts exist.
- Every artifact contains `FAKE_ONLY`.
- Packet line endings remain LF-only for checksum stability.
- Required fake identifiers are present:
  - `FAKE_OWNER_ALPHA`
  - `FAKE_JOB_001`
  - `FAKE_MATERIAL_TEST_A`
  - `FAKE_VENDOR_TEST`
- Identifier fields in CSV and JSON artifacts use `FAKE_` values.
- Private or production-looking owner/customer/job/material/vendor markers are
  absent.
- `checksums/SHA256SUMS.txt` lists every checksum-required packet artifact and
  every listed SHA-256 value matches the committed bytes.
- Output, audit, metrics, and fixture registry JSON artifacts parse.
- No-write and no-runtime-change safety flags remain false.
- The golden report has a deterministic ID and no generated timestamp,
  machine-specific path, or environment-dependent marker.

## Safety Boundary

This verifier is not a future final application path. It only checks static
fake artifacts. A future runtime implementation still requires separate G0
approval, G2 review, CI gate updates, and a new scoped PR.

## G2 Review Focus

G2 should confirm this PR:

1. Adds only the standalone verifier, docs, tests, and README link.
2. Does not change `src/asset_factory/`, parser registration, production
   behavior, safety gate code, live JSON, or sandbox JSON.
3. Keeps the verifier fake-packet-only by default.
4. Covers success, missing file, missing `FAKE_ONLY`, and checksum mismatch in
   tests.
5. Runs the verifier in local validation and checks GitHub Actions before
   marking the PR ready.
