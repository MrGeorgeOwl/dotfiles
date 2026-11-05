"""Skill names, frontmatter, and Source validation."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from pathlib import Path

from skill_cli.console import CliError, FetchError
from skill_cli.paths import Paths

NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
SHA_RE = re.compile(r"^[0-9a-f]{40}$")


@dataclass(frozen=True)
class Source:
    url: str
    pin: str
    path: str = ""

    @classmethod
    def from_fields(cls, fields: dict) -> Source | None:
        """Return Source for an external skill, or None for local."""
        src = fields.get("source")
        if isinstance(src, dict) and src.get("url"):
            return cls(
                url=str(src["url"]),
                pin=str(src.get("pin") or ""),
                path=str(src.get("path") or ""),
            )
        return None

    def as_dict(self) -> dict:
        data = {"url": self.url, "pin": self.pin}
        if self.path:
            data["path"] = self.path
        return data

    def find_problems(self) -> list[str]:
        from skill_cli.fetch import parse_git_url  # late: fetch imports skills.pin_problem

        problems: list[str] = []
        if not self.url:
            problems.append("source.url missing")
        else:
            try:
                parse_git_url(self.url)
            except FetchError as exc:
                problems.append(str(exc))
        problem = pin_problem(self.pin)
        if problem:
            problems.append(problem)
        return problems


def validate_name(name: str) -> str:
    if not NAME_RE.match(name) or len(name) > 64:
        raise CliError(f"skill name must be lowercase-hyphen, <= 64 chars: {name!r}")
    return name


def skill_path_for(paths: Paths, name: str) -> Path:
    """Return skills_dir/name. Caller must validate_name first."""
    return paths.skills_dir / name


def pin_problem(pin: object) -> str | None:
    if not pin:
        return "source.pin missing"
    if not SHA_RE.match(str(pin)):
        return "source.pin must be a 40-char commit SHA"
    return None


def read_frontmatter(path: Path) -> dict[str, str]:
    text = path.read_text(errors="replace")
    match = re.match(r"---\r?\n(.*?)\r?\n---", text, re.S)
    fields: dict[str, str] = {}
    for line in (match.group(1).splitlines() if match else []):
        key, sep, value = line.partition(":")
        if sep and key.strip() in ("name", "description"):
            value = value.strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
                value = value[1:-1]
            fields[key.strip()] = value
    return fields


def hash_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:8]


def list_repo_skills(paths: Paths) -> list[Path]:
    if not paths.skills_dir.is_dir():
        return []
    return sorted(
        p for p in paths.skills_dir.iterdir() if p.is_dir() and not p.name.startswith(".")
    )


def find_problems(skill_dir: Path) -> list[str]:
    path = skill_dir / "SKILL.md"
    if not path.is_file():
        return ["no SKILL.md"]
    meta, found = read_frontmatter(path), []
    name, desc = meta.get("name", ""), meta.get("description", "")
    if name != skill_dir.name:
        found.append(f"frontmatter name {name!r} != folder name")
    if not NAME_RE.match(skill_dir.name) or len(skill_dir.name) > 64:
        found.append("folder name must be lowercase-hyphen, <= 64 chars")
    if not desc or len(desc) > 1024:
        found.append("description missing or > 1024 chars")
    elif desc[0] in ">|":
        found.append("description must be one line")
    return found
