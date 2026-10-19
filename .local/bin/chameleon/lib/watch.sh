#!/usr/bin/env sh
set -eu

# Each platform owns its appearance detection and background-service lifecycle.
# Keep dispatch here so future Linux support does not affect the macOS listener.
ROOT="$(CDPATH= cd "$(dirname "$0")/.." && pwd)"
case "$(uname -s)" in
  Darwin) exec "$ROOT/lib/watch-macos.sh" "$@" ;;
  *)
    printf 'chameleon: watch is not supported on %s yet (currently macOS only)\n' "$(uname -s)" >&2
    exit 1
    ;;
esac
