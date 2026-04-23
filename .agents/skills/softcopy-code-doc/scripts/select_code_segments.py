#!/usr/bin/env python3

from __future__ import annotations

import argparse
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

from softcopy_support import load_if_exists_json, load_if_exists_yaml, write_yaml


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=str(ROOT))
    args = parser.parse_args()
    repo_root = Path(args.repo_root).resolve()

    repo_scan = load_if_exists_json(repo_root / "softcopy" / "outputs" / "scan" / "repo_scan.json", {})
    feature_map = load_if_exists_yaml(repo_root / "softcopy" / "feature_map.yaml", {})
    selected = repo_scan.get("candidate_core_files", [])[:10]
    payload = {
        "selection_status": "pending_review",
        "feature_map_review_status": feature_map.get("review_status", "pending_review"),
        "selected_files": selected,
    }
    write_yaml(repo_root / "softcopy" / "outputs" / "code_doc" / "code_selection.yaml", payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

