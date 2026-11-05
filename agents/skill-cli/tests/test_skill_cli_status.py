"""Exercise skill-cli status, registry, check, eval, add, remove."""

import json
from pathlib import Path
import subprocess
import unittest

from helpers import SkillCliFixture, make_git_skill_repo


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


class SkillCliStatusTests(SkillCliFixture):
    def setUp(self):
        super().setUp()
        self.add_skill("alpha", "Use for alpha.")
        self.add_skill("beta", "Use for beta.")

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
        self.assertEqual(
            alpha["copies"],
            {a: "missing" for a in ("agents", "codex", "claude", "grok")},
        )
        self.assertEqual(rep["orphans"], [])
        self.assertEqual(rep["entrypoint"], str(self.entry))

    def test_active_and_dormant_from_claude_logs(self):
        project = self.home / ".claude/projects/demo"
        jsonl(
            project / "a.jsonl",
            claude_skill("c1", "alpha", "2024-01-01T00:00:00Z"),
            claude_skill("c2", "alpha", "2024-03-01T00:00:00Z"),
            claude_skill("c2", "alpha", "2024-03-02T00:00:00Z"),
            claude_skill("c3", "beta", "2023-01-01T00:00:00Z"),
        )
        rep = self.report()
        by_name = {s["name"]: s for s in rep["skills"]}
        self.assertEqual(by_name["alpha"]["usage"], "active")
        self.assertEqual(by_name["alpha"]["total"], 2)
        self.assertEqual(by_name["alpha"]["last_used"], "2024-03-01")
        self.assertEqual(by_name["beta"]["usage"], "dormant")
        self.assertEqual(by_name["beta"]["total"], 1)

    def test_drift_detection(self):
        self.install(".agents/skills", "alpha")
        self.install(".codex/skills", "alpha", "drifted\n")
        rep = self.report()
        by_name = {s["name"]: s for s in rep["skills"]}
        self.assertEqual(by_name["alpha"]["copies"]["agents"], "ok")
        self.assertEqual(by_name["alpha"]["copies"]["codex"], "drift")

    def test_hollow_and_missing(self):
        hollow = self.home / ".claude/skills/alpha"
        hollow.mkdir(parents=True)
        rep = self.report()
        by_name = {s["name"]: s for s in rep["skills"]}
        self.assertEqual(by_name["alpha"]["copies"]["claude"], "hollow")
        self.assertEqual(by_name["alpha"]["copies"]["grok"], "missing")

    def test_orphan_local_skill(self):
        orphan = self.install(".grok/skills", "ghost", "orphan\n")
        rep = self.report()
        [o] = [x for x in rep["orphans"] if x["name"] == "ghost"]
        self.assertEqual(o["agent"], "grok")
        self.assertNotIn("pruned", o)
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

    def test_registry_writes_and_preserves_purpose(self):
        result = self.run_cli("registry")
        self.assertEqual(result.returncode, 0)
        registry = self.entry / "skills.yaml"
        self.assertIn('name: "alpha"', registry.read_text())
        text = registry.read_text().replace('purpose: ""', 'purpose: "kept"', 1)
        registry.write_text(text)
        self.add_skill("alpha", "Changed description.")
        self.run_cli("registry")
        self.assertIn('purpose: "kept"', registry.read_text())
        self.assertIn("Changed description.", registry.read_text())

    def test_check_passes_when_current(self):
        self.run_cli("registry")
        self.assertEqual(self.run_cli("check").returncode, 0)

    def test_check_fails_when_stale(self):
        self.run_cli("registry")
        self.add_skill("alpha", "Changed description.")
        bad = self.run_cli("check", check=False)
        self.assertNotEqual(bad.returncode, 0)
        self.assertIn("out of date", bad.stderr)

    def test_add_creates_template(self):
        local_before = self.home / ".agents/skills/gamma"
        local_before.mkdir(parents=True)
        (local_before / "SKILL.md").write_text("local copy\n")
        result = self.run_cli("add", "gamma")
        self.assertEqual(result.returncode, 0)
        skill_md = self.entry / "skills/gamma/SKILL.md"
        self.assertTrue(skill_md.is_file())
        self.assertIn("name: gamma", skill_md.read_text())
        self.assertIn('name: "gamma"', (self.entry / "skills.yaml").read_text())
        self.assertEqual((local_before / "SKILL.md").read_text(), "local copy\n")

    def test_remove_deletes_folder_not_local(self):
        self.run_cli("add", "gamma")
        local_before = self.home / ".agents/skills/gamma"
        local_before.mkdir(parents=True)
        (local_before / "SKILL.md").write_text("local copy\n")
        result = self.run_cli("remove", "gamma")
        self.assertEqual(result.returncode, 0)
        self.assertFalse((self.entry / "skills/gamma").exists())
        self.assertNotIn("gamma", (self.entry / "skills.yaml").read_text())
        self.assertEqual((local_before / "SKILL.md").read_text(), "local copy\n")

    def test_remove_unknown_exits_2(self):
        result = self.run_cli("remove", "nosuch", check=False)
        self.assertEqual(result.returncode, 2)

    def test_add_external_registers_only(self):
        url, pin, path = make_git_skill_repo(self.root)
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
        self.assertEqual((local / "SKILL.md").read_text(), "old local\n")

    def test_add_external_checks_local_folder_before_fetch(self):
        self.add_skill("tool", "Local tool.")
        url, pin, path = make_git_skill_repo(self.root)
        result = self.run_cli(
            "add", "tool", "--source", url, "--pin", pin, "--path", path, check=False,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("local folder", result.stderr)
        # Should fail before fetch; registry unchanged for external
        registry = self.entry / "skills.yaml"
        self.assertTrue(not registry.is_file() or "source:" not in registry.read_text())

    def test_add_external_missing_skill_md_leaves_registry_alone(self):
        url, pin, _ = make_git_skill_repo(self.root)
        result = self.run_cli(
            "add", "tool", "--source", url, "--pin", pin, "--path", "missing",
            check=False,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((self.entry / "skills/tool").exists())
        registry = self.entry / "skills.yaml"
        self.assertTrue(not registry.is_file() or "tool" not in registry.read_text())

    def test_add_rejects_non_sha_pin(self):
        result = self.run_cli(
            "add", "tool",
            "--source", "https://github.com/example/skills",
            "--pin", "main",
            check=False,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("40-char commit SHA", result.stderr)

    def test_registry_parses_nested_source(self):
        self.run_cli("registry")
        pin = "a" * 40
        url = "https://github.com/example/skills"
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
            '    path: "tool"\n'
        )
        rep = self.report()
        by_name = {s["name"]: s for s in rep["skills"]}
        self.assertIn("tool", by_name)
        self.assertEqual(by_name["tool"]["source"]["url"], url)
        self.assertEqual(by_name["tool"]["source"]["pin"], pin)
        self.assertEqual(by_name["tool"]["source"]["path"], "tool")
        # Uncached + not installed → missing
        self.assertEqual(by_name["tool"]["copies"]["agents"], "missing")

    def test_status_uncached_installed_external_is_not_fetched(self):
        self.run_cli("registry")
        pin = "b" * 40
        url = "https://github.com/example/skills"
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
            '    path: "tool"\n'
        )
        self.install(".agents/skills", "tool", "installed but uncached\n")
        rep = self.report()
        by_name = {s["name"]: s for s in rep["skills"]}
        self.assertEqual(by_name["tool"]["copies"]["agents"], "not fetched")

    def test_check_requires_pin(self):
        self.run_cli("registry")
        registry = self.entry / "skills.yaml"
        registry.write_text(
            registry.read_text()
            + '- name: "tool"\n'
            '  description: "External tool"\n'
            '  status: "experimental"\n'
            '  purpose: ""\n'
            "  source:\n"
            '    url: "https://github.com/example/skills"\n'
        )
        bad = self.run_cli("check", check=False)
        self.assertNotEqual(bad.returncode, 0)
        self.assertIn("source.pin missing", bad.stderr)

    def test_check_rejects_non_sha_pin(self):
        self.run_cli("registry")
        registry = self.entry / "skills.yaml"
        registry.write_text(
            registry.read_text()
            + '- name: "tool"\n'
            '  description: "External tool"\n'
            '  status: "experimental"\n'
            '  purpose: ""\n'
            "  source:\n"
            '    url: "https://github.com/example/skills"\n'
            '    pin: "v1.2.3"\n'
        )
        bad = self.run_cli("check", check=False)
        self.assertNotEqual(bad.returncode, 0)
        self.assertIn("40-char commit SHA", bad.stderr)

    def test_check_rejects_local_folder_for_external(self):
        self.run_cli("registry")
        self.add_skill("tool", "Should not be both.")
        registry = self.entry / "skills.yaml"
        # Re-read after add_skill doesn't update registry; append external block
        # and also put tool in registry as local via registry command first
        self.run_cli("registry")
        text = registry.read_text()
        # Convert tool entry to external by rewriting — simpler: append source to tool
        # Actually registry wrote tool as local. Replace its block with external+folder remains.
        lines = []
        skip_until_next = False
        for line in text.splitlines(True):
            if line.startswith('- name: "tool"'):
                lines.append(line)
                lines.append('  description: "External"\n')
                lines.append('  status: "experimental"\n')
                lines.append('  purpose: ""\n')
                lines.append("  source:\n")
                lines.append('    url: "https://github.com/example/skills"\n')
                lines.append(f'    pin: "{"c" * 40}"\n')
                skip_until_next = True
                continue
            if skip_until_next:
                if line.startswith("- name:"):
                    skip_until_next = False
                    lines.append(line)
                continue
            lines.append(line)
        registry.write_text("".join(lines))
        bad = self.run_cli("check", check=False)
        self.assertNotEqual(bad.returncode, 0)
        self.assertIn("must not have", bad.stderr)

    def test_remove_external_drops_registry_only(self):
        url, pin, path = make_git_skill_repo(self.root)
        self.run_cli("add", "tool", "--source", url, "--pin", pin, "--path", path)
        self.assertIn("tool", (self.entry / "skills.yaml").read_text())
        result = self.run_cli("remove", "tool")
        self.assertEqual(result.returncode, 0)
        self.assertNotIn("tool", (self.entry / "skills.yaml").read_text())

    def test_eval_runs_local_script(self):
        runner = self.entry / "skills/alpha/evals/run"
        runner.parent.mkdir(parents=True)
        runner.write_text('#!/bin/sh\necho "dir=$SKILL_DIR arg=$1"\n')
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
        cfg_home = self.root / "cfg-toml"
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
