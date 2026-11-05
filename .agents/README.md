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

## Sync and skills CLI

`.agents/skills-cli` is a uv script (Python 3.11+, stdlib only) that replaces
`agent-sync` and `skill-doctor`. Same behaviour on macOS and Linux.

```
.agents/skills-cli sync [--dry-run]   # copy skills + agent config
.agents/skills-cli status [--json]    # usage, drift, orphans
.agents/skills-cli check              # lint skills.yaml
.agents/skills-cli registry           # regenerate skills.yaml
.agents/skills-cli add NAME
.agents/skills-cli add PACKAGE SKILL[#REF]
.agents/skills-cli remove NAME
.agents/skills-cli eval NAME [args]
```

`sync` copies shared skills into `~/.agents/skills`, `~/.codex/skills`,
`~/.claude/skills`, and `~/.grok/skills` (never symlinks; each skill's `evals/`
is skipped). Pi discovers `~/.agents/skills`, so skills are not also copied into
`~/.pi/agent/skills`. It also copies prompts, Codex and Claude assets, and
`.pi/` → `~/.pi/` (or `$PI_HOME`).

Skills are mirrored. Before copying, `sync` moves any top-level skill folder
(or symlink) in those four homes that is not in the registry to
`~/.local/share/skills/removed-<timestamp>-<pid>/<agent>/<skill>`
(`$XDG_DATA_HOME` is respected). Hidden entries, plain files, and
`~/.pi/agent/skills` are left alone. To keep a local-only skill, add its name
to `~/.config/skills/keep-skills` (`$XDG_CONFIG_HOME`; `#` comments ignored).
The old `~/.config/agent-sync/keep-skills` path is still read if the new one
is missing.

### Registry and external skills

`skills.yaml` is the one list. Repo skills take `name`/`description` from each
`SKILL.md`; you edit `status`, `purpose`, and optionally `agents` (a subset of
`agents,codex,claude,grok`). External skills add `source` (`owner/repo`) and
optional `ref` (branch, tag, or full 40-char SHA). `sync` fetches them with
`npx -y skills add <source>[#<ref>] --skill <name> --copy -y` and copies the
result into the same four homes. A failed fetch warns and keeps installed
copies. A name that also exists under `.agents/skills/` aborts.

```
.agents/skills-cli add humanlayer/skills show-me#4d69d20f6e9b57b4fcf0d501ccfb1be961f0f329
.agents/skills-cli sync
```

`check` fails when the registry is stale, frontmatter is wrong, a status is
unknown, or an external entry collides with a repo folder. Tests run `check`
against the real repo.

### Status report

`status` (read-only) shows loads per skill from Claude Code, Codex, pi, omp
and Grok session logs, `active`/`dormant`/`unknown` usage, copy drift, and
skills installed but not in the registry. Synced orphans are tagged
`skills-cli moves it` unless listed in `keep-skills`; pi and omp are listed
but never pruned. Add `--json` for machine-readable output.

### Local evals

Evals live in `skills/<name>/evals/`, are gitignored, and are not synced.
Put an executable `evals/run` there and run `.agents/skills-cli eval <name>`.
It runs in `evals/` with `SKILL_DIR` set.

```
uv run --script .agents/skills-cli check
python3 -m unittest discover -s .agents/tests -v
```

## Merge the latest base into the current branch

The shared `skills/merge-base/SKILL.md` workflow discovers the PR base (falling
back to repository guidance or the remote default), fetches it, and resolves
conflicts autonomously. After verification, it completes the merge and pushes
the current branch. It never rebases or force-pushes, and asks only for safety
blockers or unresolved decisions.

After running `.agents/skills-cli sync`:

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
