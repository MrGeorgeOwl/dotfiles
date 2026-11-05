# Agentic tooling

Repo state for shared agent skills and defaults. Local install targets stay
`~/.agents`, `~/.codex`, `~/.claude`, `~/.grok` (unchanged).

## Layout

- `skills/` — every skill (local and vendored external), one folder each
- `skills.yaml` — registry (source of truth for status/purpose/source/ref/agents)
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

## Imported sources

- Codex: `~/.agents/skills`, `~/.codex/skills`, `~/.codex/config.toml`, `~/.codex/AGENTS.md`
- Claude: `~/.claude/skills`, `~/.claude/commands`, `~/.claude/agents`, `~/.claude/CLAUDE.md`
- Grok: `~/.grok/skills`
- Pi: discovers `~/.agents/skills` (no second copy under `~/.pi`)
