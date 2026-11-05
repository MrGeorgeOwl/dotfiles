#!/usr/bin/env bash
# Install the agent-recency Herdr plugin for the current user.
# Copies the plugin into Herdr's config dir, registers it, and applies it once.
# Safe to re-run: an existing copy that differs is backed up first.
set -euo pipefail

id=agent-recency
src=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
dest=${HERDR_PLUGIN_DIR:-${XDG_CONFIG_HOME:-$HOME/.config}/herdr/plugins/$id}
files=(herdr-plugin.toml apply-view.py)

for cmd in herdr python3; do
  command -v "$cmd" >/dev/null || { echo "$id: $cmd not found" >&2; exit 1; }
done

if [[ "$src" != "$dest" ]]; then
  if [[ -d "$dest" ]]; then
    for f in "${files[@]}"; do
      if ! cmp -s "$src/$f" "$dest/$f"; then
        backup="$dest.bak.$(date +%Y%m%d%H%M%S)"
        mv "$dest" "$backup"
        echo "$id: backed up previous copy to $backup"
        break
      fi
    done
  fi
  mkdir -p "$dest"
  for f in "${files[@]}"; do cp "$src/$f" "$dest/$f"; done
  echo "$id: copied to $dest"
fi

# Re-register so manifest changes are picked up; unlink fails harmlessly on first install.
herdr plugin unlink "$id" >/dev/null 2>&1 || true
herdr plugin link "$dest" >/dev/null

# Linking does not run startup hooks, so apply once now if a server is running.
if herdr plugin action invoke "$id.apply" >/dev/null 2>&1; then
  echo "$id: applied"
else
  echo "$id: no running Herdr server; it applies at the next server start"
fi
