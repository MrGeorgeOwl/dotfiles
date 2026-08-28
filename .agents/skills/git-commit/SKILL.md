---
name: git-commit
description: Use when user asks to commit changes in git.
---

# Git Commit

## Commit Format

Use exactly:

```text
<type>: <commit msg>
```

## Types 
Choose the type by the main purpose of the commit:

- `feat`: new feature is added.
- `fix`: bug is fixed.
- `refact`: behaviour is not changed but structure of the code is changed with improving code quality in mind.
- `chore`: maintenance routine that doesn't change the project behaviour. 

Keep `<commit msg>` a short summary of what was done, under 120 characters including the prefix.

## Workflow

1. Inspect the working tree and staged changes before committing.
2. If the user specifies the file names and scope of the work then commit, stage only the requested. Otherwise stage all files
3. Depending on the work done in staged files pick one type for the commit message.
4. Write the commit message in the required format.
5. Run the commit command with the chosen message.

```bash
git commit -m "<feat|fix|refact>: <commit msg>"
```

Do not use other conventional-commit types.

Do not include bot slash commands `/assign` or `/label`.
