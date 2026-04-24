#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
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


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=".")
    args = parser.parse_args()
    repo_scan = workflow.scan(Path(args.repo_root).resolve())
    payload = {
        "primary_languages": repo_scan["primary_languages"],
        "framework_signals": repo_scan["framework_signals"],
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

