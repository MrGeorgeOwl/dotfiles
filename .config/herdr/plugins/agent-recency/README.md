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

Copy the plugin out of the repo, then register the copy:

```sh
mkdir -p ~/.config/herdr/plugins
cp -R ~/code/dotfiles/.config/herdr/plugins/agent-recency ~/.config/herdr/plugins/
herdr plugin link ~/.config/herdr/plugins/agent-recency
herdr plugin action invoke agent-recency.apply
```

`plugin link` only records the path and does not run startup hooks, so the
last command applies the order once. After that, the plugin reapplies on
every agent status change and at each server start. No restart is needed.

## Update

Copy the files again. Herdr runs the new script on the next event. After a
change to `herdr-plugin.toml`, re-register it:

```sh
herdr plugin unlink agent-recency
herdr plugin link ~/.config/herdr/plugins/agent-recency
```

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
