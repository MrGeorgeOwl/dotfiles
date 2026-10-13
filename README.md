# Chameleon

`chameleon` applies a named theme to configured system components.

```sh
chameleon --list                       # List available themes.
chameleon latch                        # Apply `latch` to every component.
chameleon -c ghostty miasma            # Apply `miasma` only to Ghostty.
chameleon --fail-fast dayfox           # Stop when a component cannot apply `dayfox`.
chameleon -v -c wallpaper miasma       # Change the wallpaper and show detailed logs.
```

Successful runs are silent by default. Use `-v` or `--verbose` to show the
component summary and module-level logs.

Theme mappings live in `~/.config/chameleon/themes/<theme>.conf` as plain
`component=value` entries. Missing mappings or profiles skip that component.
`~/.config/chameleon/current` updates only when an unfiltered run applies
all components successfully.

Herdr has no config includes, so the `herdr` component replaces the `[theme]`
and `[theme.*]` tables in `~/.config/herdr/config.toml` with
`~/.config/herdr/themes/<profile>.toml`, keeps every other setting, and runs
`herdr server reload-config` so running clients switch without a restart. It is
a no-op when Herdr is not installed.

Coding agents are configured per theme with `claude=` and `grok=`:

- `claude=custom` installs `~/.config/chameleon/claude/<theme>.json` as the
  Claude Code theme `custom:chameleon`; `claude=light`, `dark` or another
  built-in preset uses that preset instead. Claude Code watches
  `~/.claude/themes`, so running sessions repaint live. A session started
  before the first run, while `theme` was not yet `custom:chameleon`, needs one
  restart.
- `grok=light` or `grok=dark` sets `[ui] theme` in `~/.grok/config.toml` to
  GrokDay or GrokNight; any other built-in name is passed through. Grok has no
  custom colours and reads the theme at startup, so new sessions pick it up.

Both modules keep every other setting, write nothing when the value is already
set, and are a no-op when the agent is not installed. pi follows the terminal
colours on its own and needs no module.

The `desktop` component switches the desktop environment between light and
dark. It is opt-in: a theme sets `desktop=light` or `desktop=dark`, and without
it the module does nothing.

- On KDE Plasma it switches the Theme picker in System Settings > Colors &
  Themes: light themes get Breeze, dark ones Breeze Dark. Set `kde=breeze` or
  `kde=breeze-dark` to override, or use `kde=lookandfeel:<package id>` or
  `kde=colorscheme:<name>` for other themes. The layout is never reset. Applying
  a theme turns off Plasma's Automatic mode. GTK apps follow through KDE's own
  GTK settings sync.
- On GNOME it sets `org.gnome.desktop.interface color-scheme` (untested).
- On macOS it only acts with `desktop_macos=appearance`, and the first run asks
  for permission to control System Events.

It does nothing when the desktop is unknown, the tools are missing, or the
theme is already active. It runs before `wallpaper`, so applying the global
theme cannot leave the wrong wallpaper behind.
