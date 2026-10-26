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

## Wallpaper in remote sessions

The `wallpaper` component skips SSH sessions when `SSH_CONNECTION`, `SSH_CLIENT`,
or `SSH_TTY` is non-empty, even with X11 forwarding. On Linux it also skips when
both `DISPLAY` and `WAYLAND_DISPLAY` are unset or empty. This covers headless
Herdr sessions even if SSH variables are not preserved. A running display manager
or reachable user D-Bus is not enough to identify the calling shell as graphical.
Local macOS sessions do not require these Linux display variables.

Local KDE wallpaper calls require `qdbus6` and GNU `timeout` (coreutils). They
have a 5-second timeout, followed by forced termination after one more second if
needed. Errors are reported instead of silently waiting for an unresponsive
Plasma scripting API. Other components are unaffected.

Use `-v` to see why wallpaper was skipped. As with other skipped components,
normal runs continue, `--fail-fast` stops, and an unfiltered run leaves
`~/.config/chameleon/current` unchanged.

## Follow system appearance

On macOS, `watch` follows actual Light/Dark appearance changes, including manual
switches and System Settings > Appearance > Auto. No cron schedule is needed.
Night Shift (display warmth) is unrelated and does not trigger it.

```sh
chameleon watch dayfox miasma           # Foreground; Ctrl-C to stop.
chameleon watch --install dayfox miasma # Start now and automatically at login.
chameleon watch --uninstall            # Stop and remove the login LaunchAgent.
```

The first theme is for Light, the second for Dark. The watcher applies once on
startup, ignores duplicate notifications, and serializes applications. If the
appearance changes during an application, the latest state is applied next.
Watch-triggered runs skip `desktop`, leaving macOS in control of appearance;
normal `chameleon <theme>` runs retain their existing desktop behavior. Failed
applications are logged and retried on the next transition or watcher restart,
not continuously.

The macOS implementation requires Xcode Command Line Tools (`xcode-select
--install`) to compile its small Swift listener on first use or after source
changes. Installing the LaunchAgent additionally requires `python3`. It captures
the installing shell's `PATH` so module tools can be found at login. Re-run
`--install` to change the theme pair or captured `PATH`. Only one watcher can run
at a time; uninstall the service before trying a foreground watcher.

- LaunchAgent: `~/Library/LaunchAgents/local.chameleon.appearance.plist`
- Logs: `~/Library/Logs/chameleon/watch.log`
- Compiled listener: `~/Library/Caches/chameleon/appearance-watcher`

Ghostty's macOS reload invokes its Reload Configuration menu item directly,
without activating the terminal or sending keystrokes. This still uses UI
scripting, and a background watcher does not inherit the terminal's Accessibility
permission. If the log reports a permission failure, grant the watcher access under
System Settings > Privacy & Security > Accessibility (called Device Control and
Data Access on newer macOS versions). Add the executable at the compiled-listener
path above, then restart it with
`launchctl kickstart -k gui/$(id -u)/local.chameleon.appearance`. Recompiling the
listener can invalidate its permission even while the switch remains enabled;
remove and re-add the executable if this happens. Until allowed, Ghostty's theme
file updates but its running windows may keep the old colors.

The listener runs a windowless AppKit application and observes its
`effectiveAppearance`, which follows the system appearance. The legacy
`AppleInterfaceThemeChangedNotification` is also accepted as a refresh hint, but
Settings changes do not depend on it. No polling runs in the background. `watch`
dispatches by platform; Linux and other unsupported platforms currently return a
non-zero exit status with a clear
error instead of starting a watcher.

Tests (use temporary configs and never switch your actual appearance):

```sh
python3 -m unittest discover -s .local/bin/chameleon/tests -v
```

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
