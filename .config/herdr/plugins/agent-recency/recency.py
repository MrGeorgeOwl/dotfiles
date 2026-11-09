"""Shared herdr socket client and workspace ranking for the recency plugins."""
import contextlib
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


def rank_spaces():
    rank = {}  # workspace_id -> (active, newest seq)
    for agent in call("agent.list")["agents"]:
        ws = agent["workspace_id"]
        active, seq = rank.get(ws, (False, 0))
        rank[ws] = (active or agent["agent_status"] in ACTIVE,
                    max(seq, agent.get("state_change_seq", 0)))
    return rank


@contextlib.contextmanager
def lock_runs():
    # Event hooks fire in bursts; serialize runs so a stale read can't win.
    os.makedirs(STATE_DIR, exist_ok=True)
    with open(os.path.join(STATE_DIR, "lock"), "w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        yield
