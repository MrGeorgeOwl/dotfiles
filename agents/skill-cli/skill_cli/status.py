"""Build and print the status report."""

from __future__ import annotations

import datetime
import json
import os
from pathlib import Path

from skill_cli.console import PROG
from skill_cli.fetch import find_cached_skill_dir
from skill_cli.paths import Paths, list_skill_roots
from skill_cli.registry import read_registry
from skill_cli.skills import Source, find_problems, hash_file, list_repo_skills
from skill_cli.sync import resolve_agents
from skill_cli.usage import count_usage_by_agent

DORMANT_DAYS = 60


def list_installed() -> dict[str, dict[str, Path | None]]:
    result: dict[str, dict[str, Path | None]] = {}
    for label, root in list_skill_roots().items():
        entries: dict[str, Path | None] = {}
        if root.is_dir():
            for item in root.iterdir():
                if item.name.startswith(".") or not item.is_dir():
                    continue
                skill = item / "SKILL.md"
                entries[item.name] = skill if skill.is_file() else None
        result[label] = entries
    return result


def build_report(paths: Paths) -> dict:
    registry = read_registry(paths)
    copies = list_installed()
    usage = count_usage_by_agent()
    newest = max((u.last for u in usage.values() if u.last), default=None)
    cutoff = None
    if newest:
        cutoff = (
            datetime.date.fromisoformat(newest) - datetime.timedelta(days=DORMANT_DAYS)
        ).isoformat()

    def summarize_usage(name: str) -> dict:
        loads = {agent: u.loads[name] for agent, u in usage.items() if u.loads[name]}
        last = max((u.last_use[name] for u in usage.values() if name in u.last_use), default=None)
        if not newest:
            state = "unknown"
        elif last and last >= cutoff:
            state = "active"
        else:
            state = "dormant"
        return {"loads": loads, "total": sum(loads.values()), "last_used": last, "usage": state}

    skills: list[dict] = []
    declared: set[str] = set()

    def append_skill(
        name: str, skill_md: Path | None, fields: dict, problems: list[str], evals: bool
    ) -> None:
        declared.add(name)
        repo_hash = hash_file(skill_md) if skill_md and skill_md.is_file() else None
        src = Source.from_fields(fields)
        src_dict = src.as_dict() if src else (
            fields.get("source") if isinstance(fields.get("source"), dict) else None
        )
        where = {}
        for label in resolve_agents(fields):
            entries = copies.get(label, {})
            if name not in entries:
                where[label] = "missing"
            elif entries[name] is None:
                where[label] = "hollow"
            elif repo_hash is None:
                where[label] = "not fetched" if src else "ok"
            else:
                where[label] = "ok" if hash_file(entries[name]) == repo_hash else "drift"
        skills.append({
            "name": name,
            "status": fields.get("status", "unregistered"),
            "source": src_dict,
            "problems": problems,
            "hash": repo_hash,
            "copies": where,
            "evals": evals,
            **summarize_usage(name),
        })

    for skill in list_repo_skills(paths):
        fields = registry.get(skill.name, {})
        path = skill / "SKILL.md"
        append_skill(
            skill.name,
            path if path.is_file() else None,
            fields,
            find_problems(skill),
            (skill / "evals").is_dir(),
        )

    for name, fields in sorted(registry.items()):
        if name in declared:
            continue
        src = Source.from_fields(fields)
        raw = fields.get("source")
        if not isinstance(raw, dict):
            continue
        cached = find_cached_skill_dir(name, raw)
        problems: list[str] = []
        if src is None:
            problems.append("source.url missing")
        else:
            problems += src.find_problems()
        append_skill(
            name,
            (cached / "SKILL.md") if cached else None,
            fields,
            problems,
            False,
        )

    orphans = []
    for label, entries in copies.items():
        for name, path in sorted(entries.items()):
            if name in declared:
                continue
            orphans.append({
                "name": name,
                "root": str(list_skill_roots()[label]),
                "agent": label,
                "hollow": path is None,
                **summarize_usage(name),
            })

    logs = {
        agent: {"files": u.files, "first": u.first, "last": u.last}
        for agent, u in usage.items()
    }
    return {
        "host": os.uname().nodename,
        "entrypoint": str(paths.agents_dir),
        "logs": logs,
        "dormant_after_days": DORMANT_DAYS,
        "skills": skills,
        "orphans": orphans,
    }


def print_report(rep: dict) -> None:
    print(f"{PROG} on {rep['host']}: {len(rep['skills'])} skills in {rep['entrypoint']}")
    print("logs:")
    for agent, loginfo in rep["logs"].items():
        window = f"{loginfo['first']} .. {loginfo['last']}" if loginfo["files"] else "no logs"
        print(f"  {agent:7} {loginfo['files']:>4} files  {window}")
    print(
        f"\n{'skill':24} {'registry':12} {'usage':8} {'loads':>5}  "
        f"{'last used':10}  copies / notes"
    )
    for s in rep["skills"]:
        bad = [f"{agent} {state}" for agent, state in s["copies"].items() if state != "ok"]
        notes = bad or ["all copies ok"]
        notes += s["problems"] + (["evals"] if s["evals"] else [])
        src = s.get("source")
        if isinstance(src, dict) and src.get("url"):
            note = f"external:{src['url']}@{src.get('pin', '')}"
            if src.get("path"):
                note += f" path={src['path']}"
            notes.append(note)
        print(
            f"{s['name']:24} {s['status']:12} {s['usage']:8} {s['total']:>5}  "
            f"{s['last_used'] or '-':10}  {', '.join(notes)}"
        )
    if rep["orphans"]:
        print("\ninstalled but not in the registry (left alone by sync):")
        for o in rep["orphans"]:
            tags = [o["agent"]] + (["no SKILL.md"] if o["hollow"] else [])
            print(
                f"  {o['name']:22} {o['usage']:8} {o['total']:>5}  "
                f"{o['last_used'] or '-':10}  {', '.join(tags)}"
            )
    print(
        f"\nusage: active = loaded within {DORMANT_DAYS} days of the newest log day; "
        "dormant = not; unknown = no logs.\n"
        "Zero loads only means zero inside the log window above."
    )


def cmd_status(paths: Paths, args) -> int:
    rep = build_report(paths)
    if args.json:
        print(json.dumps(rep, indent=1))
    else:
        print_report(rep)
    return 0
