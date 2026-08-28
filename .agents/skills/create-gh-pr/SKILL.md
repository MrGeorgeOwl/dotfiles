---
name: create-gh-pr
description: Use when the user asks Codex to create, open, draft, or publish a GitHub pull request with gh, especially when the PR body should be reviewed or approved before creation.
---

# Create GitHub PR

Create GitHub pull requests from the current branch while respecting the repository's PR template and requiring user approval before publishing.

## Workflow

1. Inspect the branch state.

- Run `git status --short`, `git branch --show-current`, and `git branch -vv`.
- If the working tree is dirty, report it and ask whether to include, commit, or leave changes out before creating the PR.
- Check for an existing PR with `gh pr view --json url,title,state`.

2. Find the PR template.

- Look for GitHub-supported template files in this order:
  - `.github/pull_request_template.md`
  - `.github/PULL_REQUEST_TEMPLATE.md`
  - `docs/pull_request_template.md`
  - `docs/PULL_REQUEST_TEMPLATE.md`
  - `pull_request_template.md`
  - `PULL_REQUEST_TEMPLATE.md`
- If `.github/PULL_REQUEST_TEMPLATE/` exists, list templates and choose the one matching the user request; ask if ambiguous.
- If no template exists, draft a compact body appropriate to the repo and say no template was found.

3. Draft the title and body.

- Use the user-provided title exactly unless they ask for grammar cleanup.
- Fill the discovered PR template. Preserve its headings and structure.
- Remove instructional HTML comments only after their guidance has been applied.
- Include only verification commands that actually passed or that the user explicitly asked to list.
- Keep the body concise.

4. Get user approval.

- Show the exact title and body.
- Ask for approval or edits.
- Do not run `gh pr create` until the user approves the final text.

5. Ensure the branch is pushed.

- If the current branch is ahead of upstream, run `git push`.
- If no upstream exists, run `git push -u origin <branch>`.
- If network access fails due to sandboxing, rerun with escalation.

6. Create the PR.

- Run `gh pr create --title ... --body ...`.
- Prefer the existing upstream/head branch. Add `--base` or `--head` only when repo state or user instructions require it.
- If `gh pr create` reports that the branch must be pushed first, push it and retry.

7. Report the result.

- Return the PR URL.
- Mention if an existing PR was found instead of creating a new one.
- Mention any command that could not be completed.

## Guardrails

- Never create the PR before the user approves the body.
- Never silently change the approved title or body.
- Do not invent verification.
- Do not force-push unless the user explicitly asks.
