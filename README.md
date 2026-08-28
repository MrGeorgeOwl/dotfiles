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
