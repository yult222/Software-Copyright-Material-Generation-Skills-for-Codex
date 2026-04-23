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

from softcopy_support import load_if_exists_json, load_if_exists_yaml, write_text


CORE_FIELDS = [
    "software_name_full",
    "version",
    "development_completion_date",
    "first_publication_status",
    "copyright_owner_type",
    "copyright_owners",
    "development_mode",
    "project_type",
]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=str(ROOT))
    args = parser.parse_args()
    repo_root = Path(args.repo_root).resolve()

    project_facts = load_if_exists_yaml(repo_root / "softcopy" / "project_facts.yaml", {})
    repo_scan = load_if_exists_json(repo_root / "softcopy" / "outputs" / "scan" / "repo_scan.json", {})
    facts = project_facts.get("facts", {})

    confirmed = []
    missing = []
    candidates = []
    conflicts = []

    for field in CORE_FIELDS:
        item = facts.get(field, {})
        status = item.get("status", "missing")
        value = item.get("value", "")
        if status == "confirmed":
            confirmed.append(f"- `{field}`: `{value}`")
        else:
            missing.append(f"- `{field}` (status: `{status}`)")

    repo_name = repo_root.name
    candidates.append(f"- Repository folder name: `{repo_name}`")
    if repo_scan:
        languages = repo_scan.get("primary_languages", [])
        if languages:
            candidates.append(f"- Detected primary languages: `{', '.join(languages)}`")
        entry_points = repo_scan.get("candidate_entry_points", [])
        if entry_points:
            candidates.append(f"- Candidate entry points: `{', '.join(entry_points[:5])}`")

    if facts.get("first_publication_status", {}).get("value") == "unpublished" and facts.get("first_publication_status", {}).get("status") != "confirmed":
        conflicts.append("- `first_publication_status` must not be set to `unpublished` before confirmation.")

    lines = [
        "# Intake Report",
        "",
        "## Overview",
        "- This report lists confirmed facts, missing required facts, candidate evidence, and conflicts.",
        "",
        "## Confirmed Facts",
        *(confirmed or ["- None"]),
        "",
        "## Missing Required Facts",
        *(missing or ["- None"]),
        "",
        "## Candidate Facts From Repository Evidence",
        *(candidates or ["- None"]),
        "",
        "## Conflicts To Resolve",
        *(conflicts or ["- None"]),
        "",
        "## Recommended Next Step",
        "- Confirm the missing core facts in `softcopy/project_facts.yaml` before attempting a formal draft.",
    ]
    write_text(repo_root / "softcopy" / "outputs" / "intake" / "intake_report.md", "\n".join(lines) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

