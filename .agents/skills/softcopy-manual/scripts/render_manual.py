#!/usr/bin/env python3

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def _root() -> Path:
    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / "softcopy_tool").exists():
            return parent
    raise RuntimeError("Repository root not found.")


sys.path.insert(0, str(_root()))
from softcopy_tool import workflow
from softcopy_tool.renderers import normalize_formats


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--formats", default="md")
    args = parser.parse_args()
    workflow.manual(Path(args.repo_root).resolve(), formats=normalize_formats(args.formats))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
