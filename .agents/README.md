# Agentic Tooling

Central storage for reusable agent assets.

## Layout

- `skills/` contains agent-agnostic skills gathered from Codex and Claude.
- `codex/` contains Codex-specific defaults.
- `claude/` contains Claude-specific defaults, including `CLAUDE.md`.
- `codex/AGENTS.md` and `claude/CLAUDE.md` hold the same engineering rules; keep them in sync.
- `claude/commands/` contains Claude slash-command prompts.
- `claude/roles/` contains Claude role/subagent prompts.
- `prompts/` is reserved for shared prompts that are not tied to one agent's file format.
- `../.pi/` contains Pi configuration synced to `~/.pi/` (for example, web-search provider settings).

Repo-specific agent settings can still live in repository-level `.codex/` or
`.claude/` folders when those files are meant to affect only this repository.
For example, `.claude/settings.local.json` remains local to this repo.

## Sync

Run `.agents/agent-sync` after changing shared agent assets.
It copies shared skills into `~/.agents/skills`, `~/.codex/skills`,
`~/.claude/skills`, and `~/.grok/skills`. Pi discovers `~/.agents/skills`
automatically, so shared skills are not also copied into `~/.pi/agent/skills`:
separate copies with the same skill name cause Pi collision warnings. Keep that
Pi-specific directory for unique skills. If you override `AGENTS_HOME`, configure
Pi to discover the custom skills location.

It copies shared prompts into both Codex and Claude configs, then copies
Codex-only and Claude-only assets into their matching config folders. It also
copies the repository `.pi/` directory into `~/.pi/` (or `$PI_HOME`).

The sync does not delete destination-only files. After upgrading from the old
sync, compare existing `~/.pi/agent/skills/<name>` directories with their
`~/.agents/skills/<name>` counterparts and move verified duplicate directories
to a backup outside either skills directory. Preserve unique files or local
changes. Symlinks to the same skill files do not cause Pi collisions.
Run `/reload` in Pi after cleanup.

Use `.agents/agent-sync --dry-run` to preview destinations.
Run `python3 -m unittest discover -s .agents/tests -v` for isolated sync tests.

## Imported Sources

- Codex: `~/.agents/skills`, `~/.codex/skills`, `~/.codex/config.toml`, `~/.codex/AGENTS.md`
- Claude: `~/.claude/skills`, `~/.claude/commands`, `~/.claude/agents`, `~/.claude/CLAUDE.md`, `~/.claude/settings.json`
- Grok: `~/.grok/skills`
- Pi: `~/.pi/agent/skills`
