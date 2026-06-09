# Agentic Tooling

Central storage for reusable agent assets.

## Layout

- `skills/` contains agent-agnostic skills gathered from Codex and Claude.
- `codex/` contains Codex-specific defaults.
- `claude/` contains Claude-specific defaults.
- `claude/commands/` contains Claude slash-command prompts.
- `claude/roles/` contains Claude role/subagent prompts.
- `prompts/` is reserved for shared prompts that are not tied to one agent's file format.

Repo-specific agent settings can still live in repository-level `.codex/` or
`.claude/` folders when those files are meant to affect only this repository.
For example, `.claude/settings.local.json` remains local to this repo.

## Sync

Run `.agents/agent-sync` after changing shared agent assets.
It copies shared skills and prompts into both Codex and Claude configs, then
copies Codex-only and Claude-only assets into their matching config folders.

Use `.agents/agent-sync --dry-run` to preview destinations.

## Imported Sources

- Codex: `~/.codex/skills`, `~/.codex/config.toml`, `~/.codex/AGENTS.md`
- Claude: `~/.claude/skills`, `~/.claude/commands`, `~/.claude/agents`, `~/.claude/CLAUDE.md`, `~/.claude/settings.json`
