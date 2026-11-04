"""Pi theme switching uses temporary configs, never the real agent directory."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT.parents[2] / '.config/chameleon'


class PiCLI(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name)
        self.bin = self.home / 'bin'
        self.bin.mkdir()
        for tool in ('sh', 'dirname', 'awk', 'python3'):
            (self.bin / tool).symlink_to(shutil.which(tool))
        (self.bin / 'pi').symlink_to(shutil.which('true'))
        self.agent = self.home / 'custom-agent'
        self.settings = self.agent / 'settings.json'
        self.active = self.agent / 'themes/chameleon.json'
        self.config = self.home / '.config/chameleon'
        shutil.copytree(CONFIG / 'pi', self.config / 'pi')
        shutil.copytree(CONFIG / 'themes', self.config / 'themes')
        self.env = dict(os.environ, HOME=str(self.home), PATH=str(self.bin),
                        CHAMELEON_ROOT=str(ROOT),
                        PI_CODING_AGENT_DIR=str(self.agent))

    def apply(self, theme):
        return subprocess.run([str(ROOT / 'chameleon'), '-c', 'pi', theme],
                              env=dict(self.env, CHAMELEON_FOLLOW_APPEARANCE='1'),
                              capture_output=True, text=True, timeout=10)

    def test_watcher_switches_one_active_theme_and_keeps_other_settings(self):
        self.agent.mkdir()
        original = {'theme': 'system', 'defaultModel': 'keep',
                    'extensions': ['example.ts']}
        self.settings.write_text(json.dumps(original))
        for theme, appearance in [('dayfox', 'light'), ('miasma', 'dark'),
                                  ('latch', 'light'), ('solarized-light', 'light')]:
            with self.subTest(theme=theme):
                result = self.apply(theme)
                self.assertEqual(result.returncode, 0, result.stderr)
                active = json.loads(self.active.read_text())
                self.assertEqual(active['name'], 'chameleon')
                self.assertEqual(active['appearance'], appearance)
                profile = json.loads((self.config / f'pi/{appearance}.json').read_text())
                self.assertEqual(active, profile)
                self.assertEqual(json.loads(self.settings.read_text()),
                                 dict(original, theme='chameleon'))
        self.assertFalse((self.home / '.pi/agent').exists())
        self.assertFalse((self.config / 'current').exists())

    def test_repeated_application_writes_nothing(self):
        self.assertEqual(self.apply('dayfox').returncode, 0)
        before = [(path.stat().st_ino, path.stat().st_mtime_ns)
                  for path in (self.settings, self.active)]
        self.assertEqual(self.apply('dayfox').returncode, 0)
        self.assertEqual(before, [(path.stat().st_ino, path.stat().st_mtime_ns)
                                  for path in (self.settings, self.active)])

    def test_linked_settings_and_permissions_survive(self):
        self.agent.mkdir()
        target = self.home / 'linked-settings.json'
        target.write_text('{"theme":"system","quietStartup":true}\n')
        target.chmod(0o640)
        self.settings.symlink_to('../linked-settings.json')
        result = self.apply('miasma')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(self.settings.is_symlink())
        self.assertEqual(target.stat().st_mode & 0o777, 0o640)
        self.assertEqual(json.loads(target.read_text()),
                         {'theme': 'chameleon', 'quietStartup': True})

    def test_invalid_settings_are_not_overwritten(self):
        self.agent.mkdir()
        for content in ('not json', '[]'):
            with self.subTest(content=content):
                self.settings.write_text(content)
                result = self.apply('dayfox')
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(self.settings.read_text(), content)
                self.assertFalse(self.active.exists())

    def test_missing_mapping_or_profile_leaves_agent_untouched(self):
        for mapping in ('', 'pi=missing\n'):
            with self.subTest(mapping=mapping):
                (self.config / 'themes/dayfox.conf').write_text(mapping)
                result = subprocess.run(
                    [str(ROOT / 'modules/pi'), 'apply', 'dayfox'],
                    env=self.env, capture_output=True, text=True)
                self.assertEqual(result.returncode, 10, result.stderr)
                self.assertFalse(self.agent.exists())

    def test_uninstalled_agent_is_a_noop(self):
        (self.bin / 'pi').unlink()
        result = self.apply('dayfox')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(self.agent.exists())


if __name__ == '__main__':
    unittest.main()
