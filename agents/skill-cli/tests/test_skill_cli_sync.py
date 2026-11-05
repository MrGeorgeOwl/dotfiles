"""Exercise skill-cli sync without touching the user's agent configuration."""

import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "skill-cli"
HOME_VARS = ("AGENTS_HOME", "CODEX_HOME", "CLAUDE_HOME", "GROK_HOME", "PI_HOME")
XDG_VARS = ("XDG_CONFIG_HOME", "XDG_DATA_HOME")
SKILL_HOMES = (".agents", ".codex", ".claude", ".grok")


class SkillCliSyncTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.repo = self.root / "repo"
        self.home = self.root / "home"
        self.home.mkdir()
        self.entry = self.repo / "agents"
        self.script = self.entry / "skill-cli/skill-cli"
        self.script.parent.mkdir(parents=True)
        shutil.copy2(SCRIPT, self.script)
        self.skill = self.entry / "skills/example/SKILL.md"
        self.skill.parent.mkdir(parents=True)
        self.skill.write_text("---\nname: example\ndescription: Test skill\n---\n")
        (self.entry / "skills.yaml").write_text(
            '- name: "example"\n  description: "Test skill"\n'
            '  status: "active"\n  purpose: ""\n'
        )
        config = self.repo / ".pi/web-search.json"
        config.parent.mkdir()
        config.write_text("{}\n")
        self.env = {k: v for k, v in os.environ.items() if k not in HOME_VARS + XDG_VARS + ("SKILL_CLI_ENTRYPOINT",)}
        self.env["HOME"] = str(self.home)
        self.env["SKILL_CLI_ENTRYPOINT"] = str(self.entry)
        cache = self.root / "uv-cache"
        cache.mkdir()
        self.env["UV_CACHE_DIR"] = str(cache)
        self.env["XDG_CACHE_HOME"] = str(cache)

    def run_sync(self, *args, check=True):
        result = subprocess.run(
            ["uv", "run", "--script", str(self.script), "sync", *args],
            env=self.env, check=check, capture_output=True, text=True,
        )
        return result.stdout if check else result

    def assert_shared_skills(self, destinations):
        for dest in destinations:
            self.assertEqual(
                (dest / "skills/example/SKILL.md").read_bytes(),
                self.skill.read_bytes(),
            )

    def test_default_homes_without_duplicate_pi_skills(self):
        self.run_sync()
        self.assert_shared_skills(
            self.home / name for name in (".agents", ".codex", ".claude", ".grok")
        )
        self.assertFalse((self.home / ".pi/agent/skills").exists())
        self.assertEqual((self.home / ".pi/web-search.json").read_text(), "{}\n")
        existing = self.home / ".pi/agent/skills/example/SKILL.md"
        existing.parent.mkdir(parents=True)
        existing.write_text("local version\n")
        self.run_sync()
        self.assertEqual(existing.read_text(), "local version\n")

    def test_custom_homes(self):
        for name in HOME_VARS:
            self.env[name] = str(self.root / name)
        self.run_sync()
        self.assert_shared_skills(Path(self.env[name]) for name in HOME_VARS[:-1])
        pi = Path(self.env["PI_HOME"])
        self.assertFalse((pi / "agent/skills").exists())
        self.assertTrue((pi / "web-search.json").is_file())
        self.assertEqual(list(self.home.iterdir()), [])

    def test_dry_run_does_not_write(self):
        output = self.run_sync("--dry-run")
        self.assertIn(str(self.home / ".agents/skills"), output)
        self.assertNotIn(str(self.home / ".pi/agent/skills"), output)
        self.assertEqual(list(self.home.iterdir()), [])

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
        result = subprocess.run(
            ["uv", "run", "--script", str(self.script), "--entrypoint", str(other), "sync"],
            env=self.env, check=True, capture_output=True, text=True,
        )
        self.assertTrue((self.home / ".agents/skills/other/SKILL.md").is_file())
        self.assertFalse((self.home / ".agents/skills/example").exists())
        self.assertIn(str(other), result.stdout)

    def test_missing_entrypoint_explains_config(self):
        env = dict(self.env)
        del env["SKILL_CLI_ENTRYPOINT"]
        env["XDG_CONFIG_HOME"] = str(self.root / "cfg")
        result = subprocess.run(
            ["uv", "run", "--script", str(self.script), "sync"],
            env=env, check=False, capture_output=True, text=True,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("no entrypoint configured", result.stderr)
        self.assertIn("config.toml", result.stderr)
        self.assertIn('entrypoint =', result.stderr)

    def make_skill(self, home, name, text="local\n"):
        path = self.home / home / "skills" / name / "SKILL.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
        return path

    def removed_dirs(self):
        return sorted((self.home / ".local/share/skills").glob("removed-*"))

    def test_stale_skills_are_moved_to_backup(self):
        for home in SKILL_HOMES:
            self.make_skill(home, "stale", f"{home} copy\n")
        output = self.run_sync()
        [removed] = self.removed_dirs()
        for home in SKILL_HOMES:
            self.assertFalse((self.home / home / "skills/stale").exists())
            label = home.lstrip(".")
            self.assertEqual(
                (removed / label / "stale/SKILL.md").read_text(), f"{home} copy\n"
            )
            self.assertIn(
                f"removed stale skill {self.home / home / 'skills/stale'}", output
            )
        self.assert_shared_skills(self.home / home for home in SKILL_HOMES)

    def test_kept_hidden_and_plain_entries_survive(self):
        keep = self.home / ".config/skill-cli/keep-skills"
        keep.parent.mkdir(parents=True)
        keep.write_bytes(b"# local-only skills\r\n\r\n  mine \r\n\n")
        kept = self.make_skill(".claude", "mine")
        system = self.make_skill(".codex", ".system")
        note = self.home / ".grok/skills/notes.txt"
        note.parent.mkdir(parents=True)
        note.write_text("note\n")
        pi_only = self.home / ".pi/agent/skills/pi-only/SKILL.md"
        pi_only.parent.mkdir(parents=True)
        pi_only.write_text("pi\n")
        self.run_sync()
        for path in (kept, system, note, pi_only):
            self.assertTrue(path.is_file(), path)
        self.assertEqual(self.removed_dirs(), [])

    def test_legacy_keep_skills_path_still_honoured(self):
        keep = self.home / ".config/agent-sync/keep-skills"
        keep.parent.mkdir(parents=True)
        keep.write_text("mine\n")
        kept = self.make_skill(".claude", "mine")
        self.run_sync()
        self.assertTrue(kept.is_file())
        self.assertEqual(self.removed_dirs(), [])

    def test_symlinked_stale_skill_moves_link_not_target(self):
        outside = self.root / "outside/linked"
        outside.mkdir(parents=True)
        (outside / "SKILL.md").write_text("outside\n")
        link = self.home / ".agents/skills/linked"
        link.parent.mkdir(parents=True)
        link.symlink_to(outside)
        self.run_sync()
        [removed] = self.removed_dirs()
        self.assertFalse(os.path.lexists(link))
        self.assertTrue((removed / "agents/linked").is_symlink())
        self.assertEqual((outside / "SKILL.md").read_text(), "outside\n")

    def test_dry_run_reports_prune_without_changes(self):
        stale = self.make_skill(".claude", "stale")
        output = self.run_sync("--dry-run")
        self.assertIn(
            f"would remove stale skill {self.home / '.claude/skills/stale'}", output
        )
        self.assertEqual(stale.read_text(), "local\n")
        self.assertEqual(sorted(p.name for p in self.home.iterdir()), [".claude"])
        self.assertEqual(os.listdir(self.home / ".claude/skills"), ["stale"])

    def test_skill_evals_are_not_synced(self):
        evals = self.skill.parent / "evals/triggers.json"
        evals.parent.mkdir()
        evals.write_text("{}\n")
        (self.skill.parent / "agents").mkdir()
        (self.skill.parent / "agents/openai.yaml").write_text("x\n")
        self.run_sync()
        for home in SKILL_HOMES:
            skill = self.home / home / "skills/example"
            self.assertEqual(sorted(p.name for p in skill.iterdir()), ["SKILL.md", "agents"])

    def test_second_run_is_noop(self):
        self.make_skill(".grok", "stale")
        self.run_sync()
        first = self.removed_dirs()
        output = self.run_sync()
        self.assertEqual(self.removed_dirs(), first)
        self.assertNotIn("stale skill", output)
        self.assert_shared_skills(self.home / home for home in SKILL_HOMES)

    def make_git_skill_repo(self, name="tool", body="from-git\n", subdir=None):
        """Create a local bare-ish git repo with a skill; return (url, pin, path)."""
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
        url = src.resolve().as_uri()
        path = str(skill_rel) if subdir or True else ""
        return url, pin, str(skill_rel)

    def register_external(self, name, url, pin, path, body_desc=None):
        registry = self.entry / "skills.yaml"
        desc = body_desc or f"External {name}"
        registry.write_text(
            registry.read_text()
            + f'- name: "{name}"\n'
            f'  description: "{desc}"\n'
            f'  status: "active"\n'
            f'  purpose: ""\n'
            f"  source:\n"
            f'    url: "{url}"\n'
            f'    pin: "{pin}"\n'
            f'    path: "{path}"\n'
        )

    def test_external_skill_fetched_and_synced(self):
        url, pin, path = self.make_git_skill_repo()
        self.register_external("tool", url, pin, path)
        output = self.run_sync()
        for home in SKILL_HOMES:
            text = (self.home / home / "skills/tool/SKILL.md").read_text()
            self.assertIn("from-git", text)
        self.assert_shared_skills(self.home / home for home in SKILL_HOMES)
        self.assertIn("fetching", output)
        # Second sync is offline (cache hit).
        bin_dir = self.root / "no-git-needed"
        bin_dir.mkdir()
        for tool in ("uv", "python3", "mkdir", "cp", "mv", "rm"):
            which = shutil.which(tool)
            if which:
                (bin_dir / tool).symlink_to(which)
        # Keep git available via /usr/bin; just confirm no error and no re-fetch log required
        output2 = self.run_sync()
        self.assertNotIn("fetching", output2)

    def test_prune_keeps_external_skill(self):
        url, pin, path = self.make_git_skill_repo()
        self.register_external("tool", url, pin, path)
        self.make_skill(".claude", "tool", "old\n")
        self.run_sync()
        self.assertEqual(self.removed_dirs(), [])
        self.assertIn(
            "from-git",
            (self.home / ".claude/skills/tool/SKILL.md").read_text(),
        )

    def test_dry_run_skips_fetch_when_uncached(self):
        url, pin, path = self.make_git_skill_repo()
        self.register_external("tool", url, pin, path)
        output = self.run_sync("--dry-run")
        self.assertIn("would fetch", output)
        self.assertEqual(list(self.home.iterdir()), [])
        cache = Path(self.env["XDG_CACHE_HOME"]) / "skill-cli"
        self.assertFalse(cache.exists() and any(cache.rglob("SKILL.md")))

    def test_pin_mismatch_errors(self):
        url, pin, path = self.make_git_skill_repo()
        bad = "0" * 40
        self.register_external("tool", url, bad, path)
        result = self.run_sync(check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertTrue(
            "pin mismatch" in result.stderr or "could not fetch" in result.stderr
            or "could not checkout" in result.stderr,
            result.stderr,
        )

    def test_missing_skill_md_errors(self):
        url, pin, path = self.make_git_skill_repo()
        self.register_external("tool", url, pin, "no-such-dir")
        result = self.run_sync(check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("no SKILL.md", result.stderr)


if __name__ == "__main__":
    unittest.main()
