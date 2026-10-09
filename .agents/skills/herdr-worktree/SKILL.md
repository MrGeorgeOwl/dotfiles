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

Use the installed CLI as the authority: run `herdr --help`, then `herdr worktree`, `herdr tab`, and `herdr agent` to inspect syntax without executing mutations. Read IDs and paths from JSON responses; never invent them. In the examples below, set shell variables from the user's request or those responses and double-quote all substitutions.

## Name

The worktree should be named after the passed Jira issue or with the passed by user name, otherwise ask the user or pick up the name from the purpose of worktree described by user's prompt.

- The user gave a name: use it, trimmed. Do not rewrite it. `rejudging` stays `rejudging`.
- The user gave a Jira key and no separate name: uppercase the key (`SMAP-11111`). A Jira key is letters, a hyphen, and digits. If that same request also states a short topic, append `-<kebab-topic>` (`SMAP-21976-jev-for-planner`). Name shouldn't be long, 4 words max.
- The user's prompt give enough description of the worktree purpose. Create a name out of it, max 4 words in kebab-topic format

## Repo and agent kind

The repo is the checkout the user named, otherwise the current one:

```bash
git -C "$repo_path" rev-parse --show-toplevel
```

Set `repo_path` to the requested checkout, or `$PWD`, before running that command. Store its output as `repo_root`.

Choose the agent from that repo root. The new checkout lives under `~/.herdr/worktrees` and must not affect the choice.

- Root is `/Users/heorhi/code/splitmetrics` or a directory inside it: `claude`
- Otherwise: `pi`

Unless the user names a base, branch from the remote default:

```bash
git -C "$repo_root" symbolic-ref --short refs/remotes/origin/HEAD
```

If that ref is missing, use `main` when it exists, otherwise `master`. Pass it as `--base`.

## Reuse

```bash
herdr worktree list --cwd "$repo_root"
```

If a linked worktree already has this branch, reuse it. Do not create a second checkout.

If the list entry has `open_workspace_id`, use it as `workspace_id` and skip both open and create. Otherwise open the existing checkout:

```bash
herdr worktree open --cwd "$repo_root" --branch "$name" --label "$name" --focus
```

Read the workspace ID and checkout path from the response. If `already_open` is true, reuse the returned workspace. For an existing workspace, discover its tabs and panes rather than assuming it has a creation response's `.result.root_pane`:

```bash
herdr tab list --workspace "$workspace_id"
herdr pane list --workspace "$workspace_id"
```

## Create

```bash
herdr worktree create --cwd "$repo_root" --branch "$name" --base "$base" --label "$name" --focus
```

Do not pass `--path`. Herdr stores the checkout under its worktree directory, slugged from the branch.

## Tabs

For a newly created workspace, leave exactly two tabs, in order: `agent`, then `terminal`. For a reused workspace, preserve existing tabs and their order; ensure an `agent` tab and a `terminal` tab exist without closing any user tabs.

1. Rename the workspace's first tab:

```bash
herdr tab rename "$agent_tab_id" agent
```

2. For a new workspace, use `.result.root_pane.pane_id` as `pane_id` and the returned tab ID as `agent_tab_id`. For a reused workspace, select the pane from its `agent` tab using the tab/pane listings. Start only in an available interactive shell pane; do not overwrite a running process.

Derive the agent name by lowercasing the branch and replacing every character outside `[a-z0-9_-]` with `-`. If the result does not start with `[a-z]`, prefix `agent-`, then truncate to 32 characters. Check `herdr agent list` for collisions. For each suffix (`-2`, `-3`, and so on), truncate the unsuffixed name to `32 - length(suffix)` before appending it. The final name must match `[a-z][a-z0-9_-]{0,31}` and be unique.

```bash
herdr agent start "$agent_name" --kind "$agent_kind" --pane "$pane_id"
```

Set `agent_kind` to `claude` or `pi` using the repo-root rule above. If start returns `agent_not_ready`, leave the pane alone and report that the agent is not ready.

3. Open a shell tab at the new checkout. This keeps focus on the agent tab:

```bash
herdr tab create --workspace "$workspace_id" --cwd "$worktree_path" --label terminal --no-focus
```

When reusing a workspace, list its tabs first. Reuse existing `agent` and `terminal` tabs. For a missing tab, rename a suitable unused shell tab or create one with the checkout cwd and `--no-focus`; preserve tabs occupied by user processes. Use the returned tab and pane IDs for a newly created `agent` tab. Do not start a second agent when the `agent` tab already has one. Do not close tabs the user already had.

## Done

Focus the `agent` tab in the created or reused worktree workspace, not just the workspace (which might have the terminal tab selected):

```bash
herdr tab focus "$agent_tab_id"
```

Report the branch, checkout path, and whether the worktree was created or reused. Do not prompt the agent unless the user requested a handoff.
