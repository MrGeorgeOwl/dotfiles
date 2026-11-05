# agent-recency

Herdr plugin that keeps the spaces with live agents at the top.

- Spaces with a working or blocked agent come first, then the other spaces
  with agents, newest agent status change first. Spaces without agents keep
  their relative order at the bottom.
- Inside each space, the Agents sidebar sorts by attention (blocked, unseen
  done, working, idle), then by newest status change.

It reorders the spaces themselves, so space numbers change as agents work.

## Requirements

Herdr 0.9.5 or newer and `python3` (stdlib only), on macOS or Linux.

## Install

From a clone of this repo, as the user who runs Herdr:

```sh
.config/herdr/plugins/agent-recency/install.sh
```

The script copies the plugin into
`${XDG_CONFIG_HOME:-~/.config}/herdr/plugins/agent-recency` (override with
`HERDR_PLUGIN_DIR`), registers it with `herdr plugin link`, and applies it
once. `plugin link` doesn't run startup hooks, which is why the script applies
it. After that the plugin reapplies on every agent status change and at each
server start, and no restart is needed. If no server is running, the first
apply happens at the next server start.

Re-run the script after pulling changes. It backs up an existing copy that
differs as `agent-recency.bak.<timestamp>` before it overwrites anything, and
it re-registers the plugin so manifest changes take effect.

## Check

```sh
herdr plugin list
herdr plugin log list --plugin agent-recency
```

## Remove

```sh
herdr plugin unlink agent-recency
rm -rf ~/.config/herdr/plugins/agent-recency
```

Unlinking stops further moves but leaves spaces where they are. The sidebar
sort lasts until the next server restart.

## Limits

- Typing to an agent counts only once its status changes.
- Inside one space, an unseen finished agent sorts above a working one.
