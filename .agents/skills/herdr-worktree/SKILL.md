---
name: herdr-worktree
description: "Create a Herdr git worktree. Use whenever the user asks to create or start a worktree in Herdr, or to work a Jira ticket in its own Herdr worktree"
---

# Herdr worktree

Create or reuse one Herdr git worktree, then stop. Do not prompt the new agent unless the user asked you to hand it the task.

## Gate

```bash
test "${HERDR_ENV:-}" = 1
```

If that fails, say you are not inside Herdr and stop. Do not create a git worktree by hand.

## Name

The worktree should be named after the passed Jira issue or with the passed by user name, otherwise ask the user or pick up the name from the purpose of worktree described by user's prompt.

- The user gave a name: use it, trimmed. Do not rewrite it. `rejudging` stays `rejudging`.
- The user gave a Jira key and no separate name: uppercase the key (`SMAP-11111`). A Jira key is letters, a hyphen, and digits. If that same request also states a short topic, append `-<kebab-topic>` (`SMAP-21976-jev-for-planner`). Name shouldn't be long, 4 words max.
- The user's prompt give enough description of the worktree purpose. Create a name out of it, max 4 words in kebab-topic format

## Repo and agent kind

The repo is the checkout the user named, otherwise the current one:

```bash
git rev-parse --show-toplevel
```

Choose the agent from that repo root. The new checkout lives under `~/.herdr/worktrees` and must not affect the choice.

- Root is `/Users/heorhi/code/splitmetrics` or a directory inside it: `claude`
- Otherwise: `pi`

Unless the user names a base, branch from the remote default:

```bash
git symbolic-ref --short refs/remotes/origin/HEAD
```

If that ref is missing, use `main` when it exists, otherwise `master`. Pass it as `--base`.

## Reuse

```bash
herdr worktree list --cwd <repo-root>
```

If a linked worktree already has this branch, open it. Do not create a second checkout.

```bash
herdr worktree open --cwd <repo-root> --branch <name> --label <name> --focus
```

If it is already open (`already_open` is true, or the list entry has `open_workspace_id`), focus that workspace and skip create:

```bash
herdr workspace focus <workspace_id>
```

## Create

```bash
herdr worktree create --cwd <repo-root> --branch <name> --base <base> --label <name> --focus
```

Do not pass `--path`. Herdr stores the checkout under its worktree directory, slugged from the branch.

## Tabs

Leave exactly two tabs, in order: `agent`, then `terminal`. Do not add any other tab.

1. Rename the workspace's first tab:

```bash
herdr tab rename <tab_id> agent
```

2. Start the agent in `.result.root_pane.pane_id`. Its name is the branch lowercased, with every character outside `[a-z0-9_-]` replaced by `-`, truncated to 32 characters, and matching `[a-z][a-z0-9_-]{0,31}`. If `herdr agent list` already has that name, append `-2`, `-3`, and so on, still within 32 characters.

```bash
herdr agent start <agent-name> --kind claude --pane <pane_id>
```

Use `--kind pi` when the repo root is outside `/Users/heorhi/code/splitmetrics`. If start returns `agent_not_ready`, leave the pane alone and say so.

3. Open a shell tab at the new checkout. This keeps focus on the agent tab:

```bash
herdr tab create --workspace <workspace_id> --cwd <worktree.path> --label terminal --no-focus
```

When reusing a workspace, list its tabs first. Add or rename only a missing `agent` or `terminal` tab. Do not start a second agent when the `agent` tab already has one. Do not close tabs the user already had.

## Done

Focus the user's herdr session on newly created worktree
