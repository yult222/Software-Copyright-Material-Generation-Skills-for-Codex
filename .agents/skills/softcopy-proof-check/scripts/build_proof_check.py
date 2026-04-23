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


DOCUMENTS_BY_MODE = {
    "independent": [
        {"doc_id": "PROOF-001", "name": "Identity or organization proof", "required": True},
        {"doc_id": "PROOF-002", "name": "Task assignment or project proof", "required": False},
    ],
    "cooperative": [
        {"doc_id": "PROOF-001", "name": "Identity or organization proof", "required": True},
        {"doc_id": "PROOF-003", "name": "Cooperative development agreement", "required": True},
    ],
    "entrusted": [
        {"doc_id": "PROOF-001", "name": "Identity or organization proof", "required": True},
        {"doc_id": "PROOF-004", "name": "Entrusted development agreement", "required": True},
    ],
    "employee": [
        {"doc_id": "PROOF-001", "name": "Identity or organization proof", "required": True},
        {"doc_id": "PROOF-005", "name": "Internal duty development proof", "required": True},
    ],
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=str(ROOT))
    args = parser.parse_args()
    repo_root = Path(args.repo_root).resolve()

    project_facts = load_if_exists_yaml(repo_root / "softcopy" / "project_facts.yaml", {})
    development_mode = project_facts.get("facts", {}).get("development_mode", {}).get("value", "")
    normalized_mode = development_mode if development_mode in DOCUMENTS_BY_MODE else "independent"

    required_documents = []
    for item in DOCUMENTS_BY_MODE[normalized_mode]:
        required_documents.append({**item, "provided": False, "file_ref": ""})

    payload = {
        "evidence_status": "pending_review",
        "development_mode": development_mode,
        "required_documents": required_documents,
        "notes": "",
    }
    write_yaml(repo_root / "softcopy" / "ownership_evidence.yaml", payload)

    checklist = ["# Proof Checklist", "", f"- development_mode: `{development_mode or 'unknown'}`", "", "## Required documents"]
    missing = ["# Missing Proofs", ""]
    for item in required_documents:
        marker = "[ ]" if item["required"] else "[-]"
        checklist.append(f"- {marker} `{item['doc_id']}` {item['name']}")
        if item["required"]:
            missing.append(f"- `{item['doc_id']}` {item['name']}")
    if len(required_documents) == 0:
        checklist.append("- None")
        missing.append("- None")

    outputs_root = repo_root / "softcopy" / "outputs" / "proof_check"
    write_text(outputs_root / "proof_checklist.md", "\n".join(checklist) + "\n")
    write_text(outputs_root / "missing_proofs.md", "\n".join(missing) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
