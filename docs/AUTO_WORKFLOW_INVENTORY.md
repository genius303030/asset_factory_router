# Auto Workflow Inventory

G1-040 creates the first Auto Workflow inventory pack. This pack is read-only
documentation, examples, and tests. It does not add automation runtime, connect
to GitHub, add a GitHub API token, read private data, change owner-pricing
runtime behavior, or mutate live or sandbox JSON.

## Purpose

Auto Workflow is the future coordination layer for task intake, task queue
state, G0/G1/G2 routing, validation evidence, and owner briefing. The current
repository already has several workflow-adjacent pieces, but they are not yet a
single task queue or automation system.

This document answers two G0 questions:

1. What automation, workflow, CI, evidence, metrics, and owner briefing surfaces
   already exist?
2. What is still missing before a safe Auto Workflow layer can be designed?

## Safety Boundary

- Documentation, examples, and tests only.
- No production behavior.
- No owner-pricing runtime changes.
- No real owner, customer, job, material, vendor, or pricing data.
- No GitHub API token, personal access token, credential, or private key.
- No live JSON mutation.
- No sandbox JSON mutation.
- No external API calls from tests.
- No new dependency or service runner.

## Current Auto Workflow Surfaces

| Area | Current files | What exists | Current limitation |
| --- | --- | --- | --- |
| PR CI | `.github/workflows/python-ci.yml` | Pull request validation on Python 3.12 with install, unit tests, owner-pricing tests, owner-pricing safety gate, and Ruff. | CI validates a PR, but it does not create or update a task queue. |
| Engineering workflow | `docs/ENGINEERING_WORKFLOW.md` | Local and CI validation rules, Ruff policy, and G0/G1/G2 usage notes. | It defines validation behavior, not task assignment or status routing. |
| Task intake templates | `.github/ISSUE_TEMPLATE/agent-task.md`, `.github/PULL_REQUEST_TEMPLATE.md` | Manual issue and PR structure for scope, checks, risks, and G0 review notes. | Templates are human-filled and not normalized into a queue artifact. |
| Owner-pricing safety gate | `scripts/check_owner_pricing_safety.py`, `docs/OWNER_PRICING_CI_GATE.md` | Read-only checks for CLI boundaries, parser registration, ignored private paths, tracked data, safety markers, and CI wiring. | It is owner-pricing-specific and not a general Auto Workflow gate. |
| Metrics tooling | `scripts/collect_pr_metrics.py`, `docs/METRICS_BASELINE.md`, `docs/OWNER_PRICING_WORKFLOW_METRICS.md`, `examples/metrics/owner_pricing_pr_metrics.csv` | A CSV-backed PR metrics baseline with schema validation and summary output. | It is manually curated and covers owner-pricing history, not live task status. |
| Fake evidence verifier | `scripts/verify_owner_pricing_fake_evidence_packet.py` | Static fake evidence packet verification for required files, checksums, fake markers, and no-write structured flags. | It verifies one owner-pricing packet shape, not arbitrary workflow evidence. |
| Evidence docs | `docs/OWNER_PRICING_FAKE_IMPLEMENTATION_EVIDENCE_PACKET.md`, `docs/OWNER_PRICING_FAKE_EVIDENCE_PACKET_ARTIFACTS.md`, `docs/OWNER_PRICING_FAKE_EVIDENCE_PACKET_VERIFIER.md` | Review rules for fake-only implementation evidence, owner-facing reports, checksums, fixtures, metrics, and G2/G0 review. | Evidence rules are strong but scoped to owner-pricing fake evidence. |
| Fixture and golden docs | `docs/OWNER_PRICING_FIXTURE_REGISTRY.md`, `docs/OWNER_PRICING_GOLDEN_REPORTS.md`, `examples/owner_pricing/README.md` | Update rules for checksum-sensitive fake fixtures and deterministic golden reports. | They do not define cross-project task queue records. |
| Owner briefing surfaces | `examples/owner_pricing_fake_evidence_packet/owner_report/fake_owner_pricing_owner_report.md`, owner approval and G0/G2 checklist docs | Owner-readable summaries and approval/review checklists exist in the owner-pricing lane. | There is no general owner briefing generator or standard digest format for all Auto Workflow tasks. |
| Test contracts | `tests/test_metrics_baseline.py`, `tests/test_owner_pricing_*`, `tests/test_production_import_plan_docs.py` | Tests enforce docs, examples, metrics schema, fake evidence, command contracts, and safety boundaries. | Existing tests protect specific lanes; they do not yet validate a general queue schema beyond this pack. |

