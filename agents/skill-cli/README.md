# skill-cli

Manage skills in this repo's `agents/` folder. Same on macOS and Linux.

## Setup

```toml
# ${XDG_CONFIG_HOME:-~/.config}/skill-cli/config.toml
entrypoint = "~/code/dotfiles/agents"   # Mac
# entrypoint = "~/Projects/dotfiles/agents"  # CachyOS
```

Or `SKILL_CLI_ENTRYPOINT` / `--entrypoint`. No config → CLI exits with the exact file to create.

Needs `uv` and `git` (git only for external skills).

## Commands

```
uv run --script agents/skill-cli/skill-cli sync [--dry-run]
uv run --script agents/skill-cli/skill-cli status [--json]
uv run --script agents/skill-cli/skill-cli check
uv run --script agents/skill-cli/skill-cli registry
uv run --script agents/skill-cli/skill-cli add NAME
uv run --script agents/skill-cli/skill-cli add NAME --source URL --pin SHA [--path SUBDIR]
uv run --script agents/skill-cli/skill-cli remove NAME
uv run --script agents/skill-cli/skill-cli eval NAME [args]
```

`add` / `remove` only change the repo (`agents/skills/` + `skills.yaml`). `sync` alone updates `~/.agents`, `~/.codex`, `~/.claude`, `~/.grok` (copy, never symlink; skips `evals/`). Sync only adds/updates — it never deletes local skills that are not in the repo.

Because sync merges, files deleted or renamed inside a repo skill stay in the agent folders until removed by hand; drift detection only hashes `SKILL.md`.

External skills are registry-only (`source.url` + `source.pin` as a 40-char commit SHA, optional `source.path`). Sync fetches them into `${XDG_CACHE_HOME:-~/.cache}/skill-cli/` and copies out; nothing is vendored under `agents/skills/`. A failed external fetch is reported and the rest of sync continues (exit non-zero).

```
python3 -m unittest discover -s agents/skill-cli/tests -v
```

## Layout

```
agents/skill-cli/
  skill-cli           # PEP 723 uv-script entrypoint (shebang + imports main)
  skill_cli/          # package: console, paths, skills, fetch, registry, sync, usage, status, cli
  tests/
```

The `skill-cli` script cannot be copied alone — it imports the adjacent `skill_cli/` package (a symlink to the script is fine; the package must sit next to the real file).

