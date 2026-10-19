#!/usr/bin/env sh
set -eu

ROOT="$(CDPATH= cd "$(dirname "$0")/.." && pwd)"
. "$ROOT/lib/common.sh"

usage() {
  printf 'Usage: chameleon watch [--install] <light-theme> <dark-theme>\n       chameleon watch --uninstall\n'
}

case "${1:-}" in -h|--help) usage; exit 0 ;; esac
is_macos || { printf 'chameleon: watch requires macOS\n' >&2; exit 1; }

label=local.chameleon.appearance
agent="$HOME/Library/LaunchAgents/$label.plist"
domain="gui/$(id -u)"
mode=watch
case "${1:-}" in
  --install|--uninstall) mode="${1#--}"; shift ;;
esac
if [ "$mode" = uninstall ]; then
  [ "$#" -eq 0 ] || { usage >&2; exit 2; }
  launchctl bootout "$domain/$label" 2>/dev/null || true
  rm -f "$agent"
  printf 'Chameleon appearance watcher uninstalled.\n'
  exit 0
fi
[ "$#" -eq 2 ] || { usage >&2; exit 2; }
for theme in "$@"; do
  if ! is_safe_name "$theme" || ! theme_exists "$theme"; then
    printf 'chameleon: unknown theme: %s\n' "$theme" >&2
    exit 2
  fi
done

# Compile only when the source changes; no Swift interpreter/compiler stays running.
cache="$HOME/Library/Caches/chameleon"
mkdir -p "$cache"
binary="$cache/appearance-watcher"
source="$ROOT/lib/appearance-watcher.swift"
if [ ! -x "$binary" ] || [ "$source" -nt "$binary" ]; then
  temporary="$(mktemp -d "$cache/build.XXXXXX")"
  trap 'rm -rf "$temporary"' EXIT HUP INT TERM
  /usr/bin/xcrun swiftc "$source" -o "$temporary/appearance-watcher"
  mv -f "$temporary/appearance-watcher" "$binary"
  rm -rf "$temporary"
  trap - EXIT HUP INT TERM
fi

if [ "$mode" = install ]; then
  # plistlib handles spaces and XML metacharacters in paths and arguments.
  command -v python3 >/dev/null 2>&1 || {
    printf 'chameleon: installing the LaunchAgent requires python3\n' >&2; exit 1;
  }
  mkdir -p "$HOME/Library/LaunchAgents" "$HOME/Library/Logs/chameleon"
  python3 - "$agent" "$ROOT/chameleon" "$1" "$2" "$label" <<'PY'
import os
import plistlib
import sys
import tempfile

agent, command, light, dark, label = sys.argv[1:]
logs = os.path.expanduser('~/Library/Logs/chameleon')
config = {
    'Label': label,
    'ProgramArguments': [command, 'watch', light, dark],
    'RunAtLoad': True,
    'KeepAlive': True,
    'ThrottleInterval': 10,
    'EnvironmentVariables': {
        'PATH': os.environ.get('PATH', '/usr/bin:/bin:/usr/sbin:/sbin'),
    },
    'StandardOutPath': logs + '/watch.log',
    'StandardErrorPath': logs + '/watch.log',
}
fd, temporary = tempfile.mkstemp(dir=os.path.dirname(agent))
try:
    with os.fdopen(fd, 'wb') as stream:
        plistlib.dump(config, stream)
    os.replace(temporary, agent)
finally:
    if os.path.exists(temporary):
        os.unlink(temporary)
PY
  launchctl bootout "$domain/$label" 2>/dev/null || true
  launchctl enable "$domain/$label"
  launchctl bootstrap "$domain" "$agent"
  printf 'Chameleon appearance watcher installed: %s\n' "$agent"
  exit 0
fi

exec "$binary" "$ROOT/chameleon" "$1" "$2" "$cache/watch.lock"
