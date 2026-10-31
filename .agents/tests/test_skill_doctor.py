"""Exercise skill-doctor against a fake repo and a fake home directory."""

import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "skill-doctor"
ENV_VARS = ("AGENTS_HOME", "CODEX_HOME", "CLAUDE_HOME", "GROK_HOME", "PI_HOME", "XDG_CONFIG_HOME")


def jsonl(path, *records):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(r) + "\n" for r in records))


def claude_skill(call_id, skill, ts):
    return {"type": "assistant", "timestamp": ts, "message": {"content": [
        {"type": "tool_use", "id": call_id, "name": "Skill", "input": {"skill": skill}}]}}


class SkillDoctorTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.home = self.root / "home"
        self.home.mkdir()
        self.agents = self.root / "repo/.agents"
        self.script = self.agents / "skill-doctor"
        self.agents.mkdir(parents=True)
        shutil.copy2(SCRIPT, self.script)
        self.add_skill("alpha", "Use for alpha.")
        self.add_skill("beta", "Use for beta.")
        self.env = {k: v for k, v in os.environ.items() if k not in ENV_VARS}
        self.env["HOME"] = str(self.home)

    def add_skill(self, name, description):
        path = self.agents / "skills" / name / "SKILL.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"---\nname: {name}\ndescription: {description}\n---\nbody\n")
        return path

    def run_doctor(self, *args, check=True):
        return subprocess.run(["python3", str(self.script), *args], env=self.env,
                              check=check, capture_output=True, text=True)

    def report(self):
        return json.loads(self.run_doctor("--json").stdout)

    def install(self, home, name, text=None):
        path = self.home / home / name / "SKILL.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        source = self.agents / "skills" / name / "SKILL.md"
        path.write_text(text if text is not None else source.read_text())
        return path

    def test_missing_logs_and_installs_are_reported_not_fatal(self):
        rep = self.report()
        self.assertEqual({log["files"] for log in rep["logs"].values()}, {0})
        [alpha, beta] = rep["skills"]
        self.assertEqual(alpha["usage"], "unknown")
        self.assertEqual(set(alpha["copies"].values()), {"missing"})
        self.assertEqual(rep["orphans"], [])
        self.assertIn("no logs", self.run_doctor().stdout)

    def test_counts_loads_from_each_agent_log_format(self):
        jsonl(self.home / ".claude/projects/p/s1.jsonl",
              claude_skill("c1", "alpha", "2026-10-20T10:00:00Z"),
              claude_skill("c1", "alpha", "2026-10-20T10:00:00Z"),  # same call twice
              {"type": "user", "uuid": "u1", "timestamp": "2026-10-21T10:00:00Z",
               "message": {"content": "<command-name>/beta</command-name>"}})
        cmd = json.dumps({"cmd": "cat /h/.codex/skills/alpha/SKILL.md"})
        jsonl(self.home / ".codex/sessions/2026/s2.jsonl",
              {"timestamp": "2026-10-22T10:00:00Z",
               "payload": {"type": "function_call", "call_id": "x1", "arguments": cmd}})
        jsonl(self.home / ".pi/agent/sessions/s3.jsonl",
              {"timestamp": "2026-10-23T10:00:00Z", "message": {"role": "assistant", "content": [
                  {"type": "toolCall", "id": "p1", "name": "read",
                   "arguments": {"path": "/h/.agents/skills/alpha/SKILL.md"}}]}})
        jsonl(self.home / ".omp/agent/sessions/s4.jsonl",
              {"timestamp": "2026-10-24T10:00:00Z", "message": {
                  "role": "toolResult", "toolCallId": "o1",
                  "content": [{"text": "[Skill file: /h/.agents/skills/alpha/SKILL.md]"}]}})
        jsonl(self.home / ".grok/sessions/g/updates.jsonl",
              {"timestamp": "2026-10-25T10:00:00Z", "params": {"update": {
                  "sessionUpdate": "tool_call", "toolCallId": "g1",
                  "rawInput": {"path": "/h/.grok/skills/alpha/SKILL.md"}}}})
        alpha, beta = self.report()["skills"]
        self.assertEqual(alpha["loads"], {"claude": 1, "codex": 1, "pi": 1, "omp": 1, "grok": 1})
        self.assertEqual((alpha["last_used"], alpha["usage"]), ("2026-10-25", "active"))
        self.assertEqual(beta["loads"], {"claude": 1})

    def test_skill_unused_for_sixty_days_is_dormant(self):
        jsonl(self.home / ".claude/projects/p/s.jsonl",
              claude_skill("old", "beta", "2026-07-01T00:00:00Z"),
              claude_skill("new", "alpha", "2026-10-30T00:00:00Z"))
        alpha, beta = self.report()["skills"]
        self.assertEqual((alpha["usage"], beta["usage"]), ("active", "dormant"))

    def test_drift_orphans_and_keep_list(self):
        self.install(".claude/skills", "alpha")
        self.install(".codex/skills", "alpha", "edited by hand\n")
        self.install(".grok/skills", "local-only", "x\n")
        (self.home / ".agents/skills/hollow").mkdir(parents=True)
        (self.home / ".codex/skills/.system").mkdir(parents=True)
        keep = self.home / ".config/agent-sync/keep-skills"
        keep.parent.mkdir(parents=True)
        keep.write_text("# mine\nlocal-only\n")
        rep = self.report()
        copies = rep["skills"][0]["copies"]
        self.assertEqual((copies["claude"], copies["codex"], copies["grok"]), ("ok", "drift", "missing"))
        orphans = {o["name"]: o for o in rep["orphans"]}
        self.assertEqual(sorted(orphans), ["hollow", "local-only"])
        self.assertTrue(orphans["local-only"]["kept"])
        self.assertTrue(orphans["hollow"]["hollow"])

    def test_registry_keeps_human_fields_and_check_catches_staleness(self):
        self.run_doctor("registry")
        registry = self.agents / "skills.yaml"
        registry.write_text(registry.read_text().replace(
            '"beta"\n  description: "Use for beta."\n  status: "active"\n  purpose: ""',
            '"beta"\n  description: "Use for beta."\n  status: "deprecated"\n  purpose: "old"'))
        self.add_skill("beta", "Use for beta, updated.")
        stale = registry.read_text()
        result = self.run_doctor("registry", "--check", check=False)
        self.assertEqual(result.returncode, 1)
        self.assertIn("out of date", result.stderr)
        self.assertEqual(registry.read_text(), stale)
        self.run_doctor("registry")
        self.assertIn('"beta"\n  description: "Use for beta, updated."\n'
                      '  status: "deprecated"\n  purpose: "old"', registry.read_text())
        self.assertEqual(self.run_doctor("registry", "--check").returncode, 0)

    def test_registry_check_rejects_bad_frontmatter_and_status(self):
        (self.agents / "skills/alpha/SKILL.md").write_text("---\nname: other\ndescription: x\n---\n")
        (self.agents / "skills/empty").mkdir()
        self.run_doctor("registry", check=False)
        registry = self.agents / "skills.yaml"
        registry.write_text(registry.read_text().replace('"active"', '"maybe"', 1))
        result = self.run_doctor("registry", "--check", check=False)
        self.assertEqual(result.returncode, 1)
        for text in ("alpha: frontmatter name 'other'", "empty: no SKILL.md", "alpha: status must be"):
            self.assertIn(text, result.stderr)

    def test_eval_runs_the_skill_eval_script(self):
        runner = self.agents / "skills/alpha/evals/run"
        runner.parent.mkdir()
        runner.write_text('#!/bin/sh\necho "evals for $SKILL_DIR in $PWD $1"\nexit 3\n')
        runner.chmod(0o755)
        result = self.run_doctor("eval", "alpha", "--quick", check=False)
        self.assertEqual(result.returncode, 3)
        self.assertIn(f"evals for {runner.parent.parent} in {runner.parent} --quick", result.stdout)
        self.assertTrue(self.report()["skills"][0]["evals"])
        self.assertEqual(self.run_doctor("eval", "beta", check=False).returncode, 2)

    def test_repo_registry_is_up_to_date(self):
        result = subprocess.run(["python3", str(SCRIPT), "registry", "--check"],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
