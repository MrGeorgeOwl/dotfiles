"""Exercise skill-cli status, registry, check, eval, add, remove, entrypoint."""

from __future__ import annotations

import json
from pathlib import Path
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


class StatusFixture(SkillCliFixture):
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


class StatusTests(StatusFixture):
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
        (self.home / ".claude/skills/alpha").mkdir(parents=True)
        rep = self.report()
        by_name = {s["name"]: s for s in rep["skills"]}
        self.assertEqual(by_name["alpha"]["copies"]["claude"], "hollow")
        self.assertEqual(by_name["alpha"]["copies"]["grok"], "missing")

    def test_orphan_local_skill(self):
        self.install(".grok/skills", "ghost", "orphan\n")
        rep = self.report()
        [o] = [x for x in rep["orphans"] if x["name"] == "ghost"]
        self.assertEqual(o["agent"], "grok")

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

    def test_registry_parses_nested_source(self):
        pin = "a" * 40
        url = "https://github.com/example/skills"
        self.write_registry(
            self.registry_entry("alpha", description="Use for alpha."),
            self.registry_entry("beta", description="Use for beta."),
            self.registry_entry(
                "tool",
                description="External tool",
                status="experimental",
                source={"url": url, "pin": pin, "path": "tool"},
            ),
        )
        rep = self.report()
        by_name = {s["name"]: s for s in rep["skills"]}
        self.assertIn("tool", by_name)
        self.assertEqual(by_name["tool"]["source"]["url"], url)
        self.assertEqual(by_name["tool"]["source"]["pin"], pin)
        self.assertEqual(by_name["tool"]["source"]["path"], "tool")
        self.assertEqual(by_name["tool"]["copies"]["agents"], "missing")

    def test_status_uncached_installed_external_is_not_fetched(self):
        pin = "b" * 40
        url = "https://github.com/example/skills"
        self.write_registry(
            self.registry_entry("alpha", description="Use for alpha."),
            self.registry_entry("beta", description="Use for beta."),
            self.registry_entry(
                "tool",
                description="External tool",
                status="experimental",
                source={"url": url, "pin": pin, "path": "tool"},
            ),
        )
        self.install(".agents/skills", "tool", "installed but uncached\n")
        rep = self.report()
        by_name = {s["name"]: s for s in rep["skills"]}
        self.assertEqual(by_name["tool"]["copies"]["agents"], "not fetched")


class RegistryCheckTests(StatusFixture):
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

    def test_registry_keeps_source_without_url(self):
        self.write_registry(
            self.registry_entry("alpha", description="Use for alpha."),
            self.registry_entry("beta", description="Use for beta."),
            self.registry_entry(
                "tool",
                description="External tool",
                status="experimental",
                purpose="keep me",
                source={"pin": "d" * 40},
            ),
        )
        bad = self.run_cli("check", check=False)
        self.assertNotEqual(bad.returncode, 0)
        self.assertIn("source.url missing", bad.stderr)
        self.assertNotIn("out of date", bad.stderr)
        # registry rewrites but still reports the incomplete source (exit 1)
        rewritten = self.run_cli("registry", check=False)
        self.assertIn("source.url missing", rewritten.stderr)
        text = (self.entry / "skills.yaml").read_text()
        self.assertIn('name: "tool"', text)
        self.assertIn('purpose: "keep me"', text)
        self.assertIn("source:", text)

    def test_check_passes_when_current(self):
        self.run_cli("registry")
        self.assertEqual(self.run_cli("check").returncode, 0)

    def test_check_fails_when_stale(self):
        self.run_cli("registry")
        self.add_skill("alpha", "Changed description.")
        bad = self.run_cli("check", check=False)
        self.assertNotEqual(bad.returncode, 0)
        self.assertIn("out of date", bad.stderr)

    def test_check_pin_and_url_problems(self):
        cases = (
            ("missing-pin", {"url": "https://github.com/example/skills"}, "source.pin missing"),
            (
                "non-sha",
                {"url": "https://github.com/example/skills", "pin": "v1.2.3"},
                "40-char commit SHA",
            ),
            (
                "unrecognized-url",
                {"url": "not-a-git-url", "pin": "c" * 40},
                "unrecognized git url",
            ),
            (
                "ssh-url",
                {
                    "url": "ssh://git@github.com/example/skills",
                    "pin": "c" * 40,
                    "path": "tool",
                },
                None,  # recognized; may still fail out-of-date vs hand-built YAML
            ),
        )
        for label, source, needle in cases:
            with self.subTest(label):
                self.write_registry(
                    self.registry_entry("alpha", description="Use for alpha."),
                    self.registry_entry("beta", description="Use for beta."),
                    self.registry_entry(
                        "tool",
                        description="External tool",
                        status="experimental",
                        source=source,
                    ),
                )
                result = self.run_cli("check", check=False)
                if needle is None:
                    # ssh is valid; regenerate so only source validity matters, then check
                    # Hand YAML may drift from render; assert scheme is accepted.
                    self.assertNotIn("unrecognized git url", result.stderr)
                    # Status must include it without exiting
                    rep = self.report()
                    self.assertEqual(
                        {s["name"]: s for s in rep["skills"]}["tool"]["source"]["url"],
                        source["url"],
                    )
                else:
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn(needle, result.stderr)

    def test_check_rejects_bad_agents(self):
        self.write_registry(
            self.registry_entry("alpha", description="Use for alpha.", agents='["claud"]'),
            self.registry_entry("beta", description="Use for beta."),
        )
        bad = self.run_cli("check", check=False)
        self.assertNotEqual(bad.returncode, 0)
        self.assertIn("unknown agents", bad.stderr)
        # status must not die on bad agents
        rep = self.report()
        self.assertTrue(any(s["name"] == "alpha" for s in rep["skills"]))

    def test_check_rejects_bad_registry_name(self):
        pin = "d" * 40
        bad_entry = (
            '- name: "../../../escaped"\n'
            '  description: "bad"\n'
            '  status: "experimental"\n'
            '  purpose: ""\n'
            "  source:\n"
            '    url: "https://github.com/example/skills"\n'
            f'    pin: "{pin}"\n'
        )
        self.write_registry(
            self.registry_entry("alpha", description="Use for alpha."),
            self.registry_entry("beta", description="Use for beta."),
            bad_entry,
        )
        bad = self.run_cli("check", check=False)
        self.assertNotEqual(bad.returncode, 0)
        self.assertIn("lowercase-hyphen", bad.stderr)

    def test_check_rejects_local_folder_for_external(self):
        self.add_skill("tool", "Should not be both.")
        self.write_registry(
            self.registry_entry("alpha", description="Use for alpha."),
            self.registry_entry("beta", description="Use for beta."),
            self.registry_entry(
                "tool",
                description="External",
                status="experimental",
                source={
                    "url": "https://github.com/example/skills",
                    "pin": "c" * 40,
                },
            ),
        )
        bad = self.run_cli("check", check=False)
        self.assertNotEqual(bad.returncode, 0)
        self.assertIn("must not have", bad.stderr)


