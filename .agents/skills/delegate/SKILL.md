---
name: delegate
description: Hand a side job (an improvement, refactor or out-of-scope fix found mid-task) to a new, unmonitored agent session in its own Herdr tab or space, then carry on with the current task. Use when the user says delegate, spin off or "do this in another session/tab". Not for subagents or work whose result the current task needs.
---

# Delegate

Start a separate agent in Herdr that finishes the job on its own. You do not
watch it, wait for it or collect its result.

Outside Herdr (`$HC_TERMINAL_ID` unset or no `herdr-app`), stop and ask the
user what to do instead. Offer options, such as a background subagent in a
worktree, or a written brief for them to start by hand.

Shell variables do not survive between tool calls: run each block in one
call and carry paths into later steps written out in full. Use `git -C`
rather than `cd`.

## 1. Pick the checkout

The finding decides the target repository, which need not be the one you
work in. The job always gets a new branch; where it lives depends on whether
the repository's checkout is free:

```sh
top=$(git -C <target repository> rev-parse --show-toplevel)
git -C "$top" status --porcelain      # any output: not free
# Live local agents (they report a status) whose current folder is inside it.
for t in $(hc ls | jq -r '.terminals[] | select(.state == "live"
    and has("status") and (.address | contains("/") | not)) | .address'); do
  hc get "$t" | jq -r --arg top "$top" '(.foreground.cwd // "") as $cwd
    | select($cwd == $top or ($cwd | startswith($top + "/")))
    | "\(.address) \(.labels.where)"'
done                                  # any agent listed: not free
```

`hc ls` shows the launch folder, so read the current one with `hc get`. The
current repository is never free: you are working in it.

```sh
top=<repository top-level>
branch=<type>/<short-slug>            # e.g. refactor/extract-retry-policy
git -C "$top" fetch origin
git -C "$top" rev-parse -q --verify origin/HEAD >/dev/null \
  || git -C "$top" remote set-head origin --auto

# Free: switch the checkout itself to the new branch.
git -C "$top" switch -c "$branch" origin/HEAD
echo "$top"

# Not free: a worktree in Herdr's worktree folder.
dir=~/.herdr/worktrees/$(basename "$top")/${branch//\//-}
git -C "$top" worktree add -b "$branch" "$dir" origin/HEAD
echo "$dir"
```

Base on `origin/HEAD`. Use your branch's `HEAD` only when the target is your
current repository and the job builds on its commits. Uncommitted changes do
not travel; say so in the brief if they matter.

## 2. Write the brief

The new agent knows nothing about this session. Include:

- Goal, and why it came up (what you found, where: file and line).
- Files and modules in play; what is out of scope.
- Done when: the exact lint/test commands that must pass, and that the work
  ends committed on its branch. No push or PR unless the user asked.
- Work alone: no reporting back to this session, stop and ask the user in
  its own tab only when blocked.

## 3. Open it without taking focus

Launch the same agent CLI you run as (`claude`, `codex`, `pi`, ...) unless the
user names another. Through `herdr-app` the session belongs to the window,
not to you, so it outlives this session.

Pick the project's space in `herdr-app ls`: your own (the one holding
`$HC_TERMINAL_ID`) for the current repository. Otherwise a local space
(`machine` null) named like the target's folder, or whose `folder` is its
top-level; a space's `folder` can be stale, so the name counts first. Found:
open a tab in it. None: open a new space.

```sh
task=$(cat <<'EOF'
<brief>
EOF
)
herdr-app do tab.new --space <space-id> --name "<short name>" \
  --folder <checkout> --argv '["claude"]' --task "$task" --focus false
# or, without a space for the project:
herdr-app do space.new --name "<short name>" --folder <checkout> \
  --argv '["claude"]' --task "$task" --focus false
```

Read the reply: it must hold the new `terminal` ID, not `error`. Then
`hc wait <terminal> --timeout 30` and `hc get <terminal>`. A `blocked` status
(a new worktree often asks "trust this folder") is the user's decision: do
not answer it. The task starts once they do.

## 4. Return to the current task

Tell the user in one line: tab or space name, branch, folder, and whether it
waits on them. Then resume where you left off. Do not `hc wait`, `hc read`
or poll it again.
