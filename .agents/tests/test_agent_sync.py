"""Exercise agent-sync without touching the user's agent configuration."""

import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "agent-sync"
HOME_VARS = ("AGENTS_HOME", "CODEX_HOME", "CLAUDE_HOME", "GROK_HOME", "PI_HOME")
XDG_VARS = ("XDG_CONFIG_HOME", "XDG_DATA_HOME")
SKILL_HOMES = (".agents", ".codex", ".claude", ".grok")


class AgentSyncTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.repo = self.root / "repo"
        self.home = self.root / "home"
        self.home.mkdir()
        self.script = self.repo / ".agents/agent-sync"
        self.script.parent.mkdir(parents=True)
        shutil.copy2(SCRIPT, self.script)
        self.skill = self.repo / ".agents/skills/example/SKILL.md"
        self.skill.parent.mkdir(parents=True)
        self.skill.write_text("---\nname: example\ndescription: Test skill\n---\n")
        config = self.repo / ".pi/web-search.json"
        config.parent.mkdir()
        config.write_text("{}\n")
        self.env = {k: v for k, v in os.environ.items() if k not in HOME_VARS + XDG_VARS}
        self.env["HOME"] = str(self.home)

    def run_sync(self, *args):
        return subprocess.run(
            ["zsh", str(self.script), *args],
            env=self.env, check=True, capture_output=True, text=True,
        ).stdout

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
        # Existing Pi-only or locally modified skills must not be deleted.
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

    def make_skill(self, home, name, text="local\n"):
        path = self.home / home / "skills" / name / "SKILL.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
        return path

    def removed_dirs(self):
        return sorted((self.home / ".local/share/agent-sync").glob("removed-*"))

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
        keep = self.home / ".config/agent-sync/keep-skills"
        keep.parent.mkdir(parents=True)
        keep.write_text("# local-only skills\nmine\n")
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

    def test_second_run_is_noop(self):
        self.make_skill(".grok", "stale")
        self.run_sync()
        first = self.removed_dirs()
        output = self.run_sync()
        self.assertEqual(self.removed_dirs(), first)
        self.assertNotIn("stale skill", output)
        self.assert_shared_skills(self.home / home for home in SKILL_HOMES)


if __name__ == "__main__":
    unittest.main()
