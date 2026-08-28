#!/usr/bin/env sh

CHAMELEON_SKIP=10
CHAMELEON_CONFIG_DIR="$HOME/.config/chameleon"
: "${CHAMELEON_VERBOSE:=0}"

is_verbose() {
  [ "$CHAMELEON_VERBOSE" = "1" ]
}

log_info() {
  is_verbose || return 0
  printf '%s\n' "$1"
}

log_warn() {
  is_verbose || return 0
  printf '%s\n' "$1" >&2
}

log_error() {
  printf '%s\n' "$1" >&2
}

fail_module() {
  log_error "$1"
  return 1
}

skip_module() {
  log_warn "$1"
  return "$CHAMELEON_SKIP"
}

is_linux() {
  [ "$(uname -s)" = "Linux" ]
}

is_macos() {
  [ "$(uname -s)" = "Darwin" ]
}

is_safe_name() {
  case "$1" in
    ""|*[!A-Za-z0-9._-]*) return 1 ;;
  esac

  return 0
}

theme_file_for() {
  theme="$1"
  is_safe_name "$theme" || return 1
  printf '%s/themes/%s.conf\n' "$CHAMELEON_CONFIG_DIR" "$theme"
}

theme_exists() {
  theme_file="$(theme_file_for "$1")" || return 1
  [ -f "$theme_file" ]
}

# Read the first exact key=value mapping from a theme definition. Values are
# plain text; they are never evaluated as shell code.
theme_value() {
  mapping_key="$1"
  theme_file="$(theme_file_for "$2")" || return 1
  [ -f "$theme_file" ] || return 1

  awk -v wanted_key="$mapping_key" '
    {
      line = $0
      sub(/\r$/, "", line)
      if (line ~ /^[[:space:]]*($|#)/) {
        next
      }

      separator = index(line, "=")
      if (!separator) {
        next
      }

      key = substr(line, 1, separator - 1)
      sub(/^[[:space:]]+/, "", key)
      sub(/[[:space:]]+$/, "", key)
      if (key != wanted_key) {
        next
      }

      value = substr(line, separator + 1)
      sub(/^[[:space:]]+/, "", value)
      sub(/[[:space:]]+$/, "", value)
      print value
      found = 1
      exit
    }
    END {
      exit(found ? 0 : 1)
    }
  ' "$theme_file"
}

list_theme_names() {
  for theme_file in "$CHAMELEON_CONFIG_DIR"/themes/*.conf; do
    [ -f "$theme_file" ] || continue
    theme_name="${theme_file##*/}"
    theme_name="${theme_name%.conf}"
    is_safe_name "$theme_name" || continue
    printf '%s\n' "$theme_name"
  done
}

atomic_write_line() {
  target="$1"
  value="$2"
  target_dir="${target%/*}"
  target_name="${target##*/}"

  [ -d "$target_dir" ] || return 1

  temporary_file="$(mktemp "$target_dir/.${target_name}.XXXXXX")" || return 1
  if ! printf '%s\n' "$value" > "$temporary_file"; then
    rm -f "$temporary_file"
    return 1
  fi

  if ! mv -f "$temporary_file" "$target"; then
    rm -f "$temporary_file"
    return 1
  fi
}

atomic_copy() {
  source_file="$1"
  target="$2"
  target_dir="${target%/*}"
  target_name="${target##*/}"

  [ -d "$target_dir" ] || return 1

  temporary_file="$(mktemp "$target_dir/.${target_name}.XXXXXX")" || return 1
  if ! cp "$source_file" "$temporary_file"; then
    rm -f "$temporary_file"
    return 1
  fi

  if ! mv -f "$temporary_file" "$target"; then
    rm -f "$temporary_file"
    return 1
  fi
}
