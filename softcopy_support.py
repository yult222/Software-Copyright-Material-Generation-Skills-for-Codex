#!/usr/bin/env python3

"""Backward-compatible imports for older skill scripts."""

from pathlib import Path

from softcopy_tool.support import (  # noqa: F401
    REPO_ROOT,
    ensure_parent,
    load_json as load_if_exists_json,
    load_yaml as load_if_exists_yaml,
    read_json,
    read_yaml,
    write_csv,
    write_json,
    write_text,
    write_yaml,
)


def repo_root() -> Path:
    return REPO_ROOT
