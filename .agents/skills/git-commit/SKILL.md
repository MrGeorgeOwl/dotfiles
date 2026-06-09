---
name: git-commit
description: Create git commits with the required message format. Use when the user asks Codex to commit changes, prepare a commit, choose a commit message, or review staged changes before committing.
---

# Git Commit

## Commit Format

Use exactly:

```text
<feat|fix|refact>: <commit msg>
```

Choose the type by the main purpose of the commit:

- `feat`: new feature is added.
- `fix`: bug is fixed.
- `refact`: code structure or implementation quality is improved without changing intended behavior.

Keep `<commit msg>` a short summary of what was done, under 120 characters including the prefix.

## Workflow

1. Inspect the working tree and staged changes before committing.
2. If only part of the work should be committed, stage only the requested or relevant files.
3. Pick exactly one type: `feat`, `fix`, or `refact`.
4. Write the commit message in the required format.
5. Run the commit command with the chosen message.

Use a complete quoted `-m` argument when committing:

```bash
git commit -m "<feat|fix|refact>: <commit msg>"
```

Ensure the opening and closing double quote characters are both present in the
actual shell command.

Do not use other conventional-commit types such as `docs`, `chore`, `test`, `style`, or `perf`.

Do not include PR, issue, or bot slash commands such as `/assign` or `/label`;
they do not work in commit messages or PR descriptions.
