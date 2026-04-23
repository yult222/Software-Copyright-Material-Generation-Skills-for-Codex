#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
from pathlib import Path


def _repo_root() -> Path:
    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / "softcopy_support.py").exists():
            return parent
    raise RuntimeError("Repository root not found.")


ROOT = _repo_root()
import sys

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from softcopy_support import load_if_exists_yaml


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=str(ROOT))
    args = parser.parse_args()
    repo_root = Path(args.repo_root).resolve()

    selection = load_if_exists_yaml(repo_root / "softcopy" / "outputs" / "code_doc" / "code_selection.yaml", {})
    pages = []
    for index, item in enumerate(selection.get("selected_files", []), start=1):
        pages.append({"page": index, "path": item.get("path", ""), "reason": "Selected candidate core file"})
    print(json.dumps(pages, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

