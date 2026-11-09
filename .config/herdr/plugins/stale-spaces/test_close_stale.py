"""close-stale.py against a fake herdr socket and a temporary state directory."""
import json
import os
import socketserver
import subprocess
import tempfile
import threading
import time
import unittest

SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "close-stale.py")
HOUR = 60 * 60


class FakeHerdr(socketserver.ThreadingMixIn, socketserver.UnixStreamServer):
    daemon_threads = True

    def __init__(self, path, workspaces, agents):
        super().__init__(path, FakeHandler)
        self.workspaces = workspaces
        self.agents = agents
        self.closed = []


class FakeHandler(socketserver.StreamRequestHandler):
    def handle(self):
        request = json.loads(self.rfile.readline())
        method, params = request["method"], request["params"]
        if method == "workspace.list":
            result = {"workspaces": self.server.workspaces}
        elif method == "agent.list":
            result = {"agents": self.server.agents}
        else:
            self.server.closed.append(params["workspace_id"])
            result = {}
        self.wfile.write((json.dumps({"id": request["id"], "result": result}) + "\n").encode())


class CloseStale(unittest.TestCase):
    def setUp(self):
        self.socket_dir = tempfile.TemporaryDirectory(dir="/tmp")
        self.state_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.socket_dir.cleanup)
        self.addCleanup(self.state_dir.cleanup)
        self.socket_path = os.path.join(self.socket_dir.name, "h.sock")

    def sweep(self, workspaces, agents, seen, event="workspace.focused"):
        now = time.time()
        state = {"focused": seen.get("focused"),
                 "spaces": {ws: [seq, now - age * HOUR] for ws, (seq, age) in seen["spaces"].items()}}
        with open(os.path.join(self.state_dir.name, "seen.json"), "w") as file:
            json.dump(state, file)
        server = FakeHerdr(self.socket_path, [
            {"workspace_id": ws, "focused": focused} for ws, focused in workspaces
        ], [{"workspace_id": ws, "agent_status": status, "state_change_seq": seq}
            for ws, status, seq in agents])
        threading.Thread(target=server.serve_forever, daemon=True).start()
        env = dict(os.environ, HERDR_SOCKET_PATH=self.socket_path,
                   HERDR_PLUGIN_STATE_DIR=self.state_dir.name, HERDR_PLUGIN_EVENT=event)
        try:
            subprocess.run(["python3", SCRIPT], env=env, check=True, capture_output=True)
        finally:
            server.shutdown()
            server.server_close()
            os.unlink(self.socket_path)
        return server.closed

    def test_sweep(self):
        cases = {
            "idle for 3h": ([("w1", False), ("w2", True)], [("w1", "idle", 5)], {"w1": (5, 3)}, {}, ["w1"]),
            "idle for 1h": ([("w1", False), ("w2", True)], [("w1", "idle", 5)], {"w1": (5, 1)}, {}, []),
            "seq changed": ([("w1", False), ("w2", True)], [("w1", "idle", 6)], {"w1": (5, 3)}, {}, []),
            "working": ([("w1", False), ("w2", True)], [("w1", "working", 5)], {"w1": (5, 3)}, {}, []),
            "focused": ([("w1", True)], [("w1", "idle", 5)], {"w1": (5, 3)}, {}, []),
            "previously focused": ([("w1", False), ("w2", True)], [("w1", "idle", 5)], {"w1": (5, 3)}, {"focused": "w1"}, []),
            "no agents": ([("w1", False), ("w2", True)], [], {"w1": (5, 3)}, {}, []),
        }
        for name, (workspaces, agents, spaces, extra, closed) in cases.items():
            with self.subTest(name):
                self.assertEqual(self.sweep(workspaces, agents, dict(extra, spaces=spaces)), closed)

    def test_startup_forgets_downtime(self):
        closed = self.sweep([("w1", False), ("w2", True)], [("w1", "idle", 5)],
                            {"spaces": {"w1": (5, 3)}}, event="startup")
        self.assertEqual(closed, [])


if __name__ == "__main__":
    unittest.main()
