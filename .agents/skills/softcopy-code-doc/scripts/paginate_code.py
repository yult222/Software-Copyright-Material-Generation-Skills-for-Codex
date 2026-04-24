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
from softcopy_tool.support import load_yaml


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=".")
    args = parser.parse_args()
    repo_root = Path(args.repo_root).resolve()
    selection = load_yaml(repo_root / "softcopy" / "outputs" / "code_doc" / "code_selection.yaml", {})
    pages = [
        {"page": index, "path": item.get("path", ""), "reason": "Selected candidate core file"}
        for index, item in enumerate(selection.get("selected_files", []), start=1)
    ]
    print(json.dumps(pages, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