## Workflow Document Inventory

The current workflow documentation is mostly owner-pricing-centered:

- `docs/ENGINEERING_WORKFLOW.md` defines CI and local validation.
- `docs/OWNER_PRICING_DRY_RUN.md` documents dry-run preview behavior.
- `docs/OWNER_PRICING_SANDBOX_APPLY_PLAN.md` documents reviewable sandbox
  planning.
- `docs/OWNER_PRICING_SANDBOX_APPLY_OUTPUT.md` documents sandbox-only output.
- `docs/OWNER_PRICING_APPROVAL_GATE.md` documents owner approval gating.
- `docs/OWNER_PRICING_FINAL_IMPORT_*` documents planning, preflight, design
  gate, checklist, audit schema, rollback, and fake rehearsal boundaries.
- `docs/OWNER_PRICING_COMMAND_CONTRACT.md` and related G2 review docs document
  future command-contract expectations.
- `docs/OWNER_PRICING_TEST_MATRIX.md` defines required future test evidence.

These documents are useful building blocks for Auto Workflow because they show
how to separate planning, fake evidence, G2 review, G0 approval, and production
no-go states.

## Script Inventory

| Script | Mode | Network access | Purpose |
| --- | --- | --- | --- |
| `scripts/check_owner_pricing_safety.py` | Read-only validation | No | Ensures owner-pricing safety boundaries and CI wiring remain intact. |
| `scripts/collect_pr_metrics.py` | Read-only validation and summary | No | Validates and summarizes the committed PR metrics CSV. |
| `scripts/verify_owner_pricing_fake_evidence_packet.py` | Read-only validation | No | Verifies the committed fake evidence packet artifacts and checksums. |

There is no script that reads GitHub issues, reads GitHub PRs, updates a task
queue, writes owner briefings, or runs scheduled automation.

## Example And Evidence Inventory

- `examples/metrics/owner_pricing_pr_metrics.csv` is the current metrics
  baseline.
- `examples/owner_pricing/` contains fake owner-pricing fixtures and golden
  artifacts for dry-run, sandbox, approval, preflight, design-gate, and fake
  rehearsal review.
- `examples/owner_pricing_fake_evidence_packet/` contains a static fake evidence
  packet with fake input, output, audit, owner report, rollback plan, checksums,
  metrics, fixture registry, and golden report.

These examples are intentionally fake-only. They are useful patterns for future
Auto Workflow examples, but they should not be treated as live data sources.

## What Is Missing For Auto Workflow

The current repo does not yet have these Auto Workflow pieces:

1. A general task queue schema that every G0/G1/G2 task can use.
2. A queue reader or writer.
3. A read-only collector for issue, PR, CI, review, and merge state.
4. A source policy that says whether future collection uses manual exports,
   GitHub connector access, or another approved path.
5. A standard owner briefing format for cross-lane task status.
6. A normalized evidence manifest for non-owner-pricing tasks.
7. A status transition policy from intake to G1 work, G2 review, G0 decision,
   blocked, done, or archived.
8. A clear rule for when `review_required` is true.
9. A standard blocked-reason vocabulary.
10. A scheduled or triggered automation plan.
11. A durable run log for future automation attempts.
12. A no-secrets policy for future local or connector-based collectors.

This PR starts only items 1, 5, 7, and 8 at documentation/example level through
`docs/G0_G1_G2_TASK_QUEUE_MAP.md` and
`examples/auto_workflow/task_queue.example.json`.

## G0 Readiness Summary

Auto Workflow is not ready for runtime automation yet.

The safe next step is to keep the next layer read-only:

- Expand the task queue schema with more examples.
- Add tests that validate status values and required fields.
- Define an owner briefing markdown template from queue records.
- Decide whether future issue or PR state should be entered manually or
  collected through an explicitly approved connector path.
- Keep tokens and private data out of the repository.

## Stop Conditions

Stop and return to G0 before continuing if a future Auto Workflow task requires:

- Storing credentials in the repo.
- Calling the GitHub API from tests.
- Reading private customer or owner data.
- Writing live JSON or sandbox JSON.
- Changing owner-pricing runtime behavior.
- Turning a docs/example/test queue into a production runner.
