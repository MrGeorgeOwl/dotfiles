"""Copy skills and agent config into local agent homes."""

from __future__ import annotations

import shutil
from pathlib import Path

from skill_cli.console import CliError, FetchError, log, warn
from skill_cli.fetch import fetch_skill_dir, find_cached_skill_dir
from skill_cli.paths import AGENTS, SYNCED, Paths, agent_home, list_skill_roots
from skill_cli.registry import read_registry
from skill_cli.skills import Source, list_repo_skills

SKILL_COPY_SKIP = {"evals", ".git", ".skill-cli-pin"}


def copy_file(src: Path, dest: Path, dry_run: bool) -> None:
    if not src.is_file():
        return
    if dry_run:
        log(f"would copy {src} -> {dest}")
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest)


def copy_dir_contents(
    src: Path, dest: Path, dry_run: bool, skip: set[str] | None = None,
) -> None:
    """Merge src into dest. Destination-only files and dirs are kept."""
    if not src.is_dir():
        return
    if dry_run:
        log(f"would sync {src}/ -> {dest}/")
        return
    skip = skip or set()
    dest.mkdir(parents=True, exist_ok=True)
    for item in list(src.iterdir()):
        if item.name in skip:
            continue
        target = dest / item.name
        if item.is_dir():
            shutil.copytree(item, target, symlinks=True, dirs_exist_ok=True)
        else:
            shutil.copy2(item, target, follow_symlinks=False)


def resolve_agents(fields: dict) -> tuple[str, ...]:
    """Return agents list; invalid values are filtered (check reports them)."""
    raw = fields.get("agents")
    if not isinstance(raw, list) or not raw:
        return SYNCED
    parts = tuple(str(p) for p in raw if str(p) in SYNCED)
    return parts or SYNCED


def sync_all(paths: Paths, dry_run: bool = False) -> int:
    if not paths.agents_dir.is_dir():
        raise CliError(f"missing {paths.agents_dir}")
    registry = read_registry(paths)
    repo_skills = [s for s in list_repo_skills(paths) if (s / "SKILL.md").is_file()]
    externals = [
        (n, fields, src)
        for n, fields in sorted(registry.items())
        if (src := Source.from_fields(fields)) is not None
    ]
    if not repo_skills and not externals:
        raise CliError(f"no skills in {paths.skills_dir} or {paths.registry.name}")

    log(f"entrypoint: {paths.agents_dir}")
    log_order = ("codex", "agents", "claude", "grok", "pi")
    pad = {"codex": "codex:  ", "agents": "agents: ", "claude": "claude: ",
           "grok": "grok:   ", "pi": "pi:     "}
    by_name = {a.name: a for a in AGENTS}
    for name in log_order:
        log(f"{pad[name]}{agent_home(by_name[name])}")

    skill_dests = {label: list_skill_roots()[label] for label in SYNCED}

    for skill in repo_skills:
        fields = registry.get(skill.name, {})
        for label in resolve_agents(fields):
            copy_dir_contents(skill, skill_dests[label] / skill.name, dry_run, skip=SKILL_COPY_SKIP)

    failed_externals: list[str] = []
    for name, fields, src in externals:
        source = src.as_dict()
        try:
            if dry_run:
                content = find_cached_skill_dir(name, source)
                if content is None:
                    log(
                        f"would fetch {src.url}@{src.pin}"
                        + (f" path={src.path}" if src.path else "")
                        + f" then sync {name}"
                    )
                    continue
            else:
                content = fetch_skill_dir(name, source)
        except FetchError as exc:
            warn(str(exc))
            failed_externals.append(name)
            continue
        for label in resolve_agents(fields):
            copy_dir_contents(content, skill_dests[label] / name, dry_run, skip=SKILL_COPY_SKIP)

    prompts = paths.agents_dir / "prompts"
    if prompts.is_dir() and any(
        p.is_file() and p.name != "README.md" for p in prompts.rglob("*")
    ):
        codex_home = agent_home(next(a for a in AGENTS if a.name == "codex"))
        claude_home = agent_home(next(a for a in AGENTS if a.name == "claude"))
        copy_dir_contents(prompts, codex_home / "prompts", dry_run)
        copy_dir_contents(prompts, claude_home / "prompts", dry_run)

    codex_home = agent_home(next(a for a in AGENTS if a.name == "codex"))
    claude_home = agent_home(next(a for a in AGENTS if a.name == "claude"))
    pi_home = agent_home(next(a for a in AGENTS if a.name == "pi"))
    copy_dir_contents(paths.agents_dir / "codex", codex_home, dry_run)
    copy_dir_contents(paths.agents_dir / "claude/commands", claude_home / "commands", dry_run)
    copy_dir_contents(paths.agents_dir / "claude/roles", claude_home / "agents", dry_run)
    copy_file(paths.agents_dir / "claude/CLAUDE.md", claude_home / "CLAUDE.md", dry_run)
    copy_file(paths.agents_dir / "claude/settings.json", claude_home / "settings.json", dry_run)
    copy_dir_contents(paths.repo_root / ".pi", pi_home, dry_run)

    if failed_externals:
        log(f"done with errors: failed externals: {', '.join(failed_externals)}")
        return 1
    log("done")
    return 0
