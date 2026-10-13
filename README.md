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
