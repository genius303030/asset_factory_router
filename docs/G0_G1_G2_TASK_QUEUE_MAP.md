# G0/G1/G2 Task Queue Map

This document maps a future Auto Workflow task queue to the existing G0/G1/G2
operating model. It is a planning and documentation artifact only. It does not
add a runner, scheduler, GitHub integration, token, runtime mutation, or
production behavior.

## Roles

| Role | Queue ownership | Main responsibility | Cannot do alone |
| --- | --- | --- | --- |
| G0 | Final owner | Sets priority, scope, acceptance criteria, business direction, and merge decision. | G0 does not need to implement the task. |
| G1 | Implementation worker | Creates scoped branch work, updates task evidence, runs checks, and opens PRs. | G1 does not merge its own PR. |
| G2 | QA and documentation officer | Reviews G1 work, checks tests, docs, edge cases, screenshots when relevant, and produces review verdicts. | G2 does not override G0 merge authority. |

## Queue Record

The first example record lives at:

```text
examples/auto_workflow/task_queue.example.json
```

Required fields:

| Field | Meaning |
| --- | --- |
| `task_id` | Stable task ID, such as `G1-040`. |
| `title` | Short human-readable task title. |
| `repo` | Repository target, preferably owner/name when known. |
| `owner` | Current accountable role or person. |
| `status` | Current task state. |
| `priority` | G0/G1/G2 priority label. |
| `next_action` | Concrete next action for the current owner. |
| `blocked_reason` | Empty when unblocked; otherwise the reason work cannot continue. |
| `review_required` | Boolean indicating whether G2 or G0 review is required before completion. |
| `source_pr` | Pull request reference when available; use `null` if not created yet. |
| `source_issue` | Issue reference when available; use `null` if not created yet. |
| `updated_at` | ISO-8601 timestamp for the last queue update. |

## Suggested Status Values

| Status | Meaning | Usual owner |
| --- | --- | --- |
| `candidate` | Task idea exists, but scope is not accepted yet. | G0 |
| `ready_for_g1` | Scope and acceptance criteria are clear enough for implementation. | G1 |
| `in_progress` | G1 is actively working. | G1 |
| `blocked` | Work cannot continue without a decision, artifact, or external state. | Current owner |
| `needs_g2_review` | G1 work is ready for G2 review. | G2 |
| `needs_g0_decision` | Review is complete enough for owner decision. | G0 |
| `done` | Accepted and complete. | G0 |
| `closed` | Intentionally stopped or superseded. | G0 |

## Routing Rules

| Queue signal | Route | Reason |
| --- | --- | --- |
| `status=candidate` | G0 | Scope, priority, and acceptance criteria are not yet fixed. |
| `status=ready_for_g1` | G1 | Implementation can begin. |
| `status=in_progress` | G1 | G1 owns branch work and validation. |
| `status=blocked` with a business or scope blocker | G0 | Owner decision is needed. |
| `status=blocked` with a technical validation blocker | G1 | G1 should attempt a narrow fix or report the blocker. |
| `review_required=true` and branch/PR exists | G2 | Review evidence is needed before G0 merge decision. |
| `status=needs_g2_review` | G2 | QA/documentation review is the next stop. |
| `status=needs_g0_decision` | G0 | Merge, reject, or re-scope decision is needed. |

## Review Required Rule

Set `review_required` to `true` when any of these are true:

- Source code changes.
- CI, scripts, workflow, or validation behavior changes.
- Owner-facing documentation changes.
- Evidence, metrics, fixture, golden report, or approval artifacts change.
- The task affects business rules, safety boundaries, or release readiness.

For docs-only inventory work, review is still required when the output becomes a
source of truth for future work.

## Blocked Reason Rule

Use an empty string when work is unblocked. When blocked, write one plain reason
that G0/G1/G2 can act on, such as:

- `needs_g0_scope_decision`
- `needs_g2_review`
- `waiting_for_pr`
- `waiting_for_ci`
- `missing_required_fixture`
- `requires_private_data_access_decision`
- `requires_token_policy_decision`

Do not hide a blocker inside `next_action`; keep it in `blocked_reason`.

## Owner Briefing Shape

A future owner briefing can be generated from queue records without reading
private data. The minimum briefing should include:

- Task ID and title.
- Repo.
- Current owner.
- Status and priority.
- Next action.
- Blocked reason.
- Review requirement.
- PR and issue references when available.
- Last updated timestamp.

This map does not implement that generator. It only defines the shape G0 can
review before any future automation is added.

## Safety Boundary

This queue map is safe only while it remains docs/example/test level. Future
automation must still preserve these rules:

- No token committed to the repo.
- No external API access from unit tests.
- No production data reads.
- No live or sandbox JSON mutation.
- No owner-pricing runtime change unless G0 explicitly assigns that scope.
