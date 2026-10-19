"""Run with: python3 -m unittest discover -s .local/bin/chameleon/tests -v

Uses temporary HOME/configs and mock theme commands; never switches appearance.
"""
import os
from pathlib import Path
import platform
import plistlib
import shutil
import subprocess
import tempfile
import time
import unittest

ROOT = Path(__file__).resolve().parents[1]


class WatchCLI(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name)
        self.bin = self.home / 'bin'
        self.bin.mkdir()
        self.env = dict(os.environ, HOME=str(self.home),
                        PATH=f'{self.bin}:{os.environ["PATH"]}')
        self.script('uname', 'echo Darwin')
        self.script('launchctl', 'exit 0')
        themes = self.home / '.config/chameleon/themes'
        themes.mkdir(parents=True)
        for theme in ['light', 'dark']:
            (themes / f'{theme}.conf').write_text('')
        cache = self.home / 'Library/Caches/chameleon'
        cache.mkdir(parents=True)
        binary = cache / 'appearance-watcher'
        binary.write_text('#!/bin/sh\nexit 0\n')
        binary.chmod(0o700)
        # Prevent compiler use in CLI tests, independent of checkout timestamps.
        future = time.time() + 3600
        os.utime(binary, (future, future))

    def script(self, name, body):
        target = self.bin / name
        target.write_text('#!/bin/sh\n' + body + '\n')
        target.chmod(0o700)

    def run_cli(self, *args):
        return subprocess.run([str(ROOT / 'chameleon'), 'watch', *args],
                              env=self.env, capture_output=True, text=True)

    def test_linux_is_explicitly_unsupported(self):
        self.script('uname', 'echo Linux')
        result = self.run_cli('light', 'dark')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('not supported on Linux', result.stderr)

    def test_validation(self):
        self.assertEqual(self.run_cli('--help').returncode, 0)
        self.assertEqual(self.run_cli().returncode, 2)
        self.assertEqual(self.run_cli('missing', 'dark').returncode, 2)
        self.assertEqual(self.run_cli('../light', 'dark').returncode, 2)

    def test_ghostty_reload_does_not_activate_terminal(self):
        self.script('pgrep', 'exit 0')
        self.script('osascript', 'printf "%s" "$2" > "$TEST_APPLESCRIPT"')
        theme = self.home / '.config/chameleon/themes/light.conf'
        theme.write_text('ghostty=light\n')
        themes = self.home / '.config/ghostty/themes'
        themes.mkdir(parents=True)
        (themes / 'light').write_text('background = #ffffff\n')
        script = self.home / 'reload.applescript'
        result = subprocess.run([str(ROOT / 'modules/ghostty'), 'apply', 'light'],
                                env=dict(self.env, CHAMELEON_ROOT=str(ROOT),
                                         XDG_CONFIG_HOME=str(self.home / '.config'),
                                         TEST_APPLESCRIPT=str(script)),
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((themes / 'current').read_text(), (themes / 'light').read_text())
        reload = script.read_text()
        self.assertIn('click menu item "Reload Configuration"', reload)
        self.assertNotIn('frontmost', reload)
        self.assertNotIn('keystroke', reload)

    def test_follow_mode_skips_only_desktop(self):
        root = self.home / 'chameleon'
        (root / 'lib').mkdir(parents=True)
        (root / 'modules').mkdir()
        shutil.copy2(ROOT / 'chameleon', root / 'chameleon')
        shutil.copy2(ROOT / 'lib/common.sh', root / 'lib/common.sh')
        events = self.home / 'modules.log'
        names = ['ghostty', 'btop', 'nvim', 'herdr', 'claude', 'grok',
                 'desktop', 'wallpaper']
        for name in names:
            module = root / 'modules' / name
            module.write_text(f'#!/bin/sh\necho {name} >> "{events}"\n')
            module.chmod(0o700)
        result = subprocess.run([str(root / 'chameleon'), 'light'],
                                env=dict(self.env, CHAMELEON_FOLLOW_APPEARANCE='1'),
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(events.read_text().splitlines(),
                         [name for name in names if name != 'desktop'])
        current = self.home / '.config/chameleon/current'
        self.assertEqual(current.read_text(), 'light\n')
        events.unlink()
        subprocess.run([str(root / 'chameleon'), 'dark'], env=self.env, check=True)
        self.assertEqual(events.read_text().splitlines(), names)

    def test_install_and_uninstall(self):
        result = self.run_cli('--install', 'light', 'dark')
        self.assertEqual(result.returncode, 0, result.stderr)
        agent = self.home / 'Library/LaunchAgents/local.chameleon.appearance.plist'
        with agent.open('rb') as stream:
            config = plistlib.load(stream)
        self.assertEqual(config['ProgramArguments'],
                         [str(ROOT / 'chameleon'), 'watch', 'light', 'dark'])
        self.assertTrue(config['KeepAlive'])
        self.assertEqual(config['EnvironmentVariables']['PATH'], self.env['PATH'])
        result = self.run_cli('--uninstall')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(agent.exists())


@unittest.skipUnless(platform.system() == 'Darwin', 'macOS listener')
class MacListener(unittest.TestCase):
    def test_appkit_observation_without_distributed_notifications(self):
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary)
            source = (ROOT / 'lib/appearance-watcher.swift').read_text()
            # Override only this test application's appearance, never the system.
            source = source.replace('application.run()', '''
application.appearance = NSAppearance(named: .aqua)
DispatchQueue.main.asyncAfter(deadline: .now() + 0.7) {
    application.appearance = NSAppearance(named: .darkAqua)
}
DispatchQueue.main.asyncAfter(deadline: .now() + 1.4) {
    application.appearance = NSAppearance(named: .aqua)
}
application.run()
''')
            (folder / 'test.swift').write_text(source)
            binary = folder / 'watch'
            subprocess.run(['xcrun', 'swiftc', str(folder / 'test.swift'),
                            '-o', str(binary)], check=True)
            events = folder / 'events'
            command = folder / 'apply'
            command.write_text(f'#!/bin/sh\necho "$3" >> "{events}"\n')
            command.chmod(0o700)
            process = subprocess.Popen([str(binary), str(command), 'day', 'night',
                                        str(folder / 'lock')],
                                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            try:
                deadline = time.monotonic() + 8
                while time.monotonic() < deadline:
                    if events.exists() and len(events.read_text().splitlines()) == 3:
                        break
                    time.sleep(0.05)
                self.assertTrue(events.exists())
                self.assertEqual(events.read_text().splitlines(), ['day', 'night', 'day'])
            finally:
                process.terminate()
                process.wait(timeout=5)

    def test_notifications_serialization_and_lock(self):
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary)
            source = (ROOT / 'lib/appearance-watcher.swift').read_text()
            # Compile production code first, including the real AppKit reader.
            subprocess.run(['xcrun', 'swiftc', str(ROOT / 'lib/appearance-watcher.swift'),
                            '-o', str(folder / 'production')], check=True)
            # Replace only the preference reader to simulate transitions without
            # changing this machine's appearance. Notification handling is real.
            start = source.index('    func appearance() -> String {')
            end = source.index('    func applyLatest()', start)
            reader = '''    func appearance() -> String {
        return try! String(contentsOfFile: ProcessInfo.processInfo.environment["TEST_STATE"]!,
                           encoding: .utf8)
    }

'''
            source = source[:start] + reader + source[end:]
            # Reproduce background delivery: System Settings need not force
            # immediate delivery, unlike the old test's synthetic notifications.
            source = source.replace('    watcher.start()',
                                    '    DistributedNotificationCenter.default().suspended = true\n'
                                    '    watcher.start()')
            (folder / 'watch.swift').write_text(source)
            (folder / 'post.swift').write_text('''import Foundation
DistributedNotificationCenter.default().postNotificationName(
    Notification.Name("AppleInterfaceThemeChangedNotification"),
    object: nil, userInfo: nil, deliverImmediately: false)
''')
            for name in ['watch', 'post']:
                subprocess.run(['xcrun', 'swiftc', str(folder / f'{name}.swift'),
                                '-o', str(folder / name)], check=True)
            state = folder / 'state'
            state.write_text('light')
            events = folder / 'events'
            command = folder / 'apply'
            command.write_text(f'''#!/bin/sh
printf 'start %s %s\\n' "$3" "$CHAMELEON_FOLLOW_APPEARANCE" >> '{events}'
sleep 1
printf 'end %s\\n' "$3" >> '{events}'
''')
            command.chmod(0o700)
            arguments = [str(folder / 'watch'), str(command), 'day', 'night',
                         str(folder / 'lock')]
            with (folder / 'log').open('w') as log:
                process = subprocess.Popen(arguments, env=dict(os.environ, TEST_STATE=str(state)),
                                           stdout=log, stderr=log)
                try:
                    def wait_for(text):
                        deadline = time.monotonic() + 8
                        while time.monotonic() < deadline:
                            if events.exists() and text in events.read_text():
                                return
                            time.sleep(0.05)
                        self.fail(f'timed out waiting for {text}: {(folder / "log").read_text()}')

                    def notify():
                        subprocess.run([str(folder / 'post')], check=True)

                    wait_for('start day 1')
                    duplicate = subprocess.run(arguments, capture_output=True)
                    self.assertNotEqual(duplicate.returncode, 0)
                    # Duplicate Light notification must not reapply the theme.
                    notify()
                    time.sleep(0.4)
                    # Dark arrives while Light is still applying; it must wait.
                    state.write_text('dark')
                    notify()
                    wait_for('end night')
                    notify()
                    time.sleep(0.5)
                    self.assertEqual(events.read_text().splitlines(),
                                     ['start day 1', 'end day', 'start night 1', 'end night'])
                    state.write_text('light')
                    notify()
                    wait_for('end day\nstart night 1\nend night\nstart day 1\nend day')
                finally:
                    process.terminate()
                    process.wait(timeout=5)


if __name__ == '__main__':
    unittest.main()
