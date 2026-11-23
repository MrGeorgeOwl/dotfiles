# Herdr app

This folder keeps the configuration of the Herdr GUI app (`herdr-app`). The app
reads it from `~/.config/herdr-app/`.

## Before you edit

Read the current manuals first. The app changes between releases, and these
manuals are the authority:

```sh
hc --skill           # herdr-core: terminals, agents and programs
herdr-app --skill    # the window: spaces, tabs, panes, keys and mods
```

Then read `~/.config/herdr-app/AGENTS.md`. The app writes this guide on each
start. It describes settings, layouts, keys and mods.

After an edit, make sure that `~/.config/herdr-app/keys.error` (or
`settings.error`) does not exist. Run `herdr-app check ~/.config/herdr-app/mods/<name>`
for each mod that you change.

## What this folder keeps

| Path | Content |
|---|---|
| `keys.json` | Keybinds. `cmd-shift-e` opens Files and `cmd-shift-g` opens Changes. |
| `settings.json` | Fonts, theme, zoom and other personal settings. |
| `themes/` | Color themes. |
| `mods/panel-files/`, `mods/panel-changes/` | Mods that open the Files or Changes view of the side panel. |
| `sync.filter` | The list of the files that sync copies. |

The app owns all other files in `~/.config/herdr-app/`: shipped layouts and
mods, `AGENTS.md`, `.d.ts` files, window state and mod state. It writes them
again, so this folder does not keep them.

## Sync

These are copies, not symlinks, because the app writes `settings.json` itself.
Run the commands from this folder.

Save the local configuration to this folder:

```sh
rsync -av --exclude-from=sync.filter ~/.config/herdr-app/ ./
git diff
```

Restore this folder to the local configuration:

```sh
rsync -av --exclude-from=sync.filter ./ ~/.config/herdr-app/
```

The app applies keys, settings, themes and mods immediately. You do not need to
restart it.

Add `--dry-run` to see the changes before you copy. Neither command deletes
files. When you remove a file, remove it on both sides.

When you add a mod or a new top-level file, add its path to `sync.filter`.
