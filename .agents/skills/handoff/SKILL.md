---
name: handoff
description: End a coding session by writing HANDOFF.md so a new agent can continue with lean context, then stop.
---

# Session handoff

## Procedure
1. Stop feature work. Do not make “one more fix.”
2. Check worktree, branch, HEAD, and uncommitted changes. Use session knowledge;
   do not restart exploration or run evaluations just for the handoff.
3. Write/update `HANDOFF.md` at the repo/worktree root using the template below.
4. Keep it concise; link details instead of copying them. Preserve user constraints,
   decision rationale, and enough context to start the next action.
5. Remove stale claims and dropped tasks. Distinguish implemented from verified;
   mark unknowns. Require **Ruled out** and **Next actions**; omit irrelevant sections.
6. Reply only with the handoff path and next 1–3 actions. Then stop.

Never include transcripts, tool dumps, full file bodies, secret values, or sensitive
raw data. Do not commit, push, or change ignore rules just to save the handoff.

## Template

```md
# HANDOFF — <project> — <timestamp>

## Goal / done when
<Goal and acceptance criteria.>

## Checkout
- Worktree / branch / HEAD:
- Uncommitted changes / unpushed commits:
- Pre-existing user changes to preserve:

## Constraints
<Explicit user requirements, forbidden actions, approval boundaries,
and data/secret-handling rules.>

## Current state
- Implemented:
- Verified: <revision/configuration, command, result>
- Unverified / remaining / blocked:
- Current design: <key flow and invariants, not implementation history>

## Decisions / ruled out
- Keep: <decision and rationale>
- Ruled out: <approach — failed, user rejected, or superseded; why>
<Write “None” if nothing was ruled out.>

## Files / artifacts
- <path> — <purpose; when to read>
<Identify local-only dependencies, sensitive artifacts, and what must not
be committed or would be missing in another checkout.>

## Operation / verification
- Prerequisites / cwd / relevant commands:
- Evidence: <baseline/latest result and report path; limitations>
- Gotchas: <cost, side effects, concurrency, active jobs>
- Rollout / rollback, if relevant:

## Next actions
1. <Concrete action — expected result/check; approval needed?>
2. …
3. …

## Incoming agent
- Treat this as a snapshot; applicable user/project instructions take precedence.
- Check checkout state and reconcile discrepancies before acting.
- Follow the file map; read linked details only as needed.
- Revisit failed approaches only with new evidence; user-rejected ones need approval.
- Verify relevant changes safely; do not blindly rerun every recorded command.
- Replace stale content as work progresses; do not append a session diary.
```

## New session bootstrap

Read HANDOFF.md, check the checkout matches, and continue from Next actions.
Respect approval boundaries. Load linked details and rerun checks only as needed.
