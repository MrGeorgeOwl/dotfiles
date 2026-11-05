"""Manage shared agent skills. One CLI for sync, status, registry, and evals.

  skill-cli sync [--dry-run]          copy skills (local + external) to agent dirs
  skill-cli status [--json]           usage, drift, orphans on this machine
  skill-cli check                     lint skills.yaml (for tests/CI)
  skill-cli registry                  regenerate skills.yaml; keep human fields
  skill-cli add NAME                  create agents/skills/NAME + register
  skill-cli add NAME --source URL --pin SHA [--path SUB]
                                  register an external skill (git fetch at sync)
  skill-cli remove NAME               delete folder + registry entry (repo only)
  skill-cli eval NAME [args]          run skills/NAME/evals/run with SKILL_DIR set

Config: ${XDG_CONFIG_HOME:-~/.config}/skill-cli/config.toml
  entrypoint = "/path/to/dotfiles/agents"

Override with --entrypoint or SKILL_CLI_ENTRYPOINT. OS-agnostic (macOS + Linux).
Copies files; never symlinks. Only sync changes local agent dirs (add/update only;
never deletes local skills that are not in the repo).
External skills live in skills.yaml under source.url / source.pin [/ source.path];
fetched into ${XDG_CACHE_HOME:-~/.cache}/skill-cli/ and never vendored into the repo.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys

from skill_cli.console import PROG, CliError, FetchError, log
from skill_cli.fetch import fetch_skill_dir
from skill_cli.paths import Paths, resolve_entrypoint
from skill_cli.registry import find_registry_errors, read_registry, write_registry
from skill_cli.skills import NAME_RE, pin_problem, read_frontmatter, skill_path_for, validate_name
from skill_cli.status import cmd_status
from skill_cli.sync import sync_all

SKILL_TEMPLATE = """\
---
name: {name}
description: TODO: one-line description of when to use this skill.
---

# {name}

