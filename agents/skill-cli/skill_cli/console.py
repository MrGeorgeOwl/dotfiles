"""Logging and CLI errors."""

from __future__ import annotations

import sys

PROG = "skill-cli"


class CliError(Exception):
    """Abort the command; main() prints and exits with code."""

    def __init__(self, msg: str, code: int = 1) -> None:
        super().__init__(msg)
        self.code = code


class FetchError(CliError):
    """External skill fetch or resolve failed; sync continues past these."""


def log(msg: str) -> None:
    print(f"{PROG}: {msg}")


def warn(msg: str) -> None:
    print(f"{PROG}: warning: {msg}", file=sys.stderr)
