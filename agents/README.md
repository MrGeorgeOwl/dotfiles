# Agentic tooling

Repo state for shared agent skills and defaults. Local install targets stay
`~/.agents`, `~/.codex`, `~/.claude`, `~/.grok` (unchanged).

## Layout

- `skills/` — local skills, one folder each (externals are not stored here)
- `skills.yaml` — registry (status/purpose/source/agents; externals use source.url+pin)
- `skill-cli/` — `skill-cli` uv script, tests, short README
- `codex/`, `claude/`, `prompts/` — agent-specific defaults synced by `skill-cli sync`
- `../.pi/` — Pi config synced to `~/.pi/`

## skill-cli

See `skill-cli/README.md`. Quick start after setting `entrypoint` in
`~/.config/skill-cli/config.toml`:

```
uv run --script agents/skill-cli/skill-cli sync --dry-run
uv run --script agents/skill-cli/skill-cli status
```

`add` / `remove` edit this repo only. `sync` updates local agent dirs.

## Merge the latest base into the current branch

Shared skill `skills/merge-base`. After `skill-cli sync`:

| Agent | Command | Explicit base example |
| --- | --- | --- |
| Claude Code | `/merge-base` | `/merge-base develop` |
| Grok | `/merge-base` | `/merge-base upstream/main` |
| Pi | `/skill:merge-base` | `/skill:merge-base develop` |

Run `/reload` in Pi; restart Claude Code if the command is not yet visible.
Grok reloads skills when their files change.

## External skills

Declared in `skills.yaml` with `source.url` / `source.pin` / optional `source.path`.
`skill-cli sync` fetches into `~/.cache/skill-cli/` and installs alongside local skills.

## Imported sources

- Codex: `~/.agents/skills`, `~/.codex/skills`, `~/.codex/config.toml`, `~/.codex/AGENTS.md`
- Claude: `~/.claude/skills`, `~/.claude/commands`, `~/.claude/agents`, `~/.claude/CLAUDE.md`
- Grok: `~/.grok/skills`
- Pi: discovers `~/.agents/skills` (no second copy under `~/.pi`)
