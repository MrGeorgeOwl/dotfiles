#!/usr/bin/env bash
set -euo pipefail

usage() {
  printf 'Usage: %s [theme]\n' "${0##*/}" >&2
  printf 'Build config.toml using a theme from themes/. Defaults to solarized-light.\n' >&2
}

if (($# > 1)); then
  usage
  exit 1
fi

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
theme="${1:-solarized-light}"
base_file="$script_dir/base.toml"
theme_file="$script_dir/themes/$theme.toml"
config_file="$script_dir/config.toml"

if [[ ! -f "$base_file" ]]; then
  printf 'Missing base configuration: %s\n' "$base_file" >&2
  exit 1
fi

if [[ ! -f "$theme_file" ]]; then
  printf 'Unknown Herdr theme: %s\n' "$theme" >&2
  exit 1
fi

temp_file="$(mktemp "$script_dir/.config.toml.XXXXXX")"
trap 'rm -f "$temp_file"' EXIT

{
  cat "$base_file"
  printf '\n[theme]\n'
  cat "$theme_file"
} > "$temp_file"

mv "$temp_file" "$config_file"
trap - EXIT
printf 'Built %s with theme %s\n' "$config_file" "$theme"
