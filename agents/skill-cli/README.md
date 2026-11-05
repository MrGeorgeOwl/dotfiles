# skill-cli

Manage skills in this repo's `agents/` folder. Same on macOS and Linux.

## Setup

```toml
# ${XDG_CONFIG_HOME:-~/.config}/skill-cli/config.toml
entrypoint = "~/code/dotfiles/agents"   # Mac
# entrypoint = "~/Projects/dotfiles/agents"  # CachyOS
```

Or `SKILL_CLI_ENTRYPOINT` / `--entrypoint`. No config → CLI exits with the exact file to create.

Optional keep list: `~/.config/skill-cli/keep-skills` (legacy `skills/` and `agent-sync/` paths still read).

Needs `uv`. External `add` needs `npx`.

## Commands

```
uv run --script agents/skill-cli/skill-cli sync [--dry-run]
uv run --script agents/skill-cli/skill-cli status [--json]
uv run --script agents/skill-cli/skill-cli check
uv run --script agents/skill-cli/skill-cli registry
uv run --script agents/skill-cli/skill-cli add NAME
uv run --script agents/skill-cli/skill-cli add PACKAGE SKILL[#REF]
uv run --script agents/skill-cli/skill-cli remove NAME
uv run --script agents/skill-cli/skill-cli eval NAME [args]
```

`add` / `remove` only change the repo (`agents/skills/` + `skills.yaml`). `sync` alone updates `~/.agents`, `~/.codex`, `~/.claude`, `~/.grok` (copy, never symlink; skips `evals/`). External skills are vendored into `agents/skills/<name>/` at add time; sync just copies them.

```
python3 -m unittest discover -s agents/skill-cli/tests -v
```
