"""Parse agent session logs for skill loads."""

from __future__ import annotations

import collections
import datetime
import glob
import json
import re
from pathlib import Path

from skill_cli.paths import AGENTS, agent_home

SKILL_PATH = re.compile(r"/([A-Za-z0-9._:~-]+)/SKILL\.md")


def parse_day(ts) -> str | None:
    if isinstance(ts, (int, float)):
        try:
            return datetime.datetime.fromtimestamp(
                ts / (1000 if ts > 1e12 else 1)
            ).strftime("%Y-%m-%d")
        except (OverflowError, OSError, ValueError):
            return None
    text = str(ts or "")[:10]
    return text if re.match(r"\d{4}-\d\d-\d\d$", text) else None


class Usage:
    def __init__(self) -> None:
        self.files = 0
        self.first: str | None = None
        self.last: str | None = None
        self.loads: collections.Counter = collections.Counter()
        self.last_use: dict[str, str] = {}
        self.seen: set = set()

    def record_day(self, ts) -> None:
        t = parse_day(ts)
        if t:
            self.first = min(self.first or t, t)
            self.last = max(self.last or t, t)

    def add(self, skill, ts, key) -> None:
        if not skill or key is None or key in self.seen:
            return
        self.seen.add(key)
        skill = skill.split(":")[-1]
        self.loads[skill] += 1
        t = parse_day(ts)
        if t:
            self.last_use[skill] = max(self.last_use.get(skill, t), t)


def read_records(pattern: Path):
    for name in glob.glob(str(pattern), recursive=True):
        try:
            with open(name, errors="replace") as fh:
                for line in fh:
                    try:
                        yield name, line, json.loads(line)
                    except ValueError:
                        yield name, line, None
        except OSError:
            continue


def extract_text(content) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return " ".join(x.get("text", "") for x in content if isinstance(x, dict))
    return ""


def parse_skill_path(path) -> str | None:
    match = SKILL_PATH.search(str(path))
    return match.group(1) if match else None


def scan(usage: Usage, pattern: Path, handle) -> None:
    files: set[str] = set()
    for name, line, record in read_records(pattern):
        files.add(name)
        if isinstance(record, dict):
            handle(usage, name, line, record)
    usage.files += len(files)


def parse_claude_record(u, name, line, r) -> None:
    ts = r.get("timestamp")
    u.record_day(ts)
    content = (r.get("message") or {}).get("content")
    if r.get("type") == "assistant" and isinstance(content, list):
        for block in content:
            if not isinstance(block, dict) or block.get("type") != "tool_use":
                continue
            args = block.get("input") or {}
            if block.get("name") == "Skill":
                u.add(args.get("skill"), ts, block.get("id"))
            elif block.get("name") == "Read":
                u.add(parse_skill_path(args.get("file_path", "")), ts, block.get("id"))
    elif r.get("type") == "user":
        match = re.search(
            r"<command-name>/?([A-Za-z0-9:_-]+)</command-name>", extract_text(content)
        )
        if match:
            u.add(match.group(1), ts, r.get("uuid"))


def parse_codex_record(u, name, line, r) -> None:
    ts = r.get("timestamp")
    u.record_day(ts)
    payload = r.get("payload") or {}
    if payload.get("type") != "function_call" or "SKILL.md" not in line:
        return
    try:
        args = json.loads(payload.get("arguments") or "{}")
        cmd = args.get("cmd") or args.get("command") or ""
    except (ValueError, AttributeError):
        cmd = payload.get("arguments") or ""
    if isinstance(cmd, list):
        cmd = " ".join(map(str, cmd))
    if re.search(r"\b(cat|sed|head|nl|bat|less|tail)\b", cmd) and "find " not in cmd:
        for match in SKILL_PATH.finditer(cmd):
            u.add(match.group(1), ts, (payload.get("call_id"), match.group(1)))


def parse_pi_record(u, name, line, r) -> None:
    ts = r.get("timestamp")
    u.record_day(ts)
    msg = r.get("message") or {}
    content = msg.get("content")
    if msg.get("role") == "assistant" and isinstance(content, list):
        for block in content:
            if isinstance(block, dict) and block.get("type") == "toolCall" and block.get("name") == "read":
                path = str((block.get("arguments") or {}).get("path", ""))
                if path.endswith("SKILL.md"):
                    u.add(parse_skill_path(path), ts, block.get("id"))
    elif msg.get("role") == "toolResult":
        match = re.search(
            r"\[Skill file: [^\]]*?/([^/\]]+)/SKILL\.md\]", json.dumps(content)
        )
        if match:
            u.add(match.group(1), ts, msg.get("toolCallId"))
    elif msg.get("role") == "user":
        match = re.match(r"\s*/skill:([A-Za-z0-9._-]+)", extract_text(content))
        if match:
            u.add(match.group(1), ts, (name, ts))


def parse_grok_record(u, name, line, r) -> None:
    ts = r.get("timestamp")
    u.record_day(ts)
    update = (r.get("params") or {}).get("update") or {}
    if update.get("sessionUpdate") == "tool_call":
        raw = json.dumps(update.get("rawInput") or update.get("title") or "")
        u.add(parse_skill_path(raw), ts, update.get("toolCallId"))


PARSERS = {
    "claude": parse_claude_record,
    "codex": parse_codex_record,
    "pi": parse_pi_record,
    "grok": parse_grok_record,
}


def count_usage_by_agent() -> dict[str, Usage]:
    # Preserve historical report key order (status --json).
    order = ("claude", "codex", "pi", "omp", "grok")
    by_name = {a.name: a for a in AGENTS}
    result: dict[str, Usage] = {}
    for name in order:
        agent = by_name[name]
        handle = PARSERS[agent.parse]
        usage = Usage()
        home = agent_home(agent)
        for pattern in agent.session_globs:
            scan(usage, home / pattern, handle)
        result[name] = usage
    return result
