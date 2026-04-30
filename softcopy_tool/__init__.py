"""SoftCopy Skill Pack command-line support."""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version


def _version() -> str:
    try:
        return version("softcopy-codex-skill-pack")
    except PackageNotFoundError:
        return "0+unknown"


__version__ = _version()
