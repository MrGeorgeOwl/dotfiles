# dotfiles

## Chameleon

`chameleon` applies a named theme across Ghostty, btop, Neovim, and the
wallpaper. Its launcher and modules live in `~/.local/bin/chameleon/`; the
zsh customization adds that directory to `PATH`.

```sh
chameleon --list
chameleon latch
chameleon -c ghostty miasma
chameleon --fail-fast dayfox
```

Theme data is stored in `~/.config/chameleon/themes/<theme>.conf` as plain
`component=value` mappings. An absent mapping skips that component; an absent
profile is also reported as a skip. `~/.config/chameleon/current` is updated
only after an unfiltered run applies every component successfully.
