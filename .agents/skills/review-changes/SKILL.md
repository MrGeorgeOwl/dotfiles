---
name: review-changes
description: Review uncommitted git changes and suggest improvements before commit. Use when Codex needs to inspect the current working tree, analyze modified files for correctness, bugs, project convention violations, security concerns, and missing error handling, and recommend whether to test, commit, or make changes first.
---

# Review Changes

Review the current working tree before commit. Focus on uncommitted changes, not the full branch, and provide practical feedback on what is good, what is risky, and what should happen next.

## Workflow

1. Check the current working tree.

- Run `git status` first to see which files changed and whether there are staged, unstaged, or untracked files.
- If there are no uncommitted changes, say so explicitly and stop.

2. Inspect the actual diff.

- Run `git diff` to review the content of the changes.
- If staged and unstaged changes differ materially, note that in the review.
- If the diff is large, review file-by-file but do not skip modified files.

3. Analyze each modified file.

- For every modified file, check:
  - whether the change is correct and complete
  - whether there are potential bugs or edge cases
  - whether the code follows project conventions already used in the repository
  - whether there are security concerns such as injection, auth mistakes, unsafe defaults, or data exposure
  - whether error handling is adequate for the changed paths
- Flag missing tests when behavior changes but coverage is absent or unclear.
- Prefer concrete, code-level feedback over generic advice.

4. Summarize the review.

- Separate the output into:
  - what looks good
  - concerns or suggestions
  - recommended next steps
- Recommended next steps should clearly tell the user whether to:
  - test
  - commit
  - make changes first

## Response Format

Use this structure:

```markdown
What looks good
- ...

Concerns or suggestions
- `path/to/file.ext:line` What looks risky or incomplete, and what to improve.

Recommended next steps
- Test
- Commit
- Make changes
```

- If there are no concerns, say so explicitly and recommend testing or committing as appropriate.
- If the diff is ambiguous because necessary context is missing, say what could not be verified.

## Review Standard

Be direct and specific. The point is to improve the pending changes before they are committed.
