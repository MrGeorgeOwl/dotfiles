"""Git fetch into XDG cache for external skills."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
from pathlib import Path

from skill_cli.console import FetchError, log
from skill_cli.paths import resolve_xdg_cache
from skill_cli.skills import pin_problem


def parse_git_url(url: str) -> tuple[str, str]:
    """Return (host, owner/repo) for cache layout. Raises FetchError if unrecognized."""
    raw = url.strip().rstrip("/")
    if raw.endswith(".git"):
        raw = raw[:-4]
    if raw.startswith("git@"):
        _, rest = raw.split("@", 1)
        host, _, path = rest.partition(":")
        if not host or not path:
            raise FetchError(f"unrecognized git url: {url}")
        return host, path
    if raw.startswith("file:"):
        path = raw[5:]
        if path.startswith("//"):
            path = path[2:]
        return "file", path.lstrip("/") or "repo"
    match = re.match(r"^(?:https?|ssh)://(?:[^@/]+@)?([^/]+)/(.+)$", raw)
    if match:
        return match.group(1), match.group(2)
    raise FetchError(f"unrecognized git url: {url}")


def resolve_cache_dir(url: str, pin: str) -> Path:
    host, repo = parse_git_url(url)
    parts = Path(repo)
    return resolve_xdg_cache() / "skill-cli" / host / parts.parent / f"{parts.name}@{pin}"


def ensure_fetched(url: str, pin: str) -> Path:
    """Fetch url at pin into the XDG cache. Reuses cache when pin matches."""
    if shutil.which("git") is None:
        raise FetchError("git not found; required for external skills")
    dest = resolve_cache_dir(url, pin)
    marker = dest / ".skill-cli-pin"
    if marker.is_file() and marker.read_text().strip() == pin:
        return dest

    env = {**os.environ, "GIT_TERMINAL_PROMPT": "0", "GIT_CONFIG_NOSYSTEM": "1"}
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True, exist_ok=True)

    log(f"fetching {url}@{pin}")

    def run(cmd: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess:
        return subprocess.run(cmd, cwd=cwd, env=env, capture_output=True, text=True, check=False)

    init = run(["git", "init"], dest)
    if init.returncode != 0:
        raise FetchError(f"git init failed in {dest}: {init.stderr.strip()}")
    run(["git", "remote", "add", "origin", url], dest)
    fetched = run(["git", "fetch", "--depth", "1", "origin", pin], dest)
    if fetched.returncode != 0:
        shutil.rmtree(dest)
        clone = run(["git", "clone", url, str(dest)])
        if clone.returncode != 0:
            raise FetchError(
                f"could not fetch {url}@{pin}: "
                f"{fetched.stderr.strip() or clone.stderr.strip()}"
            )
        checked = run(["git", "checkout", "--detach", pin], dest)
        if checked.returncode != 0:
            raise FetchError(f"could not checkout {pin} in {url}: {checked.stderr.strip()}")
    else:
        checked = run(["git", "checkout", "--detach", "FETCH_HEAD"], dest)
        if checked.returncode != 0:
            raise FetchError(
                f"could not checkout FETCH_HEAD for {url}@{pin}: {checked.stderr.strip()}"
            )

    marker.write_text(pin + "\n")
    return dest


def resolve_skill_subdir(root: Path, name: str, subpath: str) -> Path | None:
    candidates: list[Path] = []
    if subpath:
        candidates.append(root / subpath)
    else:
        candidates.append(root / name)
        candidates.append(root)
    for candidate in candidates:
        if (candidate / "SKILL.md").is_file():
            return candidate
    return None


def find_cached_skill_dir(name: str, source: dict) -> Path | None:
    """Return cached skill dir if already fetched; else None (no network)."""
    url = source.get("url") or ""
    pin = source.get("pin") or ""
    if not url or not pin:
        return None
    try:
        dest = resolve_cache_dir(url, pin)
    except FetchError:
        return None
    marker = dest / ".skill-cli-pin"
    if not marker.is_file() or marker.read_text().strip() != pin:
        return None
    return resolve_skill_subdir(dest, name, source.get("path") or "")


def fetch_skill_dir(name: str, source: dict) -> Path:
    """Fetch and resolve the directory that contains SKILL.md for an external skill."""
    if not source.get("url"):
        raise FetchError(f"{name}: source.url missing")
    problem = pin_problem(source.get("pin"))
    if problem:
        raise FetchError(f"{name}: {problem}")
    root = ensure_fetched(source["url"], source["pin"])
    found = resolve_skill_subdir(root, name, source.get("path") or "")
    if found is None:
        where = f" path={source.get('path')}" if source.get("path") else ""
        raise FetchError(f"{name}: no SKILL.md under {root}{where}")
    return found