Describe what this skill does.
"""


def cmd_check(paths: Paths, _args: argparse.Namespace) -> int:
    errors = find_registry_errors(paths)
    for error in errors:
        print(f"{PROG}: {error}", file=sys.stderr)
    return 1 if errors else 0


def cmd_registry(paths: Paths, args: argparse.Namespace) -> int:
    if not args.check:
        write_registry(paths)
        log(f"wrote {paths.registry}")
    return cmd_check(paths, args)


def cmd_add(paths: Paths, args: argparse.Namespace) -> int:
    registry = read_registry(paths)
    name = validate_name(args.name)

    if args.source:
        if not args.pin:
            raise CliError("--pin is required with --source")
        problem = pin_problem(args.pin)
        if problem:
            raise CliError(f"--pin: {problem}")
        skill_dir = skill_path_for(paths, name)
        if skill_dir.exists():
            raise CliError(
                f"{name} has a local folder at {skill_dir}; "
                "remove it first — external skills are registry-only"
            )
        source = {"url": args.source, "pin": args.pin}
        if args.path:
            source["path"] = args.path
        try:
            content = fetch_skill_dir(name, source)
        except FetchError as exc:
            raise CliError(str(exc)) from exc
        desc = read_frontmatter(content / "SKILL.md").get("description", "")
        entry = registry.get(name, {})
        entry["status"] = entry.get("status") or "experimental"
        entry["purpose"] = entry.get("purpose") or f"External: {args.source}."
        entry["description"] = desc
        entry["source"] = source
        registry[name] = entry
        write_registry(paths, registry)
        log(f"registered external {name} from {args.source}@{args.pin}")
        return 0

    if args.pin or args.path:
        raise CliError("--pin/--path require --source")

    paths.skills_dir.mkdir(parents=True, exist_ok=True)
    skill_dir = skill_path_for(paths, name)
    skill_md = skill_dir / "SKILL.md"
    created = False
    if not skill_md.is_file():
        skill_dir.mkdir(parents=True, exist_ok=True)
        skill_md.write_text(SKILL_TEMPLATE.format(name=name))
        log(f"created {skill_md}")
        created = True
    else:
        log(f"already exists {skill_md}")
    entry = registry.get(name, {})
    entry["status"] = entry.get("status") or "active"
    entry["purpose"] = entry.get("purpose") or ""
    if created:
        entry.pop("source", None)
    registry[name] = entry
    write_registry(paths, registry)
    log(f"registered {name}")
    return 0


def cmd_remove(paths: Paths, args: argparse.Namespace) -> int:
    """Delete the skill folder (if local) and registry entry. Never touches local agent dirs."""
    registry = read_registry(paths)
    name = args.name
    skill_dir = paths.skills_dir / name
    is_local = (
        bool(NAME_RE.match(name))
        and len(name) <= 64
        and skill_dir.is_dir()
        and skill_dir.resolve().parent == paths.skills_dir.resolve()
    )
    if name not in registry and not is_local:
        raise CliError(f"{name!r} is not in the registry and has no folder", code=2)
    if is_local:
        shutil.rmtree(skill_dir)
        log(f"deleted {skill_dir}")
    if name in registry:
        del registry[name]
        write_registry(paths, registry)
        log(f"removed {name} from {paths.registry.name}")
    return 0


def cmd_sync(paths: Paths, args: argparse.Namespace) -> int:
    return sync_all(paths, dry_run=args.dry_run)


def cmd_eval(paths: Paths, args: argparse.Namespace) -> int:
    name = args.name
    skill_dir = paths.skills_dir / name
    evals = skill_dir / "evals"
    runner = evals / "run"
    if not (skill_dir / "SKILL.md").is_file():
        print(f"{PROG}: no skill named {name!r}", file=sys.stderr)
        return 2
    if not os.access(runner, os.X_OK):
        print(f"{PROG}: {runner} is missing or not executable", file=sys.stderr)
        return 2
    env = dict(os.environ, SKILL_DIR=str(skill_dir))
    return subprocess.run([str(runner), *args.rest], cwd=evals, env=env).returncode


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=PROG, description=__doc__.split("\n\n")[0],
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--entrypoint",
        help="path to the repo agents/ folder (overrides config and env)",
    )
    sub = parser.add_subparsers(dest="command")

    sync = sub.add_parser("sync", help="copy agents/skills and agent config to local dirs")
    sync.add_argument("--dry-run", action="store_true")
    sync.set_defaults(handler=cmd_sync)

    status = sub.add_parser("status", help="report usage, drift, orphans")
    status.add_argument("--json", action="store_true")
    status.set_defaults(handler=cmd_status)

    check = sub.add_parser("check", help="lint skills.yaml (write nothing)")
    check.set_defaults(handler=cmd_check)

    reg = sub.add_parser("registry", help="regenerate skills.yaml from SKILL.md files")
    reg.add_argument("--check", action="store_true", help="check only; write nothing")
    reg.set_defaults(handler=cmd_registry)

    add = sub.add_parser("add", help="create a local skill or register an external one")
    add.add_argument("name", help="skill name (lowercase-hyphen)")
    add.add_argument("--source", help="git URL for an external skill")
    add.add_argument("--pin", help="40-char commit SHA")
    add.add_argument("--path", help="subdir inside the repo that contains SKILL.md")
    add.set_defaults(handler=cmd_add)

    rem = sub.add_parser("remove", help="delete skill folder + registry entry (repo only)")
    rem.add_argument("name")
    rem.set_defaults(handler=cmd_remove)

    ev = sub.add_parser("eval", help="run a skill's local evals/run")
    ev.add_argument("name")
    ev.add_argument("rest", nargs=argparse.REMAINDER)
    ev.set_defaults(handler=cmd_eval)

    parser.set_defaults(handler=cmd_status, json=False)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
        paths = Paths.from_entrypoint(resolve_entrypoint(args.entrypoint))
        return args.handler(paths, args)
    except CliError as exc:
        print(f"{PROG}: {exc}", file=sys.stderr)
        return exc.code


if __name__ == "__main__":
    sys.exit(main())
