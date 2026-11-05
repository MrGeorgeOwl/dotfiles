"""Exercise skills-cli status, registry, check, eval, add, remove."""

import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "skills-cli"
ENV_VARS = (
    "AGENTS_HOME", "CODEX_HOME", "CLAUDE_HOME", "GROK_HOME", "PI_HOME", "XDG_CONFIG_HOME"
)


def jsonl(path, *records):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(r) + "\n" for r in records))


def claude_skill(call_id, skill, ts):
    return {
        "type": "assistant",
        "timestamp": ts,
        "message": {
            "content": [
                {"type": "tool_use", "id": call_id, "name": "Skill", "input": {"skill": skill}}
            ]
        },
    }


class SkillsCliStatusTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.home = self.root / "home"
        self.home.mkdir()
        self.agents = self.root / "repo/.agents"
        self.script = self.agents / "skills-cli"
        self.agents.mkdir(parents=True)
        shutil.copy2(SCRIPT, self.script)
        self.add_skill("alpha", "Use for alpha.")
        self.add_skill("beta", "Use for beta.")
        self.env = {k: v for k, v in os.environ.items() if k not in ENV_VARS}
        self.env["HOME"] = str(self.home)
        cache = self.root / "uv-cache"
        cache.mkdir()
        self.env["UV_CACHE_DIR"] = str(cache)
        self.env["XDG_CACHE_HOME"] = str(cache)

    def add_skill(self, name, description):
        path = self.agents / "skills" / name / "SKILL.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"---\nname: {name}\ndescription: {description}\n---\nbody\n")
        return path

    def run_cli(self, *args, check=True):
        return subprocess.run(
            ["uv", "run", "--script", str(self.script), *args],
            env=self.env, check=check, capture_output=True, text=True,
        )

    def report(self):
        return json.loads(self.run_cli("status", "--json").stdout)

    def install(self, home, name, text=None):
        path = self.home / home / name / "SKILL.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        source = self.agents / "skills" / name / "SKILL.md"
        path.write_text(text if text is not None else source.read_text())
        return path

    def test_no_logs_or_installs(self):
        rep = self.report()
        self.assertEqual({log["files"] for log in rep["logs"].values()}, {0})
        [alpha, beta] = rep["skills"]
        self.assertEqual(alpha["usage"], "unknown")
        self.assertEqual(set(alpha["copies"].values()), {"missing"})
        self.assertEqual(rep["orphans"], [])
        self.assertIn("no logs", self.run_cli("status").stdout)

    def test_counts_loads_from_each_agent_log_format(self):
        jsonl(
            self.home / ".claude/projects/p/s1.jsonl",
            claude_skill("c1", "alpha", "2026-10-20T10:00:00Z"),
            claude_skill("c1", "alpha", "2026-10-20T10:00:00Z"),
            {
                "type": "user",
                "uuid": "u1",
                "timestamp": "2026-10-21T10:00:00Z",
                "message": {"content": "<command-name>/beta</command-name>"},
            },
        )
        cmd = json.dumps({"cmd": "cat /h/.codex/skills/alpha/SKILL.md"})
        jsonl(
            self.home / ".codex/sessions/2026/s2.jsonl",
            {
                "timestamp": "2026-10-22T10:00:00Z",
                "payload": {"type": "function_call", "call_id": "x1", "arguments": cmd},
            },
        )
        jsonl(
            self.home / ".pi/agent/sessions/s3.jsonl",
            {
                "timestamp": "2026-10-23T10:00:00Z",
                "message": {
                    "role": "assistant",
                    "content": [
                        {
                            "type": "toolCall",
                            "id": "p1",
                            "name": "read",
                            "arguments": {"path": "/h/.agents/skills/alpha/SKILL.md"},
                        }
                    ],
                },
            },
        )
        jsonl(
            self.home / ".omp/agent/sessions/s4.jsonl",
            {
                "timestamp": "2026-10-24T10:00:00Z",
                "message": {
                    "role": "toolResult",
                    "toolCallId": "o1",
                    "content": [{"text": "[Skill file: /h/.agents/skills/alpha/SKILL.md]"}],
                },
            },
        )
        jsonl(
            self.home / ".grok/sessions/g/updates.jsonl",
            {
                "timestamp": "2026-10-25T10:00:00Z",
                "params": {
                    "update": {
                        "sessionUpdate": "tool_call",
                        "toolCallId": "g1",
                        "rawInput": {"path": "/h/.grok/skills/alpha/SKILL.md"},
                    }
                },
            },
        )
        alpha, beta = self.report()["skills"]
        self.assertEqual(
            alpha["loads"], {"claude": 1, "codex": 1, "pi": 1, "omp": 1, "grok": 1}
        )
        self.assertEqual((alpha["last_used"], alpha["usage"]), ("2026-10-25", "active"))
        self.assertEqual(beta["loads"], {"claude": 1})

    def test_skill_unused_for_sixty_days_is_dormant(self):
        jsonl(
            self.home / ".claude/projects/p/s.jsonl",
            claude_skill("old", "beta", "2026-07-01T00:00:00Z"),
            claude_skill("new", "alpha", "2026-10-30T00:00:00Z"),
        )
        alpha, beta = self.report()["skills"]
        self.assertEqual((alpha["usage"], beta["usage"]), ("active", "dormant"))

    def test_copy_drift(self):
        self.install(".claude/skills", "alpha")
        self.install(".codex/skills", "alpha", "edited by hand\n")
        copies = self.report()["skills"][0]["copies"]
        self.assertEqual(
            (copies["claude"], copies["codex"], copies["grok"]), ("ok", "drift", "missing")
        )

    def test_orphans_and_keep_list(self):
        self.install(".grok/skills", "local-only", "x\n")
        (self.home / ".agents/skills/hollow").mkdir(parents=True)
        (self.home / ".codex/skills/.system").mkdir(parents=True)
        keep = self.home / ".config/skills/keep-skills"
        keep.parent.mkdir(parents=True)
        keep.write_text("# mine\nlocal-only\n")
        orphans = {o["name"]: o for o in self.report()["orphans"]}
        self.assertEqual(sorted(orphans), ["hollow", "local-only"])
        self.assertTrue(orphans["local-only"]["kept"])
        self.assertTrue(orphans["hollow"]["hollow"])

    def test_pi_and_omp_orphans_are_not_pruned(self):
        self.install(".claude/skills", "local-only", "x\n")
        self.install(".pi/agent/skills", "pi-only", "x\n")
        self.install(".omp/agent/skills", "omp-only", "x\n")
        orphans = {o["name"]: o["pruned"] for o in self.report()["orphans"]}
        self.assertEqual(orphans, {"local-only": True, "pi-only": False, "omp-only": False})
        self.assertNotIn("moves these", self.run_cli("status").stdout)

    def test_registry_check_catches_staleness(self):
        self.run_cli("registry")
        self.add_skill("beta", "Use for beta, updated.")
        registry = self.agents / "skills.yaml"
        stale = registry.read_text()
        result = self.run_cli("check", check=False)
        self.assertEqual(result.returncode, 1)
        self.assertIn("out of date", result.stderr)
        self.assertEqual(registry.read_text(), stale)

    def test_registry_regenerate_keeps_human_fields(self):
        self.run_cli("registry")
        registry = self.agents / "skills.yaml"
        registry.write_text(
            registry.read_text().replace(
                '"beta"\n  description: "Use for beta."\n  status: "active"\n  purpose: ""',
                '"beta"\n  description: "Use for beta."\n  status: "deprecated"\n  purpose: "old"',
            )
        )
        self.add_skill("beta", "Use for beta, updated.")
        self.run_cli("registry")
        self.assertIn(
            '"beta"\n  description: "Use for beta, updated."\n'
            '  status: "deprecated"\n  purpose: "old"',
            registry.read_text(),
        )
        self.assertEqual(self.run_cli("check").returncode, 0)

    def test_registry_check_rejects_bad_frontmatter(self):
        (self.agents / "skills/alpha/SKILL.md").write_text(
            "---\nname: other\ndescription: x\n---\n"
        )
        (self.agents / "skills/empty").mkdir()
        self.run_cli("registry", check=False)
        result = self.run_cli("check", check=False)
        self.assertEqual(result.returncode, 1)
        for text in ("alpha: frontmatter name 'other'", "empty: no SKILL.md"):
            self.assertIn(text, result.stderr)

    def test_registry_check_rejects_unknown_status(self):
        self.run_cli("registry")
        registry = self.agents / "skills.yaml"
        registry.write_text(registry.read_text().replace('"active"', '"maybe"', 1))
        result = self.run_cli("check", check=False)
        self.assertEqual(result.returncode, 1)
        self.assertIn("alpha: status must be", result.stderr)

    def test_registry_check_rejects_multiline_description(self):
        self.add_skill("alpha", ">-\n  Use for\n  alpha.")
        self.run_cli("registry", check=False)
        result = self.run_cli("check", check=False)
        self.assertEqual(result.returncode, 1)
        self.assertIn("alpha: description must be one line", result.stderr)

    def test_add_and_remove_external_skill(self):
        self.run_cli("registry")
        self.run_cli("add", "owner/repo", "tool#abc")
        registry = (self.agents / "skills.yaml").read_text()
        self.assertIn('source: "owner/repo"', registry)
        self.assertIn('ref: "abc"', registry)
        self.assertIn('name: "tool"', registry)
        self.assertEqual(self.run_cli("check").returncode, 0)
        self.run_cli("remove", "tool")
        self.assertNotIn("tool", (self.agents / "skills.yaml").read_text())

    def test_remove_repo_skill_requires_deleting_folder(self):
        self.run_cli("registry")
        result = self.run_cli("remove", "alpha", check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("still has .agents/skills/alpha/", result.stderr)

    def add_eval_runner(self, name):
        runner = self.agents / f"skills/{name}/evals/run"
        runner.parent.mkdir()
        runner.write_text('#!/bin/sh\necho "evals for $SKILL_DIR in $PWD $1"\nexit 3\n')
        runner.chmod(0o755)
        return runner

    def test_eval_runs_the_skill_eval_script(self):
        runner = self.add_eval_runner("alpha")
        result = self.run_cli("eval", "alpha", "--quick", check=False)
        self.assertEqual(result.returncode, 3)
        self.assertIn(
            f"evals for {runner.parent.parent} in {runner.parent} --quick", result.stdout
        )

    def test_report_flags_skills_with_evals(self):
        self.add_eval_runner("alpha")
        alpha, beta = self.report()["skills"]
        self.assertEqual((alpha["evals"], beta["evals"]), (True, False))

    def test_eval_without_runner_exits_2(self):
        self.assertEqual(self.run_cli("eval", "beta", check=False).returncode, 2)

    def test_repo_registry_is_up_to_date(self):
        result = subprocess.run(
            ["uv", "run", "--script", str(SCRIPT), "check"],
            capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
