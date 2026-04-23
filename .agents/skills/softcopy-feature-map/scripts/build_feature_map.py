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

from softcopy_support import load_if_exists_json, load_if_exists_yaml, write_text, write_yaml


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=str(ROOT))
    args = parser.parse_args()
    repo_root = Path(args.repo_root).resolve()

    module_candidates = load_if_exists_yaml(repo_root / "softcopy" / "outputs" / "scan" / "module_candidates.yaml", {"modules": []})
    route_inventory = load_if_exists_json(repo_root / "softcopy" / "outputs" / "scan" / "repo_scan.json", {})
    routes = route_inventory.get("detected_routes", [])

    features = []
    for index, module in enumerate(module_candidates.get("modules", [])[:10], start=1):
        feature_id = f"FEAT-{index:03d}"
        name = module.get("name", f"模块 {index}")
        module_routes = [item["route"] for item in routes if item["file"] in module.get("paths", [])][:5]
        features.append(
            {
                "feature_id": feature_id,
                "review_status": "pending_review",
                "name": {
                    "value": name,
                    "status": "derived",
                    "blocking": False,
                    "owner_skill": "softcopy-feature-map",
                    "sources": [
                        {
                            "source_type": "repo_scan",
                            "source_ref": "softcopy/outputs/scan/module_candidates.yaml#/modules",
                            "authority_level": "B",
                            "confidence": 0.6,
                        }
                    ],
                },
                "summary": {
                    "value": f"Candidate feature derived from module {name}.",
                    "status": "derived",
                    "blocking": False,
                    "owner_skill": "softcopy-feature-map",
                    "sources": [
                        {
                            "source_type": "repo_scan",
                            "source_ref": "softcopy/outputs/scan/module_candidates.yaml#/modules",
                            "authority_level": "B",
                            "confidence": 0.6,
                        }
                    ],
                },
                "priority": "medium",
                "source_paths": module.get("paths", []),
                "routes_or_commands": module_routes,
                "ui_pages": [],
                "api_groups": [],
                "manual_sections": [f"SEC-{index:03d}"],
                "screenshot_ids": [],
                "application_claims": [f"Provide {name} related capability."],
            }
        )

    payload = {"review_status": "pending_review", "features": features}
    write_yaml(repo_root / "softcopy" / "feature_map.yaml", payload)
    report = ["# Feature Map Report", "", "- review_status: `pending_review`", "", "## Proposed features"]
    report.extend(f"- `{item['feature_id']}` {item['name']['value']}" for item in features)
    if not features:
        report.append("- None")
    write_text(repo_root / "softcopy" / "outputs" / "feature_map" / "feature_map_report.md", "\n".join(report) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

