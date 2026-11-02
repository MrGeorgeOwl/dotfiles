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

Skills are mirrored. Before copying, the sync removes any top-level skill folder
(or symlink) in `~/.agents/skills`, `~/.codex/skills`, `~/.claude/skills`, or
`~/.grok/skills` that is not in `.agents/skills` or `.agents/external-skills`.
Removed skills are moved, not deleted, to `~/.local/share/agent-sync/removed-<timestamp>-<pid>/<agent>/<skill>`
(`$XDG_DATA_HOME` is respected), and each one is printed. Symlinks are moved
as links; their targets are never touched. Hidden entries such as
`~/.codex/skills/.system`, plain files, and `~/.pi/agent/skills` are left alone.
To keep a local-only skill, add its name on its own line to
`~/.config/agent-sync/keep-skills` (`$XDG_CONFIG_HOME` is respected; lines
starting with `#` are ignored). `--dry-run` prints `would remove stale skill`
lines without changing anything.

### External skills

Skills published elsewhere are listed in `.agents/external-skills` instead of
being copied into `.agents/skills`. One per line:

```
<package> <skill>[#<ref>]
humanlayer/skills show-me#4d69d20f6e9b57b4fcf0d501ccfb1be961f0f329
```

`<package>` is anything `npx skills add` accepts (usually `owner/repo`).
`<ref>` pins a branch, tag, or full 40-character commit SHA; the skills CLI
cannot clone short SHAs. Without a ref, every sync takes the latest version.
Blank lines and lines starting with `#` are ignored.

For each entry, the sync runs
`npx -y skills add <package>[#<ref>] --skill <skill> --copy -y` in a temporary
folder with `DISABLE_TELEMETRY=1 DO_NOT_TRACK=1`, then copies the skill into
the same four skills folders as the repo skills. Pruning never moves listed
skills. If npx is missing, the network is down, or the skill is not found, the
sync prints a warning, leaves the installed copies alone, and carries on. A
name that also exists in `.agents/skills` aborts the sync. `--dry-run` prints
`would install external skill <skill> from <package>[@<ref>]` without
fetching.

To add one, run `npx skills add <package> --list` to see its skill names, add
a line, then run `.agents/agent-sync`. To update a pinned skill, change the
ref.

Other destination-only files (commands, agents, prompts, configs) are not
deleted. After upgrading from the old sync, compare existing `~/.pi/agent/skills/<name>` directories with their
`~/.agents/skills/<name>` counterparts and move verified duplicate directories
to a backup outside either skills directory. Preserve unique files or local
changes. Symlinks to the same skill files do not cause Pi collisions.
Run `/reload` in Pi after cleanup.

Use `.agents/agent-sync --dry-run` to preview destinations.
Run `python3 -m unittest discover -s .agents/tests -v` for isolated sync tests.

## Merge the latest base into the current branch

The shared `skills/merge-base/SKILL.md` workflow discovers the PR base (falling
back to repository guidance or the remote default), fetches it, and resolves
conflicts autonomously. After verification, it completes the merge and pushes
the current branch. It never rebases or force-pushes, and asks only for safety
blockers or unresolved decisions.

After running `.agents/agent-sync`:

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
