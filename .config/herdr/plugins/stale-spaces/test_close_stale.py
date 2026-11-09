"""close-stale.py against a fake herdr socket and a temporary state directory."""
import json
import os
import socketserver
import subprocess
import tempfile
import threading
import time
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent / "close-stale.py"
HOUR = 60 * 60
IDLE = [("idle", 5)]


class FakeHerdr(socketserver.ThreadingMixIn, socketserver.UnixStreamServer):
    daemon_threads = True

    def __init__(self, path, workspaces, agents):
        super().__init__(path, FakeHandler)
        self.results = {"workspace.list": {"workspaces": workspaces},
                        "agent.list": {"agents": agents}}
        self.closed = []


class FakeHandler(socketserver.StreamRequestHandler):
    def handle(self):
        request = json.loads(self.rfile.readline())
        if request["method"] == "workspace.close":
            self.server.closed.append(request["params"]["workspace_id"])
        result = self.server.results.get(request["method"], {})
        self.wfile.write((json.dumps({"id": request["id"], "result": result}) + "\n").encode())


class CloseStale(unittest.TestCase):
    def setUp(self):
        socket_dir = tempfile.TemporaryDirectory(dir="/tmp")
        state_dir = tempfile.TemporaryDirectory()
        self.addCleanup(socket_dir.cleanup)
        self.addCleanup(state_dir.cleanup)
        self.socket_path = os.path.join(socket_dir.name, "h.sock")
        self.state_dir = Path(state_dir.name)

    def sweep(self, agents, seen, focused="w2", last_focused=None, event="workspace.focused"):
        """Run one sweep over spaces w1 and w2; agents and the seen (seq, hours ago) clock belong to w1."""
        seq, hours = seen
        state = {"focused": last_focused, "spaces": {"w1": [seq, time.time() - hours * HOUR]}}
        (self.state_dir / "seen.json").write_text(json.dumps(state))
        server = FakeHerdr(
            self.socket_path,
            [{"workspace_id": ws, "focused": ws == focused} for ws in ("w1", "w2")],
            [{"workspace_id": "w1", "agent_status": status, "state_change_seq": seq}
             for status, seq in agents],
        )
        threading.Thread(target=server.serve_forever, daemon=True).start()
        env = dict(os.environ, HERDR_SOCKET_PATH=self.socket_path,
                   HERDR_PLUGIN_STATE_DIR=str(self.state_dir), HERDR_PLUGIN_EVENT=event)
        try:
            subprocess.run(["python3", SCRIPT], env=env, check=True, capture_output=True)
        finally:
            server.shutdown()
            server.server_close()
            os.unlink(self.socket_path)
        return server.closed

    def test_sweep(self):
        cases = {
            "idle for 3h": ({"agents": IDLE, "seen": (5, 3)}, ["w1"]),
            "idle for 1h": ({"agents": IDLE, "seen": (5, 1)}, []),
            "seq changed": ({"agents": [("idle", 6)], "seen": (5, 3)}, []),
            "working": ({"agents": [("working", 5)], "seen": (5, 3)}, []),
            "focused": ({"agents": IDLE, "seen": (5, 3), "focused": "w1"}, []),
            "previously focused": ({"agents": IDLE, "seen": (5, 3), "last_focused": "w1"}, []),
            "no agents for 3h": ({"agents": [], "seen": (0, 3)}, ["w1"]),
            "agents just left": ({"agents": [], "seen": (5, 3)}, []),
            "startup forgets downtime": ({"agents": IDLE, "seen": (5, 3), "event": "startup"}, []),
        }
        for name, (fixture, closed) in cases.items():
            with self.subTest(name):
                self.assertEqual(self.sweep(**fixture), closed)


if __name__ == "__main__":
    unittest.main()
