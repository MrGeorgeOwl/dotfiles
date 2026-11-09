#!/usr/bin/env python3
"""Close spaces whose agents have been idle and unchanged for two hours.

A space's clock restarts whenever it is active, focused, was the last focused
one, or its newest state_change_seq moves. Spaces without agents are never
closed, and a fresh startup forgets the clocks so downtime does not count.
"""
import json
import os
import sys
import time

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "agent-recency"))
from recency import STATE_DIR, call, lock_runs, rank_spaces

STALE_AFTER = 2 * 60 * 60
STATE_FILE = os.path.join(STATE_DIR, "seen.json")


def load_state():
    if os.environ.get("HERDR_PLUGIN_EVENT") == "startup" or not os.path.exists(STATE_FILE):
        return {"focused": None, "spaces": {}}
    with open(STATE_FILE) as file:
        return json.load(file)


with lock_runs():
    state = load_state()
    now = time.time()
    rank = rank_spaces()
    workspaces = call("workspace.list")["workspaces"]
    focused = next((w["workspace_id"] for w in workspaces if w["focused"]), None)
    spaces = {}
    for ws in (w["workspace_id"] for w in workspaces if w["workspace_id"] in rank):
        active, seq = rank[ws]
        entry = state["spaces"].get(ws)
        if active or ws in (focused, state["focused"]) or entry is None or entry[0] != seq:
            spaces[ws] = [seq, now]
        elif now - entry[1] >= STALE_AFTER:
            call("workspace.close", {"workspace_id": ws})
            print(f"closed: {ws}")
        else:
            spaces[ws] = entry
    with open(STATE_FILE + ".tmp", "w") as file:
        json.dump({"focused": focused, "spaces": spaces}, file)
    os.replace(STATE_FILE + ".tmp", STATE_FILE)
