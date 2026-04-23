#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
from pathlib import Path

from scan_repo import scan_repository


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=".")
    args = parser.parse_args()
    repo_root = Path(args.repo_root).resolve()
    repo_scan = scan_repository(repo_root)["repo_scan"]
    print(json.dumps(repo_scan["detected_routes"], ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

