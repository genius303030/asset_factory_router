# Auto Workflow Owner Briefing Example

EXAMPLE-ONLY. READ-ONLY. NO AUTO-MERGE.

This briefing uses fake example data to demonstrate the future owner briefing
shape. It is not live sync, not GitHub API output, not a token-backed report,
not an approval record, and not a merge instruction.

## Today's Conclusion

Auto Workflow is on track at the template layer. G1-040 is shown as a completed
inventory example, and G1-041 is shown as a draft owner-briefing template
example. No owner manual intervention is required in this example round.

## PR Status

| PR | Branch | Base | State | CI | Review | Merge readiness |
| --- | --- | --- | --- | --- | --- | --- |
| #39-example | `codex/g1-039-example-task` | `main` | example closed | example pass | example G2 reviewed | example done |
| #40-example | `codex/g1-040-auto-workflow-inventory` | `main` | example draft | example pass | waiting G2 | not ready |
| #41-example | `codex/g1-041-owner-briefing-template-pack` | `codex/g1-040-auto-workflow-inventory` | example draft | not run in example | waiting G2 | not ready |

All PR rows are example-only placeholders. They are not live GitHub status.

## Task Status

| Task | Title | Owner | Status | Priority | Review required | Next action |
| --- | --- | --- | --- | --- | --- | --- |
| G1-039 | Example previous workflow task | G0 | done | P2 | true | No action in this example. |
| G1-040 | Auto Workflow Inventory Pack | G2 | waiting_review | P2 | true | Review inventory and queue map. |
| G1-041 | Owner Briefing Template Pack | G1 | in_progress | P2 | true | Finish template, examples, and tests. |

## G1/G2 Division Of Work

- G1 produces read-only docs, example source data, example briefing markdown,
  tests, validation output, branch, commit, and draft PR.
- G2 reviews whether the briefing format is accurate, safe, and useful for G0.
- G0 decides whether the template is accepted, needs changes, or should become
  the basis for the next Auto Workflow package.

Automation does not approve, does not request review as a substitute for G2,
and does not merge automatically.

## Blocked Items

No blocked items in this example.

| Task | Blocked reason | Current owner | Owner intervention |
| --- | --- | --- | --- |
| none | none | none | no |

## Next Action

- G0: Review the owner briefing shape after G2 comments.
- G1: Keep the package docs/examples/tests only and avoid runtime automation.
- G2: Confirm required sections, example-only safety labels, and no auto-merge
  boundary.

## Owner Manual Action Required

No.

Reason: this example round is waiting on G1/G2 workflow steps, not a G0 business
decision. G0 will need to act manually only when review is complete and an
approval, rejection, merge, or re-scope decision is requested.
