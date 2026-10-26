"""Wallpaper checks use temporary configs and fake desktop commands only."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
import unittest

ROOT = Path(__file__).resolve().parents[1]
TIMEOUT = shutil.which('timeout')


class WallpaperCLI(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name)
        self.bin = self.home / 'bin'
        self.bin.mkdir()
        # Isolate PATH so a missing mock can never call the real desktop tools.
        for tool in ('sh', 'awk', 'sed', 'dirname'):
            (self.bin / tool).symlink_to(shutil.which(tool))
        self.env = dict(os.environ, HOME=str(self.home), PATH=str(self.bin),
                        CHAMELEON_ROOT=str(ROOT), CHAMELEON_VERBOSE='1',
                        CHAMELEON_WALLPAPERS_DIR=str(self.home / 'Wallpapers'),
                        SSH_CONNECTION='', SSH_CLIENT='', SSH_TTY='',
                        DISPLAY='', WAYLAND_DISPLAY='', XDG_SESSION_TYPE='tty')
        self.calls = self.home / 'qdbus.json'
        self.timeout_args = self.home / 'timeout.args'
        self.env.update(TEST_DBUS_CALL=str(self.calls),
                        TEST_TIMEOUT_ARGS=str(self.timeout_args),
                        TEST_OSASCRIPT_CALL=str(self.home / 'osascript.call'))
        self.script('uname', 'echo Linux')
        self.script('timeout', 'printf "%s\\n" "$@" > "$TEST_TIMEOUT_ARGS"\n'
                              'shift 2\nexec "$@"')
        self.script('osascript', 'printf called > "$TEST_OSASCRIPT_CALL"')
        self.dbus_script('')
        themes = self.home / '.config/chameleon/themes'
        themes.mkdir(parents=True)
        (themes / 'test.conf').write_text('wallpaper=test.png\n')
        wallpapers = self.home / 'Wallpapers'
        wallpapers.mkdir()
        (wallpapers / 'test.png').touch()
        self.current = themes.parent / 'current'
        self.current.write_text('previous\n')

    def script(self, name, body):
        target = self.bin / name
        target.write_text('#!/bin/sh\n' + body + '\n')
        target.chmod(0o700)

    def dbus_script(self, body):
        target = self.bin / 'qdbus6'
        target.write_text(f'#!{sys.executable}\n'
                          'import json, os, signal, sys, time\n'
                          'from pathlib import Path\n'
                          'Path(os.environ["TEST_DBUS_CALL"]).write_text('
                          'json.dumps(sys.argv[1:]))\n' + body + '\n')
        target.chmod(0o700)

    def run_module(self, **env):
        return subprocess.run([str(ROOT / 'modules/wallpaper'), 'apply', 'test'],
                              env=dict(self.env, **env), capture_output=True,
                              text=True, timeout=10)

    def test_headless_skips_before_wallpaper_validation(self):
        (self.home / 'Wallpapers/test.png').unlink()
        result = self.run_module(DBUS_SESSION_BUS_ADDRESS='unix:path=/unused')
        self.assertEqual(result.returncode, 10, result.stderr)
        self.assertIn('no graphical session', result.stderr)
        self.assertFalse(self.calls.exists())
        self.assertFalse(self.timeout_args.exists())

    def test_ssh_skips_even_with_a_display(self):
        for platform in ('Linux', 'Darwin'):
            self.script('uname', f'echo {platform}')
            for variable in ('SSH_CONNECTION', 'SSH_CLIENT', 'SSH_TTY'):
                with self.subTest(platform=platform, variable=variable):
                    result = self.run_module(**{variable: 'remote', 'DISPLAY': ':10'})
                    self.assertEqual(result.returncode, 10, result.stderr)
                    self.assertIn('SSH session', result.stderr)
                    self.assertFalse(self.calls.exists())
                    self.assertFalse((self.home / 'osascript.call').exists())

    def test_local_x11_and_wayland_apply_with_a_timeout(self):
        for env in ({'DISPLAY': ':0'}, {'WAYLAND_DISPLAY': 'wayland-0'}):
            with self.subTest(env=env):
                result = self.run_module(**env)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn("applied 'test.png'", result.stdout)
                args = json.loads(self.calls.read_text())
                self.assertEqual(args[:3], ['org.kde.plasmashell', '/PlasmaShell',
                                           'org.kde.PlasmaShell.evaluateScript'])
                self.assertIn(f'file://{self.home}/Wallpapers/test.png', args[3])
                self.assertEqual(self.timeout_args.read_text().splitlines()[:2],
                                 ['--kill-after=1s', '5s'])

    def test_local_macos_does_not_require_linux_display_variables(self):
        self.script('uname', 'echo Darwin')
        result = self.run_module()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((self.home / 'osascript.call').exists())
        self.assertFalse(self.calls.exists())

    def test_cli_skip_is_successful_unless_fail_fast(self):
        for flags, expected in (([], 0), (['--fail-fast'], 1)):
            with self.subTest(flags=flags):
                result = subprocess.run(
                    [str(ROOT / 'chameleon'), '-v', *flags, '-c', 'wallpaper', 'test'],
                    env=self.env, capture_output=True, text=True, timeout=10)
                self.assertEqual(result.returncode, expected, result.stderr)
                self.assertIn('wallpaper: skipped', result.stdout)
                self.assertEqual(self.current.read_text(), 'previous\n')
                self.assertFalse(self.calls.exists())

    def test_skip_is_silent_without_verbose(self):
        result = self.run_module(CHAMELEON_VERBOSE='0')
        self.assertEqual(result.returncode, 10)
        self.assertEqual(result.stdout + result.stderr, '')

    def test_missing_dependencies_fail_without_calling_dbus(self):
        for tool in ('qdbus6', 'timeout'):
            with self.subTest(tool=tool):
                path = self.bin / tool
                hidden = path.with_suffix('.hidden')
                path.rename(hidden)
                try:
                    result = self.run_module(DISPLAY=':0')
                finally:
                    hidden.rename(path)
                self.assertEqual(result.returncode, 1, result.stderr)
                self.assertIn(f'{tool} not found', result.stderr)
                self.assertFalse(self.calls.exists())

    def test_dbus_failure_keeps_diagnostics(self):
        self.dbus_script('print("DBus test failure", file=sys.stderr)\nsys.exit(1)')
        result = self.run_module(DISPLAY=':0')
        self.assertEqual(result.returncode, 1)
        self.assertIn('DBus test failure', result.stderr)
        self.assertIn('failed to set wallpaper with qdbus6', result.stderr)
        self.assertNotIn('applied', result.stdout)

    def test_timeout_diagnostic(self):
        for status in (124, 137):
            with self.subTest(status=status):
                self.script('timeout', f'exit {status}')
                result = self.run_module(DISPLAY=':0')
                self.assertEqual(result.returncode, 1)
                self.assertIn('KDE Plasma did not respond within 5 seconds', result.stderr)
                self.assertNotIn('applied', result.stdout)

    @unittest.skipUnless(TIMEOUT, 'requires the Linux timeout utility')
    def test_unresponsive_dbus_is_killed_even_if_it_ignores_term(self):
        (self.bin / 'timeout').unlink()
        (self.bin / 'timeout').symlink_to(TIMEOUT)
        self.dbus_script('signal.signal(signal.SIGTERM, signal.SIG_IGN)\ntime.sleep(12)')
        started = time.monotonic()
        result = self.run_module(DISPLAY=':0')
        elapsed = time.monotonic() - started
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn('KDE Plasma did not respond within 5 seconds', result.stderr)
        self.assertTrue(self.calls.exists())
        self.assertGreaterEqual(elapsed, 5)
        self.assertLess(elapsed, 9)


if __name__ == '__main__':
    unittest.main()