class AddRemoveTests(StatusFixture):
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

    def test_remove_invalid_names_delete_nothing(self):
        self.run_cli("registry")
        before = {
            p: p.read_bytes() if p.is_file() else None
            for p in sorted((self.entry / "skills").rglob("*"))
        }
        registry_before = (self.entry / "skills.yaml").read_text()
        for bad in ("", "..", "a/b"):
            with self.subTest(bad=bad):
                result = self.run_cli("remove", bad, check=False)
                self.assertNotEqual(result.returncode, 0)
                self.assertTrue((self.entry / "skills/alpha/SKILL.md").is_file())
                self.assertTrue((self.entry / "skills/beta/SKILL.md").is_file())
                self.assertEqual((self.entry / "skills.yaml").read_text(), registry_before)
                after = {
                    p: p.read_bytes() if p.is_file() else None
                    for p in sorted((self.entry / "skills").rglob("*"))
                }
                self.assertEqual(after, before)

    def test_add_external_registers_only(self):
        repo = make_git_skill_repo(self.root)
        local = self.home / ".agents/skills/tool"
        local.mkdir(parents=True)
        (local / "SKILL.md").write_text("old local\n")
        result = self.run_cli(
            "add", "tool", "--source", repo.url, "--pin", repo.pin, "--path", repo.path,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse((self.entry / "skills/tool").exists())
        registry = (self.entry / "skills.yaml").read_text()
        self.assertIn("source:", registry)
        self.assertIn(f'url: "{repo.url}"', registry)
        self.assertIn(f'pin: "{repo.pin}"', registry)
        self.assertEqual((local / "SKILL.md").read_text(), "old local\n")

    def test_add_external_checks_local_folder_before_fetch(self):
        self.add_skill("tool", "Local tool.")
        self.run_cli("registry")
        repo = make_git_skill_repo(self.root)
        result = self.run_cli(
            "add", "tool", "--source", repo.url, "--pin", repo.pin,
            "--path", repo.path, check=False,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("local folder", result.stderr)
        self.assertFalse(any(Path(self.env["XDG_CACHE_HOME"]).rglob("SKILL.md")))
        registry = self.entry / "skills.yaml"
        self.assertTrue(registry.is_file())
        self.assertNotIn("source:", registry.read_text())

    def test_add_external_missing_skill_md_leaves_registry_alone(self):
        self.run_cli("registry")
        before = (self.entry / "skills.yaml").read_text()
        repo = make_git_skill_repo(self.root)
        result = self.run_cli(
            "add", "tool", "--source", repo.url, "--pin", repo.pin, "--path", "missing",
            check=False,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((self.entry / "skills/tool").exists())
        self.assertEqual((self.entry / "skills.yaml").read_text(), before)
        self.assertNotIn("tool", before)

    def test_add_rejects_non_sha_pin(self):
        result = self.run_cli(
            "add", "tool",
            "--source", "https://github.com/example/skills",
            "--pin", "main",
            check=False,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("40-char commit SHA", result.stderr)

    def test_remove_external_drops_registry_only(self):
        repo = make_git_skill_repo(self.root)
        self.run_cli(
            "add", "tool", "--source", repo.url, "--pin", repo.pin, "--path", repo.path,
        )
        self.assertIn("tool", (self.entry / "skills.yaml").read_text())
        result = self.run_cli("remove", "tool")
        self.assertEqual(result.returncode, 0)
        self.assertNotIn("tool", (self.entry / "skills.yaml").read_text())


class EvalTests(StatusFixture):
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

    def test_eval_invalid_name(self):
        result = self.run_cli("eval", "..", check=False)
        self.assertNotEqual(result.returncode, 0)


class EntrypointTests(SkillCliFixture):
    def setUp(self):
        super().setUp()
        self.add_skill("example")
        self.write_registry(self.registry_entry("example"))
        (self.root / "repo/.pi").mkdir(parents=True)
        (self.root / "repo/.pi/web-search.json").write_text("{}\n")

    def test_entrypoint_flag_overrides_env(self):
        other = self.root / "other/agents"
        other.mkdir(parents=True)
        (other / "skills/other/SKILL.md").parent.mkdir(parents=True)
        (other / "skills/other/SKILL.md").write_text(
            "---\nname: other\ndescription: Other\n---\n"
        )
        (other / "skills.yaml").write_text(
            '- name: "other"\n  description: "Other"\n  status: "active"\n  purpose: ""\n'
        )
        result = self.run_cli("--entrypoint", str(other), "sync")
        self.assertTrue((self.home / ".agents/skills/other/SKILL.md").is_file())
        self.assertFalse((self.home / ".agents/skills/example").exists())
        self.assertIn(str(other), result.stdout)

    def test_missing_entrypoint_explains_config(self):
        env = dict(self.env)
        del env["SKILL_CLI_ENTRYPOINT"]
        env["XDG_CONFIG_HOME"] = str(self.root / "cfg-empty")
        result = self.run_cli("sync", check=False, env=env)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("no entrypoint configured", result.stderr)
        self.assertIn("config.toml", result.stderr)
        self.assertIn("entrypoint =", result.stderr)

    def test_config_toml_entrypoint(self):
        env = dict(self.env)
        del env["SKILL_CLI_ENTRYPOINT"]
        cfg_home = self.root / "cfg-toml"
        cfg = cfg_home / "skill-cli/config.toml"
        cfg.parent.mkdir(parents=True)
        cfg.write_text(f'entrypoint = "{self.entry}"\n')
        env["XDG_CONFIG_HOME"] = str(cfg_home)
        result = self.run_cli("status", "--json", env=env)
        rep = json.loads(result.stdout)
        self.assertEqual(rep["entrypoint"], str(self.entry))
        self.assertGreaterEqual(len(rep["skills"]), 1)


class ParseRecordTests(StatusFixture):
    """Feed agent log shapes through status --json (same path as production)."""

    def test_parse_codex_record(self):
        session = self.home / ".codex/sessions/s.jsonl"
        jsonl(
            session,
            {
                "timestamp": "2024-05-01T00:00:00Z",
                "payload": {
                    "type": "function_call",
                    "call_id": "c1",
                    "arguments": json.dumps({
                        "cmd": ["cat", "/home/u/.agents/skills/alpha/SKILL.md"],
                    }),
                },
            },
        )
        rep = self.report()
        by_name = {s["name"]: s for s in rep["skills"]}
        self.assertEqual(by_name["alpha"]["loads"].get("codex"), 1)

    def test_parse_grok_record(self):
        updates = self.home / ".grok/sessions/s/updates.jsonl"
        jsonl(
            updates,
            {
                "timestamp": "2024-05-02T00:00:00Z",
                "params": {
                    "update": {
                        "sessionUpdate": "tool_call",
                        "toolCallId": "g1",
                        "rawInput": {"path": "/h/.grok/skills/beta/SKILL.md"},
                    }
                },
            },
        )
        rep = self.report()
        by_name = {s["name"]: s for s in rep["skills"]}
        self.assertEqual(by_name["beta"]["loads"].get("grok"), 1)

    def test_parse_claude_read_and_command(self):
        project = self.home / ".claude/projects/demo"
        jsonl(
            project / "a.jsonl",
            {
                "type": "assistant",
                "timestamp": "2024-05-03T00:00:00Z",
                "message": {
                    "content": [{
                        "type": "tool_use",
                        "id": "r1",
                        "name": "Read",
                        "input": {"file_path": "/h/.claude/skills/alpha/SKILL.md"},
                    }]
                },
            },
            {
                "type": "user",
                "uuid": "u1",
                "timestamp": "2024-05-04T00:00:00Z",
                "message": {"content": "<command-name>/beta</command-name>"},
            },
        )
        rep = self.report()
        by_name = {s["name"]: s for s in rep["skills"]}
        self.assertEqual(by_name["alpha"]["loads"].get("claude"), 1)
        self.assertEqual(by_name["beta"]["loads"].get("claude"), 1)



if __name__ == "__main__":
    unittest.main()
