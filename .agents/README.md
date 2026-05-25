# Agentic Tooling

Central storage for reusable agent assets.

## Layout

- `skills/` contains agent-agnostic skills gathered from Codex and Claude.
- `claude/commands/` contains Claude slash-command prompts.
- `claude/roles/` contains Claude role/subagent prompts.
- `prompts/` is reserved for shared prompts that are not tied to one agent's file format.

Agent-specific defaults, permissions, and rule formats stay in the repository-level
`.codex/` and `.claude/` folders.

## Imported Sources

- Codex: `~/.codex/skills`, `~/.codex/rules/default.rules`, `~/.codex/config.toml`, `~/.codex/AGENTS.md`
- Claude: `~/.claude/skills`, `~/.claude/commands`, `~/.claude/agents`, `~/.claude/CLAUDE.md`, `~/.claude/settings.json`

When the same skill existed in both Codex and Claude, the file with the newest
mtime won. The only duplicated skill with different content was `grill`, where
the Claude copy was newer.
