#!/usr/bin/env python3
"""Order spaces by agent activity and sort the Agents sidebar to match.

Spaces: active (working/blocked) agents first, then other spaces with agents,
both by newest state_change_seq; spaces without agents keep their order last.
"""
import fcntl
import json
import os
import socket
import tempfile

PLUGIN_ID = os.environ.get("HERDR_PLUGIN_ID", "agent-recency")
SOCKET = os.environ.get("HERDR_SOCKET_PATH") or os.path.expanduser("~/.config/herdr/herdr.sock")
STATE_DIR = os.environ.get("HERDR_PLUGIN_STATE_DIR") or tempfile.gettempdir()
ACTIVE = {"working", "blocked"}


def call(method, params=None):
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
        sock.connect(SOCKET)
        req = {"id": PLUGIN_ID, "method": method, "params": params or {}}
        sock.sendall((json.dumps(req) + "\n").encode())
        reply = json.loads(sock.makefile().readline())
    if "error" in reply:
        raise SystemExit(f"{method}: {reply['error']}")
    return reply["result"]


def space_order():
    current = [w["workspace_id"] for w in call("workspace.list")["workspaces"]]
    rank = {}  # workspace_id -> (active, newest seq)
    for agent in call("agent.list")["agents"]:
        ws = agent["workspace_id"]
        active, seq = rank.get(ws, (False, 0))
        rank[ws] = (active or agent["agent_status"] in ACTIVE,
                    max(seq, agent.get("state_change_seq", 0)))
    with_agents = sorted((ws for ws in current if ws in rank),
                         key=lambda ws: rank[ws], reverse=True)
    return current, with_agents + [ws for ws in current if ws not in rank]


# Event hooks fire in bursts; serialize runs so a stale read can't win.
os.makedirs(STATE_DIR, exist_ok=True)
with open(os.path.join(STATE_DIR, "lock"), "w") as lock:
    fcntl.flock(lock, fcntl.LOCK_EX)
    current, wanted = space_order()
    if wanted != current:
        call("workspace.move_block", {"workspace_ids": wanted})
        print("spaces:", " ".join(wanted))
    if os.environ.get("HERDR_PLUGIN_EVENT") != "pane.agent_status_changed":
        call("agent.view.set", {
            "source": f"plugin:{PLUGIN_ID}",
            "label": "recency",
            "sort": [
                {"field": "workspace_order", "order": "asc"},
                {"field": "attention", "order": "desc"},
                {"field": "state_change_seq", "order": "desc"},
            ],
        })
