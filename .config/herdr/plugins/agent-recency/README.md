# agent-recency

Herdr plugin: spaces with working/blocked agents go first, then by newest agent
status change; spaces without agents go last. Space numbers change as it reorders.

Needs Herdr 0.9.5+ and python3.

- Install or update: `./install.sh` (re-runnable; backs up a differing copy).
  Installs to `${XDG_CONFIG_HOME:-~/.config}/herdr/plugins/agent-recency`,
  override with `HERDR_PLUGIN_DIR`.
- Check: `herdr plugin log list --plugin agent-recency`
- Remove: `herdr plugin unlink agent-recency`, then delete the installed dir.
