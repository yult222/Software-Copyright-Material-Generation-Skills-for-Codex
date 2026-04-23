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

from softcopy_support import load_if_exists_yaml, write_text, write_yaml


def infer_doc_type(project_facts: dict) -> str:
    facts = project_facts.get("facts", {})
    project_type = facts.get("project_type", {}).get("value", "")
    has_gui = project_facts.get("profile", {}).get("has_gui", {}).get("value", False)
    has_backend_api = project_facts.get("profile", {}).get("has_backend_api", {}).get("value", False)
    if has_gui and has_backend_api:
        return "hybrid"
    if has_gui:
        return "user_manual"
    if project_type in {"cli_tool", "sdk", "algorithm_library"}:
        return "design_spec"
    return "api_manual"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=str(ROOT))
    args = parser.parse_args()
    repo_root = Path(args.repo_root).resolve()

    project_facts = load_if_exists_yaml(repo_root / "softcopy" / "project_facts.yaml", {})
    feature_map = load_if_exists_yaml(repo_root / "softcopy" / "feature_map.yaml", {})

    sections = []
    for index, feature in enumerate(feature_map.get("features", []), start=1):
        section_id = f"SEC-{index:03d}"
        title = feature.get("name", {}).get("value") or f"功能 {index}"
        sections.append(
            {
                "section_id": section_id,
                "title": title,
                "goal": f"说明 {title} 的使用方式。",
                "prerequisites": [],
                "steps": [],
                "expected_result": "",
                "screenshot_ids": [],
                "notes": [],
            }
        )

    stub = {
        "manifest_status": "pending_review",
        "doc_type": infer_doc_type(project_facts),
        "sections": sections,
        "screenshots": [],
    }
    outputs_root = repo_root / "softcopy" / "outputs" / "manual"
    write_yaml(outputs_root / "manual_manifest.stub.yaml", stub)
    outline = ["# Manual Outline", "", f"- doc_type: `{stub['doc_type']}`", "", "## Sections"]
    outline.extend(f"- `{item['section_id']}` {item['title']}" for item in sections)
    if not sections:
        outline.append("- None")
    write_text(outputs_root / "manual_outline.md", "\n".join(outline) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

