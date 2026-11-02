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

    def run_sync(self, *args, check=True):
        result = subprocess.run(
            ["zsh", str(self.script), *args],
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


    def use_fake_npx(self, fail=False):
        """Put an npx on PATH that 'installs' a skill offline and logs its call."""
        bin_dir = self.root / "bin"
        bin_dir.mkdir(exist_ok=True)
        self.npx_log = self.root / "npx.log"
        npx = bin_dir / "npx"
        npx.write_text(
            "#!/bin/sh\n"
            f'echo "$DISABLE_TELEMETRY $DO_NOT_TRACK $*" >> "{self.npx_log}"\n'
            + ("exit 1\n" if fail else "")
            + 'mkdir -p ".agents/skills/$6"\n'
            'echo "fetched $4" > ".agents/skills/$6/SKILL.md"\n'
        )
        npx.chmod(0o755)
        self.env["PATH"] = f"{bin_dir}{os.pathsep}{self.env['PATH']}"

    def write_manifest(self, data):
        (self.repo / ".agents/external-skills").write_bytes(data)

    def npx_calls(self):
        return self.npx_log.read_text().splitlines() if self.npx_log.exists() else []

    def test_external_skill_is_copied_to_every_skill_home(self):
        self.use_fake_npx()
        self.write_manifest(b"owner/repo tool\n")
        output = self.run_sync()
        self.assertEqual(
            self.npx_calls(), ["1 1 -y skills add owner/repo --skill tool --copy -y"]
        )
        for home in SKILL_HOMES:
            self.assertEqual(
                (self.home / home / "skills/tool/SKILL.md").read_text(),
                "fetched owner/repo\n",
            )
        self.assertIn("installed external skill tool from owner/repo\n", output)
        self.assert_shared_skills(self.home / home for home in SKILL_HOMES)

    def test_pinned_ref_is_passed_to_the_cli(self):
        self.use_fake_npx()
        self.write_manifest(b"owner/repo tool#v1.2\n")
        output = self.run_sync()
        self.assertEqual(
            self.npx_calls(), ["1 1 -y skills add owner/repo#v1.2 --skill tool --copy -y"]
        )
        self.assertIn("installed external skill tool from owner/repo@v1.2\n", output)

    def test_manifest_ignores_comments_blanks_crlf_and_spacing(self):
        self.use_fake_npx()
        self.write_manifest(
            b"# external\r\n\r\n  owner/one   first \r\n\towner/two second#abc\t\n\n"
        )
        self.run_sync()
        self.assertEqual(
            [call.split()[5] for call in self.npx_calls()],
            ["owner/one", "owner/two#abc"],
        )

    def test_malformed_manifest_line_aborts(self):
        self.use_fake_npx()
        self.write_manifest(b"owner/repo\n")
        result = self.run_sync(check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("external-skills:1: expected", result.stderr)
        self.assertEqual(list(self.home.iterdir()), [])

    def test_prune_keeps_external_skill(self):
        self.use_fake_npx()
        self.write_manifest(b"owner/repo tool\n")
        self.make_skill(".claude", "tool", "old\n")
        self.run_sync()
        self.assertEqual(self.removed_dirs(), [])
        self.assertEqual(
            (self.home / ".claude/skills/tool/SKILL.md").read_text(),
            "fetched owner/repo\n",
        )

    def test_fetch_failure_keeps_installed_copy(self):
        self.use_fake_npx(fail=True)
        self.write_manifest(b"owner/repo tool\n")
        kept = self.make_skill(".grok", "tool", "old\n")
        result = self.run_sync(check=False)
        self.assertEqual(result.returncode, 0)
        self.assertIn("could not fetch external skill tool from owner/repo", result.stderr)
        self.assertEqual(kept.read_text(), "old\n")
        self.assertEqual(self.removed_dirs(), [])
        self.assert_shared_skills(self.home / home for home in SKILL_HOMES)

    def test_missing_npx_skips_external_skill(self):
        bin_dir = self.root / "no-npx"
        bin_dir.mkdir()
        for tool in ("zsh", "date", "mkdir", "cp", "mv", "rm", "tail", "mktemp"):
            (bin_dir / tool).symlink_to(shutil.which(tool))
        self.env["PATH"] = str(bin_dir)
        self.write_manifest(b"owner/repo tool\n")
        kept = self.make_skill(".agents", "tool", "old\n")
        result = self.run_sync(check=False)
        self.assertEqual(result.returncode, 0)
        self.assertIn("npx not found; skipped external skill tool", result.stderr)
        self.assertEqual(kept.read_text(), "old\n")

    def test_external_skill_colliding_with_repo_skill_aborts(self):
        self.use_fake_npx()
        self.write_manifest(b"owner/repo example\n")
        result = self.run_sync(check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("external skill 'example' collides with", result.stderr)
        self.assertEqual(self.npx_calls(), [])
        self.assertEqual(list(self.home.iterdir()), [])

    def test_dry_run_reports_external_skill_without_fetching(self):
        self.use_fake_npx()
        self.write_manifest(b"owner/repo tool#main\n")
        output = self.run_sync("--dry-run")
        self.assertIn("would install external skill tool from owner/repo@main\n", output)
        self.assertEqual(self.npx_calls(), [])
        self.assertEqual(list(self.home.iterdir()), [])

if __name__ == "__main__":
    unittest.main()
