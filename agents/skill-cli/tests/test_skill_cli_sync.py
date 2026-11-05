"""Exercise skill-cli sync without touching the user's agent configuration."""

from __future__ import annotations

import os
from pathlib import Path
import subprocess as sp
import unittest
from unittest import mock

from helpers import HOME_VARS, SKILL_HOMES, SkillCliFixture, load_skill_cli, make_git_skill_repo


class SyncFixture(SkillCliFixture):
    def setUp(self):
        super().setUp()
        self.skill = self.add_skill("example")
        self.write_registry(self.registry_entry("example"))
        (self.root / "repo/.pi").mkdir(parents=True)
        (self.root / "repo/.pi/web-search.json").write_text("{}\n")

    def run_sync(self, *args, check=True):
        return self.run_cli("sync", *args, check=check)

    def assert_shared_skills(self, destinations):
        for dest in destinations:
            self.assertEqual(
                (Path(dest) / "skills/example/SKILL.md").read_bytes(),
                self.skill.read_bytes(),
            )

    def make_local_skill(self, home, name, text="local\n"):
        path = self.home / home / "skills" / name / "SKILL.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
        return path


class DefaultHomesSyncTests(SyncFixture):
    def test_installs_without_duplicate_pi_skills(self):
        self.run_sync()
        self.assert_shared_skills(self.home / name for name in SKILL_HOMES)
        self.assertFalse((self.home / ".pi/agent/skills").exists())
        self.assertEqual((self.home / ".pi/web-search.json").read_text(), "{}\n")

    def test_pi_agent_skills_left_alone(self):
        existing = self.home / ".pi/agent/skills/example/SKILL.md"
        existing.parent.mkdir(parents=True)
        existing.write_text("local version\n")
        self.run_sync()
        self.assertEqual(existing.read_text(), "local version\n")

    def test_dry_run_does_not_write(self):
        stale = self.make_local_skill(".claude", "stale")
        output = self.run_sync("--dry-run").stdout
        self.assertIn(str(self.home / ".agents/skills"), output)
        self.assertNotIn(str(self.home / ".pi/agent/skills"), output)
        self.assertEqual(stale.read_text(), "local\n")
        self.assertEqual(sorted(p.name for p in self.home.iterdir()), [".claude"])

    def test_local_only_skills_survive_sync(self):
        local = self.make_local_skill(".claude", "mine", "keep me\n")
        self.run_sync()
        self.assertEqual(local.read_text(), "keep me\n")
        self.assertTrue((self.home / ".claude/skills/example/SKILL.md").is_file())

    def test_symlinked_local_skill_untouched(self):
        outside = self.root / "outside/linked"
        outside.mkdir(parents=True)
        (outside / "SKILL.md").write_text("outside\n")
        link = self.home / ".agents/skills/linked"
        link.parent.mkdir(parents=True)
        link.symlink_to(outside)
        self.run_sync()
        self.assertTrue(link.is_symlink())
        self.assertEqual((outside / "SKILL.md").read_text(), "outside\n")

    def test_skill_evals_are_not_synced(self):
        evals = self.skill.parent / "evals/triggers.json"
        evals.parent.mkdir()
        evals.write_text("{}\n")
        (self.skill.parent / "agents").mkdir()
        (self.skill.parent / "agents/openai.yaml").write_text("x\n")
        self.run_sync()
        for home in SKILL_HOMES:
            skill = self.home / home / "skills/example"
            self.assertEqual(
                sorted(p.name for p in skill.iterdir()), ["SKILL.md", "agents"]
            )

    def test_destination_only_nested_files_survive(self):
        (self.root / "repo/.pi/agent").mkdir(parents=True)
        (self.root / "repo/.pi/agent/settings.json").write_text('{"from":"repo"}\n')
        dest_session = self.home / ".pi/agent/sessions/s.jsonl"
        dest_session.parent.mkdir(parents=True)
        dest_session.write_text('{"local":true}\n')
        dest_auth = self.home / ".pi/agent/auth.json"
        dest_auth.write_text('{"token":"secret"}\n')
        self.run_sync()
        self.assertEqual(dest_session.read_text(), '{"local":true}\n')
        self.assertEqual(dest_auth.read_text(), '{"token":"secret"}\n')
        self.assertEqual(
            (self.home / ".pi/agent/settings.json").read_text(), '{"from":"repo"}\n'
        )

    def test_agents_field_limits_targets(self):
        self.write_registry(self.registry_entry("example", agents='["claude"]'))
        self.run_sync()
        self.assertTrue((self.home / ".claude/skills/example/SKILL.md").is_file())
        self.assertFalse((self.home / ".agents/skills/example").exists())
        self.assertFalse((self.home / ".codex/skills/example").exists())
        self.assertFalse((self.home / ".grok/skills/example").exists())

    def test_external_skill_fetched_and_synced(self):
        repo = make_git_skill_repo(self.root, body="from-git\n")
        self.write_registry(
            self.registry_entry("example"),
            self.registry_entry(
                "tool",
                description="External tool",
                source={"url": repo.url, "pin": repo.pin, "path": repo.path},
            ),
        )
        output = self.run_sync().stdout
        for home in SKILL_HOMES:
            self.assertIn(
                "from-git",
                (self.home / home / "skills/tool/SKILL.md").read_text(),
            )
        self.assertIn("fetching", output)
        output2 = self.run_sync().stdout
        self.assertNotIn("fetching", output2)

    def test_external_skill_without_path(self):
        for label, kwargs in (
            ("named-subdir", {}),
            ("repo-root", {"at_root": True}),
        ):
            with self.subTest(label):
                self.setUp()
                repo = make_git_skill_repo(self.root, name="tool", **kwargs)
                source = {"url": repo.url, "pin": repo.pin}
                if repo.path:
                    source["path"] = repo.path
                self.write_registry(
                    self.registry_entry("example"),
                    self.registry_entry(
                        "tool", description="External tool", source=source,
                    ),
                )
                self.run_sync()
                self.assertTrue(
                    (self.home / ".agents/skills/tool/SKILL.md").is_file()
                )

    def test_dry_run_skips_fetch_when_uncached(self):
        repo = make_git_skill_repo(self.root)
        self.write_registry(
            self.registry_entry("example"),
            self.registry_entry(
                "tool",
                description="External tool",
                source={"url": repo.url, "pin": repo.pin, "path": repo.path},
            ),
        )
        output = self.run_sync("--dry-run").stdout
        self.assertIn("would fetch", output)
        self.assertFalse(any(Path(self.env["XDG_CACHE_HOME"]).rglob("SKILL.md")))

    def test_failed_external_continues_sync(self):
        cases = (
            ("missing-skill-md", None, "no SKILL.md"),
            (
                "bad-fetch",
                {"url": "file:///no/such/repo", "pin": "0" * 40, "path": "tool"},
                None,
            ),
            (
                "ssh-url",
                {
                    "url": "ssh://git@github.com/example/skills",
                    "pin": "0" * 40,
                    "path": "tool",
                },
                None,
            ),
        )
        for label, source, needle in cases:
            with self.subTest(label):
                self.setUp()
                if label == "missing-skill-md":
                    repo = make_git_skill_repo(self.root)
                    source = {
                        "url": repo.url,
                        "pin": repo.pin,
                        "path": "no-such-dir",
                    }
                self.write_registry(
                    self.registry_entry("example"),
                    self.registry_entry(
                        "tool", description="External tool", source=source,
                    ),
                )
                result = self.run_sync(check=False)
                self.assertNotEqual(result.returncode, 0)
                if needle:
                    self.assertIn(needle, result.stderr)
                self.assertTrue(
                    (self.home / ".agents/skills/example/SKILL.md").is_file()
                )
                self.assertTrue((self.home / ".pi/web-search.json").is_file())

    def test_pin_mismatch_errors(self):
        repo = make_git_skill_repo(self.root)
        os.environ["XDG_CACHE_HOME"] = self.env["XDG_CACHE_HOME"]
        mod = load_skill_cli()
        real_run = sp.run

        def fake_run(cmd, *args, **kwargs):
            result = real_run(cmd, *args, **kwargs)
            if list(cmd[:2]) == ["git", "rev-parse"]:
                return sp.CompletedProcess(
                    args=result.args,
                    returncode=0,
                    stdout="0" * 40 + "\n",
                    stderr=result.stderr or "",
                )
            return result

        with mock.patch.object(mod.subprocess, "run", side_effect=fake_run):
            with self.assertRaises(mod.FetchError) as ctx:
                mod.ensure_fetched(repo.url, repo.pin)
        self.assertIn("pin mismatch", str(ctx.exception))


class CustomHomesSyncTests(SyncFixture):
    def setUp(self):
        super().setUp()
        for name in HOME_VARS:
            self.env[name] = str(self.root / name)

    def test_installs_into_env_homes_only(self):
        self.run_sync()
        self.assert_shared_skills(Path(self.env[name]) for name in HOME_VARS[:-1])
        pi = Path(self.env["PI_HOME"])
        self.assertFalse((pi / "agent/skills").exists())
        self.assertTrue((pi / "web-search.json").is_file())
        self.assertEqual(list(self.home.iterdir()), [])


if __name__ == "__main__":
    unittest.main()
