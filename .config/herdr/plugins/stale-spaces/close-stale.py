#!/usr/bin/env python3
"""Close spaces that have been idle and unchanged for two hours.

A space's clock restarts whenever it is active, focused, was the last focused
one, or its newest state_change_seq moves (a space without agents counts as
seq 0). A fresh startup forgets the clocks so downtime does not count.
"""
import json
import os
import sys
import time
from pathlib import Path
from typing import NamedTuple

sys.path.append(str(Path(__file__).resolve().parent.parent / "agent-recency"))
from recency import STATE_DIR, call, lock_runs, rank_spaces

STALE_AFTER = 2 * 60 * 60
STATE_FILE = Path(STATE_DIR) / "seen.json"


class Clock(NamedTuple):
    seq: int
    since: float


def load_state():
    if os.environ.get("HERDR_PLUGIN_EVENT") == "startup" or not STATE_FILE.exists():
        return None, {}
    state = json.loads(STATE_FILE.read_text())
    return state["focused"], {ws: Clock(*clock) for ws, clock in state["spaces"].items()}


with lock_runs():
    last_focused, clocks = load_state()
    now = time.time()
    rank = rank_spaces()
    workspaces = call("workspace.list")["workspaces"]
    focused = next((w["workspace_id"] for w in workspaces if w["focused"]), None)
    kept = {}
    for ws in (w["workspace_id"] for w in workspaces):
        active, seq = rank.get(ws, (False, 0))
        clock = clocks.get(ws, Clock(seq, now))
        if active or ws in (focused, last_focused) or clock.seq != seq:
            clock = Clock(seq, now)
        if now - clock.since < STALE_AFTER:
            kept[ws] = clock
            continue
        call("workspace.close", {"workspace_id": ws})
        print(f"closed: {ws}")
    tmp = STATE_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps({"focused": focused, "spaces": kept}))
    tmp.replace(STATE_FILE)
