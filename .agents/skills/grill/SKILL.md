---
name: grill
description: Adversarial code review for a git branch before merge. Use when user needs to review all changes on the current branch against its base branch, find bugs and missing tests, check for breaking changes, security issues, and performance regressions, and decide whether the branch is ready to ship.
---

# Grill

Perform a skeptical staff-engineer review of the current branch. Treat the review as a gate: do not approve the branch until every material issue is resolved.

## Workflow

1. Determine the base branch.

- Prefer the repository default branch when it resolves cleanly.
- Check in this order:
  - `origin/main`
  - `origin/master`
  - `main`
  - `master`
- Use the first branch that exists.
- If none exist, state that the base branch could not be determined and stop.

2. Review the full branch diff.

- Run `git diff <base>...HEAD` to inspect every change on the branch.
- Run `git status --short` to catch unstaged or untracked work that may affect the review context.
- If the diff is large, review file-by-file but do not skip files.

3. Review with an adversarial mindset.

- Assume the branch is not ready until proven otherwise.
- Look for:
  - Logic errors
  - Edge cases and failure modes
  - Race conditions and ordering bugs
  - Missing or inadequate tests for changed behavior
  - Breaking changes to public APIs, schemas, or contracts
  - Security problems such as injection, auth bypass, unsafe defaults, or data exposure
  - Performance regressions and unnecessary work on hot paths
- Check whether the implementation is complete, not just plausible.
- Check whether naming, structure, and patterns match the project conventions already present in the repository.

4. Produce a shipping decision.

- Choose exactly one verdict:
  - `SHIP IT`
  - `NEEDS WORK`
  - `BLOCK`
- Use `SHIP IT` only when there are no unresolved material issues.
- Use `NEEDS WORK` when the branch is directionally correct but still has fixable problems.
- Use `BLOCK` when the branch has correctness, safety, compatibility, or rollout risks that make merging unacceptable.

5. Report findings precisely.

- If the verdict is `NEEDS WORK` or `BLOCK`, list every issue separately.
- For each issue, include:
  - severity
  - file path
  - line number or nearest relevant location
  - what is wrong
  - what needs to change
- Prefer concrete, actionable fixes over vague criticism.
- Call out missing tests explicitly and say what behavior must be covered.

6. Summarize what is solid.

- After the issues list, briefly note what looks good so the user knows what does not need rework.
- Keep praise factual and short.

7. Re-review after changes.

- After the user makes fixes, restart from base-branch detection and re-run the branch diff.
- Do not assume prior issues are fixed without verifying the updated code.
- Only return `SHIP IT` when every previously raised issue is resolved and no new issues appear.

## Response Format

Use this structure:

```markdown
Verdict: SHIP IT | NEEDS WORK | BLOCK

What looks good
- ...

Issues
- [severity] `path/to/file.ext:line` Description of the problem and what to fix.

Recommended next step
- Make changes
- Add tests
- Re-run review
- Merge
```

- If there are no issues, say so explicitly in the `Issues` section.
- If the branch cannot be reviewed fully because context is missing, say what is missing and do not give `SHIP IT`.

## Review Standard

Be hard to satisfy. The goal is to prevent bad merges, not to be agreeable.
