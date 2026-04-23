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

from softcopy_support import load_if_exists_yaml, write_json, write_text, write_yaml


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=str(ROOT))
    args = parser.parse_args()
    repo_root = Path(args.repo_root).resolve()

    stub_path = repo_root / "softcopy" / "outputs" / "manual" / "manual_manifest.stub.yaml"
    manifest_path = repo_root / "softcopy" / "manual_manifest.yaml"
    manifest = load_if_exists_yaml(manifest_path, {})
    if not manifest.get("sections") and stub_path.exists():
        manifest = load_if_exists_yaml(stub_path, {})
        write_yaml(manifest_path, manifest)

    lines = ["# Manual", "", f"- manifest_status: `{manifest.get('manifest_status', 'pending_review')}`", "", "## Sections"]
    trace_sections = []
    for section in manifest.get("sections", []):
        lines.append(f"### {section.get('title', '')}")
        lines.append(f"- Goal: {section.get('goal', '')}")
        prerequisites = section.get("prerequisites", [])
        steps = section.get("steps", [])
        lines.append(f"- Prerequisites: {prerequisites or 'None'}")
        lines.append(f"- Steps: {steps or 'None'}")
        lines.append(f"- Expected result: {section.get('expected_result', '') or 'None'}")
        trace_sections.append(
            {
                "section_id": section.get("section_id", ""),
                "sources": [
                    {
                        "source_type": "manual_manifest",
                        "source_ref": f"softcopy/manual_manifest.yaml#/sections/{section.get('section_id', '')}",
                        "authority_level": "B",
                        "confidence": 0.9,
                    }
                ],
            }
        )
    if not manifest.get("sections"):
        lines.append("- None")

    outputs_root = repo_root / "softcopy" / "outputs" / "manual"
    write_text(outputs_root / "manual.md", "\n".join(lines) + "\n")
    write_text(outputs_root / "manual_report.md", "# Manual Report\n\n- Generated manual from current manifest.\n")
    write_json(outputs_root / "manual_trace.json", {"sections": trace_sections, "screenshots": manifest.get("screenshots", [])})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
