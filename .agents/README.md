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
`~/.grok/skills` that is not in `.agents/skills`. Removed skills are moved, not
deleted, to `~/.local/share/agent-sync/removed-<timestamp>-<pid>/<agent>/<skill>`
(`$XDG_DATA_HOME` is respected), and each one is printed. Symlinks are moved
as links; their targets are never touched. Hidden entries such as
`~/.codex/skills/.system`, plain files, and `~/.pi/agent/skills` are left alone.
To keep a local-only skill, add its name on its own line to
`~/.config/agent-sync/keep-skills` (`$XDG_CONFIG_HOME` is respected; lines
starting with `#` are ignored). `--dry-run` prints `would remove stale skill`
lines without changing anything.

Other destination-only files (commands, agents, prompts, configs) are not
deleted. After upgrading from the old sync, compare existing `~/.pi/agent/skills/<name>` directories with their
`~/.agents/skills/<name>` counterparts and move verified duplicate directories
to a backup outside either skills directory. Preserve unique files or local
changes. Symlinks to the same skill files do not cause Pi collisions.
Run `/reload` in Pi after cleanup.

Use `.agents/agent-sync --dry-run` to preview destinations.
Run `python3 -m unittest discover -s .agents/tests -v` for isolated sync and
skill-doctor tests.

## Skills registry and skill-doctor

`skills.yaml` lists every shared skill once. `name` and `description` are
copied from each `SKILL.md`; `status` (`active`, `experimental`, `deprecated`)
and `purpose` are yours to edit. After adding a skill or changing a
description, run `.agents/skill-doctor registry`; it keeps your edits. The
tests run `.agents/skill-doctor registry --check`, which fails when the file is
stale, a frontmatter `name` does not match its folder, or a folder has no
`SKILL.md`.

Run `.agents/skill-doctor` on each machine to see, without changing anything:

- loads per skill from the Claude Code, Codex, pi, omp and Grok session logs,
  with each log's date window (a load means the skill was read, not that it
  helped; zero loads only covers that window);
- `usage`: `active` if loaded within 60 days of the newest log day,
  `dormant` if not, `unknown` if the machine has no logs;
- installed copies whose `SKILL.md` differs from the repo (`drift`) or is
  missing;
- skills installed but not in the repo, which agent-sync would move unless
  they are in `keep-skills`.

Add `--json` for machine-readable output.

### Local evals

Evals live in `skills/<name>/evals/` and stay on your machine: the folder is
gitignored and agent-sync does not copy it. Put an executable `evals/run`
there (it can call `claude plugin eval`, a regex check script, or anything
else) and run it with `.agents/skill-doctor eval <name> [args]`. It runs in the
`evals/` folder with `SKILL_DIR` set, and its exit code is returned. Evals that
call a model cost money on each run.

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
