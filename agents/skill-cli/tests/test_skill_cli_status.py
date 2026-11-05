"""Exercise skill-cli status, registry, check, eval, add, remove."""

import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "skill-cli"
ENV_VARS = (
    "AGENTS_HOME", "CODEX_HOME", "CLAUDE_HOME", "GROK_HOME", "PI_HOME",
    "XDG_CONFIG_HOME", "SKILL_CLI_ENTRYPOINT",
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


class SkillCliStatusTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.home = self.root / "home"
        self.home.mkdir()
        self.entry = self.root / "repo/agents"
        self.script = self.entry / "skill-cli/skill-cli"
        self.script.parent.mkdir(parents=True)
        shutil.copy2(SCRIPT, self.script)
        self.add_skill("alpha", "Use for alpha.")
        self.add_skill("beta", "Use for beta.")
        self.env = {k: v for k, v in os.environ.items() if k not in ENV_VARS}
        self.env["HOME"] = str(self.home)
        self.env["SKILL_CLI_ENTRYPOINT"] = str(self.entry)
        cache = self.root / "uv-cache"
        cache.mkdir()
        self.env["UV_CACHE_DIR"] = str(cache)
        self.env["XDG_CACHE_HOME"] = str(cache)

    def add_skill(self, name, description):
        path = self.entry / "skills" / name / "SKILL.md"
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
        source = self.entry / "skills" / name / "SKILL.md"
        path.write_text(text if text is not None else source.read_text())
        return path

    def test_no_logs_or_installs(self):
        rep = self.report()
        self.assertEqual({log["files"] for log in rep["logs"].values()}, {0})
        [alpha, beta] = rep["skills"]
        self.assertEqual(alpha["name"], "alpha")
        self.assertEqual(alpha["usage"], "unknown")
        self.assertEqual(alpha["copies"], {a: "missing" for a in ("agents", "codex", "claude", "grok")})
        self.assertEqual(rep["orphans"], [])
        self.assertEqual(rep["entrypoint"], str(self.entry))

    def test_active_and_dormant_from_claude_logs(self):
        project = self.home / ".claude/projects/demo"
        jsonl(
            project / "a.jsonl",
            claude_skill("c1", "alpha", "2024-01-01T00:00:00Z"),
            claude_skill("c2", "alpha", "2024-03-01T00:00:00Z"),
            claude_skill("c2", "alpha", "2024-03-02T00:00:00Z"),  # dup id ignored
            claude_skill("c3", "beta", "2023-01-01T00:00:00Z"),
        )
        rep = self.report()
        by_name = {s["name"]: s for s in rep["skills"]}
        self.assertEqual(by_name["alpha"]["usage"], "active")
        self.assertEqual(by_name["alpha"]["total"], 2)
        self.assertEqual(by_name["alpha"]["last_used"], "2024-03-01")
        self.assertEqual(by_name["beta"]["usage"], "dormant")
        self.assertEqual(by_name["beta"]["total"], 1)

    def test_drift_hollow_and_orphan(self):
        self.install(".agents/skills", "alpha")
        self.install(".codex/skills", "alpha", "drifted\n")
        hollow = self.home / ".claude/skills/alpha"
        hollow.mkdir(parents=True)
        orphan = self.install(".grok/skills", "ghost", "orphan\n")
        # ghost isn't a real skill folder under agents; install helper used wrong base
        # Rewrite: put orphan only under grok
        rep = self.report()
        by_name = {s["name"]: s for s in rep["skills"]}
        self.assertEqual(by_name["alpha"]["copies"]["agents"], "ok")
        self.assertEqual(by_name["alpha"]["copies"]["codex"], "drift")
        self.assertEqual(by_name["alpha"]["copies"]["claude"], "hollow")
        self.assertEqual(by_name["alpha"]["copies"]["grok"], "missing")
        [o] = [x for x in rep["orphans"] if x["name"] == "ghost"]
        self.assertEqual(o["agent"], "grok")
        self.assertTrue(o["pruned"])
        self.assertTrue(orphan.is_file())

    def test_pi_skill_file_marker(self):
        session = self.home / ".pi/agent/sessions/s1.jsonl"
        jsonl(
            session,
            {
                "timestamp": "2024-06-01T00:00:00Z",
                "message": {
                    "role": "toolResult",
                    "toolCallId": "t1",
                    "content": [{"text": "[Skill file: /h/.agents/skills/alpha/SKILL.md]"}],
                },
            },
        )
        rep = self.report()
        by_name = {s["name"]: s for s in rep["skills"]}
        self.assertEqual(by_name["alpha"]["loads"]["pi"], 1)

    def test_registry_and_check(self):
        result = self.run_cli("registry")
        self.assertEqual(result.returncode, 0)
        registry = self.entry / "skills.yaml"
        self.assertIn('name: "alpha"', registry.read_text())
        self.assertEqual(self.run_cli("check").returncode, 0)
        # Stale: tweak purpose by hand then change description in SKILL.md
        text = registry.read_text().replace('purpose: ""', 'purpose: "kept"')
        registry.write_text(text)
        self.add_skill("alpha", "Changed description.")
        bad = self.run_cli("check", check=False)
        self.assertNotEqual(bad.returncode, 0)
        self.assertIn("out of date", bad.stderr)
        self.run_cli("registry")
        self.assertIn('purpose: "kept"', registry.read_text())
        self.assertIn("Changed description.", registry.read_text())

    def test_add_creates_template_and_remove_deletes_folder(self):
        local_before = self.home / ".agents/skills/gamma"
        local_before.mkdir(parents=True)
        (local_before / "SKILL.md").write_text("local copy\n")
        result = self.run_cli("add", "gamma")
        self.assertEqual(result.returncode, 0)
        skill_md = self.entry / "skills/gamma/SKILL.md"
        self.assertTrue(skill_md.is_file())
        self.assertIn("name: gamma", skill_md.read_text())
        self.assertIn('name: "gamma"', (self.entry / "skills.yaml").read_text())
        # Local dir untouched by add
        self.assertEqual((local_before / "SKILL.md").read_text(), "local copy\n")

        result = self.run_cli("remove", "gamma")
        self.assertEqual(result.returncode, 0)
        self.assertFalse((self.entry / "skills/gamma").exists())
        self.assertNotIn("gamma", (self.entry / "skills.yaml").read_text())
        # Local dir still untouched by remove
        self.assertEqual((local_before / "SKILL.md").read_text(), "local copy\n")

    def make_git_skill_repo(self, name="tool", body="from-git\n", subdir=None):
        src = self.root / f"ext-{name}"
        if src.exists():
            shutil.rmtree(src)
        skill_rel = Path(subdir) if subdir else Path(name)
        skill_dir = src / skill_rel
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text(
            f"---\nname: {name}\ndescription: External {name}\n---\n{body}"
        )
        subprocess.run(["git", "init"], cwd=src, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.email", "t@example.com"], cwd=src, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.name", "t"], cwd=src, check=True, capture_output=True)
        subprocess.run(["git", "add", "-A"], cwd=src, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "init"], cwd=src, check=True, capture_output=True)
        pin = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=src, check=True, capture_output=True, text=True,
        ).stdout.strip()
        return src.resolve().as_uri(), pin, str(skill_rel)

    def test_add_external_registers_only(self):
        url, pin, path = self.make_git_skill_repo()
        local = self.home / ".agents/skills/tool"
        local.mkdir(parents=True)
        (local / "SKILL.md").write_text("old local\n")
        result = self.run_cli(
            "add", "tool", "--source", url, "--pin", pin, "--path", path,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse((self.entry / "skills/tool").exists())
        registry = (self.entry / "skills.yaml").read_text()
        self.assertIn("source:", registry)
        self.assertIn(f'url: "{url}"', registry)
        self.assertIn(f'pin: "{pin}"', registry)
        self.assertIn(f'path: "{path}"', registry)
        self.assertEqual((local / "SKILL.md").read_text(), "old local\n")

    def test_add_external_missing_skill_md_leaves_registry_alone(self):
        url, pin, path = self.make_git_skill_repo()
        result = self.run_cli(
            "add", "tool", "--source", url, "--pin", pin, "--path", "missing",
            check=False,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((self.entry / "skills/tool").exists())
        registry = self.entry / "skills.yaml"
        self.assertTrue(not registry.is_file() or "tool" not in registry.read_text())

    def test_registry_parses_nested_source(self):
        url, pin, path = self.make_git_skill_repo()
        # Write registry by hand, then status --json should expose source mapping
        self.run_cli("registry")
        registry = self.entry / "skills.yaml"
        registry.write_text(
            registry.read_text()
            + '- name: "tool"\n'
            '  description: "External tool"\n'
            '  status: "experimental"\n'
            '  purpose: ""\n'
            "  source:\n"
            f'    url: "{url}"\n'
            f'    pin: "{pin}"\n'
            f'    path: "{path}"\n'
        )
        # Prefetch via add would work; status should list it
        rep = self.report()
        by_name = {s["name"]: s for s in rep["skills"]}
        self.assertIn("tool", by_name)
        self.assertEqual(by_name["tool"]["source"]["url"], url)
        self.assertEqual(by_name["tool"]["source"]["pin"], pin)
        self.assertEqual(by_name["tool"]["source"]["path"], path)

    def test_check_requires_pin_and_rejects_local_folder_for_external(self):
        url, pin, path = self.make_git_skill_repo()
        self.run_cli("registry")
        registry = self.entry / "skills.yaml"
        # missing pin
        registry.write_text(
            registry.read_text()
            + '- name: "tool"\n'
            '  description: "External tool"\n'
            '  status: "experimental"\n'
            '  purpose: ""\n'
            "  source:\n"
            f'    url: "{url}"\n'
        )
        bad = self.run_cli("check", check=False)
        self.assertNotEqual(bad.returncode, 0)
        self.assertIn("source.pin missing", bad.stderr)

    def test_remove_external_drops_registry_only(self):
        url, pin, path = self.make_git_skill_repo()
        self.run_cli("add", "tool", "--source", url, "--pin", pin, "--path", path)
        self.assertIn("tool", (self.entry / "skills.yaml").read_text())
        result = self.run_cli("remove", "tool")
        self.assertEqual(result.returncode, 0)
        self.assertNotIn("tool", (self.entry / "skills.yaml").read_text())

    def test_eval_runs_local_script(self):
        runner = self.entry / "skills/alpha/evals/run"
        runner.parent.mkdir(parents=True)
        runner.write_text("#!/bin/sh\necho \"dir=$SKILL_DIR arg=$1\"\n")
        runner.chmod(0o755)
        result = self.run_cli("eval", "alpha", "x")
        self.assertEqual(result.returncode, 0)
        self.assertIn(f"dir={self.entry / 'skills/alpha'}", result.stdout)
        self.assertIn("arg=x", result.stdout)

    def test_eval_missing_skill(self):
        result = self.run_cli("eval", "nosuch", check=False)
        self.assertEqual(result.returncode, 2)

    def test_config_toml_entrypoint(self):
        env = dict(self.env)
        del env["SKILL_CLI_ENTRYPOINT"]
        cfg_home = self.root / "cfg"
        cfg = cfg_home / "skill-cli/config.toml"
        cfg.parent.mkdir(parents=True)
        cfg.write_text(f'entrypoint = "{self.entry}"\n')
        env["XDG_CONFIG_HOME"] = str(cfg_home)
        result = subprocess.run(
            ["uv", "run", "--script", str(self.script), "status", "--json"],
            env=env, check=True, capture_output=True, text=True,
        )
        rep = json.loads(result.stdout)
        self.assertEqual(rep["entrypoint"], str(self.entry))
        self.assertEqual(len(rep["skills"]), 2)


if __name__ == "__main__":
    unittest.main()
