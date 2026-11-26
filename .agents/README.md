# Agentic Tooling

Central storage for reusable agent assets.

## Layout

- `skills/` contains agent-agnostic skills gathered from Codex and Claude.
- `codex/` contains Codex-specific defaults.
- `claude/` contains Claude-specific defaults, including `CLAUDE.md`.
- `codex/AGENTS.md` and `claude/CLAUDE.md` hold the same engineering rules; keep them in sync.
  `~/.codex/AGENTS.md` and `~/.claude/CLAUDE.md` are symlinks to them.
- `claude/commands/` contains Claude slash-command prompts.
- `../.pi/` contains Pi configuration for `~/.pi/` (for example, web-search provider settings).

Repo-specific agent settings can still live in repository-level `.codex/` or
`.claude/` folders when those files are meant to affect only this repository.
For example, `.claude/settings.local.json` remains local to this repo.

## Registry

`skills.yaml` lists every skill. Local skills live in `skills/<name>/`;
external ones carry a `source` (repo URL, pinned commit, path).

## Merge the latest base into the current branch

The shared `skills/merge-base/SKILL.md` workflow discovers the PR base (falling
back to repository guidance or the remote default), fetches it, and resolves
conflicts autonomously. After verification, it completes the merge and pushes
the current branch. It never rebases or force-pushes, and asks only for safety
blockers or unresolved decisions.

Once the skill is installed:

| Agent | Command | Explicit base example |
| --- | --- | --- |
| Claude Code | `/merge-base` | `/merge-base develop` |
| Grok | `/merge-base` | `/merge-base upstream/main` |
| Pi | `/skill:merge-base` | `/skill:merge-base develop` |

Run `/reload` in Pi; restart Claude Code if the command is not yet visible.
Grok reloads skills when their files change.

## Imported Sources

- Codex: `~/.agents/skills`, `~/.codex/skills`, `~/.codex/config.toml`, `~/.codex/AGENTS.md`
- Claude: `~/.claude/skills`, `~/.claude/commands`, `~/.claude/agents`, `~/.claude/CLAUDE.md`, `~/.claude/settings.json`
- Grok: `~/.grok/skills`
- Pi: `~/.pi/agent/skills`
