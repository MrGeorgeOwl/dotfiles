"""Entrypoint resolution and agent home layout."""

from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass
from pathlib import Path

from skill_cli.console import CliError


@dataclass(frozen=True)
class Paths:
    agents_dir: Path
    repo_root: Path
    skills_dir: Path
    registry: Path

    @classmethod
    def from_entrypoint(cls, entrypoint: Path) -> Paths:
        if not entrypoint.is_dir():
            raise CliError(f"entrypoint is not a directory: {entrypoint}")
        return cls(
            agents_dir=entrypoint,
            repo_root=entrypoint.parent,
            skills_dir=entrypoint / "skills",
            registry=entrypoint / "skills.yaml",
        )


@dataclass(frozen=True)
class Agent:
    """One agent home: skills dir, optional session-log globs, sync flag."""

    name: str
    home_var: str | None  # None → Path.home() / default_dir
    default_dir: str
    skills_subdir: str
    session_globs: tuple[str, ...]
    synced: bool
    parse: str | None = None  # usage parser key: claude|codex|pi|grok


AGENTS: tuple[Agent, ...] = (
    Agent("agents", "AGENTS_HOME", ".agents", "skills", (), True),
    Agent(
        "codex", "CODEX_HOME", ".codex", "skills",
        ("sessions/**/*.jsonl", "archived_sessions/*.jsonl"), True, "codex",
    ),
    Agent(
        "claude", "CLAUDE_HOME", ".claude", "skills",
        ("projects/**/*.jsonl",), True, "claude",
    ),
    Agent(
        "grok", "GROK_HOME", ".grok", "skills",
        ("sessions/**/updates.jsonl",), True, "grok",
    ),
    Agent(
        "pi", "PI_HOME", ".pi", "agent/skills",
        ("agent/sessions/**/*.jsonl",), False, "pi",
    ),
    Agent(
        "omp", None, ".omp", "agent/skills",
        ("agent/sessions/**/*.jsonl",), False, "pi",
    ),
)

SYNCED: tuple[str, ...] = tuple(a.name for a in AGENTS if a.synced)


def resolve_home_var(var: str, default: str) -> Path:
    return Path(os.environ[var]) if os.environ.get(var) else Path.home() / default


def agent_home(agent: Agent) -> Path:
    if agent.home_var is None:
        return Path.home() / agent.default_dir
    return resolve_home_var(agent.home_var, agent.default_dir)


def agent_skills_dir(agent: Agent) -> Path:
    return agent_home(agent) / agent.skills_subdir


def list_skill_roots() -> dict[str, Path]:
    return {a.name: agent_skills_dir(a) for a in AGENTS}


def resolve_xdg_cache() -> Path:
    return resolve_home_var("XDG_CACHE_HOME", ".cache")


def resolve_config_dir() -> Path:
    return resolve_home_var("XDG_CONFIG_HOME", ".config") / "skill-cli"


def format_config_example(path_hint: str) -> str:
    return (
        f"Create {resolve_config_dir() / 'config.toml'} with:\n"
        f'  entrypoint = "{path_hint}"\n'
        "Or pass --entrypoint PATH / set SKILL_CLI_ENTRYPOINT."
    )


def resolve_entrypoint(cli_value: str | None) -> Path:
    if cli_value:
        return Path(cli_value).expanduser().resolve()
    env = os.environ.get("SKILL_CLI_ENTRYPOINT")
    if env:
        return Path(env).expanduser().resolve()
    cfg = resolve_config_dir() / "config.toml"
    if cfg.is_file():
        try:
            data = tomllib.loads(cfg.read_text())
        except tomllib.TOMLDecodeError as exc:
            raise CliError(f"bad config {cfg}: {exc}") from exc
        ep = data.get("entrypoint")
        if isinstance(ep, str) and ep.strip():
            return Path(ep).expanduser().resolve()
        raise CliError(
            f"{cfg} has no entrypoint string\n"
            + format_config_example("~/code/dotfiles/agents")
        )
    raise CliError(
        "no entrypoint configured\n"
        + format_config_example("~/code/dotfiles/agents")
    )
