#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
from pathlib import Path

from scan_repo import iter_source_files, count_effective_lines


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=".")
    args = parser.parse_args()
    repo_root = Path(args.repo_root).resolve()
    files = iter_source_files(repo_root)
    payload = {
        str(path.relative_to(repo_root)): count_effective_lines(path)
        for path in files
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

