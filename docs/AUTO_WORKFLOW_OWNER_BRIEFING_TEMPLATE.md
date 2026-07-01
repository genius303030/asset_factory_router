# Auto Workflow Owner Briefing Template

G1-041 adds the first owner briefing template for the Auto Workflow mainline.
This is a read-only documentation and example layer. It does not add a queue
runner, scheduler, GitHub collector, token flow, external API call, production
behavior, owner-pricing runtime change, or live/sandbox JSON mutation.

## Purpose

The owner briefing is the short daily or per-round report G0 can read before
deciding what should move next. It turns task queue records, PR status notes,
review state, blockers, and next actions into one owner-facing summary.

The briefing is not an approval engine. It does not merge PRs, approve work,
close tasks, or replace G0 judgment.

## Required Sections

Every owner briefing should include these sections in this order:

1. Today's Conclusion
2. PR Status
3. Task Status
4. G1/G2 Division Of Work
5. Blocked Items
6. Next Action
7. Owner Manual Action Required

## Section Guide

### Today's Conclusion

State the shortest useful conclusion for G0. This should answer whether the
current round is on track, waiting for review, blocked, or ready for an owner
decision.

Recommended fields:

- Overall status.
- One-line reason.
- Whether manual owner intervention is required.

### PR Status

List only PR facts needed for owner decision-making:

- PR number or example placeholder.
- Branch.
- Base branch.
- Draft or ready state.
- CI state when known.
- Review state.
- Merge readiness.

When the data is example-only or manually entered, label it clearly. Do not
claim live sync unless a future G0-approved collector exists.

### Task Status

Summarize active tasks from the queue:

- Task ID.
- Title.
- Owner role.
- Status.
- Priority.
- Next action.
- Review requirement.

### G1/G2 Division Of Work

Separate implementation ownership from review ownership:

- G1 produces branches, docs, examples, tests, and validation evidence.
- G2 reviews the work, checks docs/tests/evidence, and reports risks.
- G0 makes business, priority, scope, approval, and merge decisions.

Automation may prepare or format briefing data, but it must not approve,
request review as a substitute for G2, or merge automatically.

### Blocked Items

List only active blockers. Each blocker should include:

- Task ID.
- Blocked reason.
- Current owner.
- Required decision or artifact.
- Whether the owner needs to intervene.

If there are no blockers, say so plainly.

### Next Action

Give the next action for each route:

- G0 next action.
- G1 next action.
- G2 next action.

Each action should be concrete enough for the role to execute without reading
the whole queue.

### Owner Manual Action Required

State whether G0 must act manually:

- `yes`: G0 must decide, approve, reject, merge, unblock, or change scope.
- `no`: G0 can monitor; work is waiting on G1/G2 or CI.

This section should not hide a required owner decision inside general notes.

## Source Data Shape

The example source file lives at:

```text
examples/auto_workflow/owner_briefing.source.example.json
```

Required top-level fields:

- `generated_at`
- `repo`
- `open_prs`
- `active_tasks`
- `waiting_review`
- `blocked_items`
- `next_actions`
- `owner_manual_action_required`

Future generator work can read this shape only after G0 approves the source
policy. Until then, examples remain static, fake, and manually maintained.

## Example Briefing

The example briefing lives at:

```text
examples/auto_workflow/owner_briefing.example.md
```

It uses example-only fake data. It may mention G1-039 or G1-040 as sample task
states, but it is not a live sync, not a GitHub API result, and not a merge
decision.

## G0/G1/G2 Use

- G1 may produce briefing source data and markdown output.
- G2 may verify that the briefing matches queue records, PR facts, checks, and
  safety boundaries.
- G0 decides whether to approve, reject, merge, re-scope, or unblock work.

No automation should auto-merge, auto-approve, or bypass G0/G2 review.

## Safety Boundary

- Read-only template and examples only.
- No queue runner.
- No scheduler.
- No GitHub collector.
- No token flow.
- No environment variable reads.
- No external API calls.
- No automatic merge.
- No production behavior.
- No real owner-pricing data.
- No owner-pricing runtime changes.
- No live JSON mutation.
- No sandbox JSON mutation.
