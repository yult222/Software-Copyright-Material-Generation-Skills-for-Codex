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

from softcopy_support import load_if_exists_yaml, write_json, write_text


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=str(ROOT))
    args = parser.parse_args()
    repo_root = Path(args.repo_root).resolve()

    selection = load_if_exists_yaml(repo_root / "softcopy" / "outputs" / "code_doc" / "code_selection.yaml", {})
    selected_files = selection.get("selected_files", [])

    lines = ["# Source Code Evidence", "", "## File Selection Summary"]
    page_trace = []
    for index, item in enumerate(selected_files, start=1):
        lines.append(f"- `{item.get('path', '')}` ({item.get('effective_code_lines', 0)} lines)")
        page_trace.append(
            {
                "page": index,
                "path": item.get("path", ""),
                "sources": [
                    {
                        "source_type": "repo_scan",
                        "source_ref": "softcopy/outputs/scan/repo_scan.json#/candidate_core_files",
                        "authority_level": "B",
                        "confidence": 0.8,
                    }
                ],
            }
        )
    if not selected_files:
        lines.append("- None")

    lines.extend(["", "## Paginated Source Code", "Generated pagination placeholder only."])
    lines.extend(["", "## Page Trace Notes", "- See `page_trace.json`."])

    outputs_root = repo_root / "softcopy" / "outputs" / "code_doc"
    write_text(outputs_root / "code_doc.md", "\n".join(lines) + "\n")
    write_text(outputs_root / "code_doc_report.md", "# Code Doc Report\n\n- Generated placeholder code document from current selection.\n")
    write_json(outputs_root / "page_trace.json", {"pages": page_trace})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

