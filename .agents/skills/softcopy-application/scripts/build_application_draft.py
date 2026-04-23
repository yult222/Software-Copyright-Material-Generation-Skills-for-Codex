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

from softcopy_support import load_if_exists_json, load_if_exists_yaml, write_json, write_text


CORE_FIELDS = [
    "software_name_full",
    "software_name_short",
    "version",
    "development_completion_date",
    "first_publication_status",
    "first_publication_date",
    "copyright_owner_type",
    "copyright_owners",
    "development_mode",
    "project_type",
]


def envelope(value, status, blocking, owner_skill, sources):
    return {
        "value": value,
        "status": status,
        "blocking": blocking,
        "owner_skill": owner_skill,
        "sources": sources,
        "last_updated_by": owner_skill,
    }


def clone_fact_field(name: str, facts: dict) -> dict:
    item = facts.get(name)
    if item is None:
        return envelope("" if name != "copyright_owners" else [], "missing", name != "software_name_short", "softcopy-application", [])
    cloned = dict(item)
    cloned["owner_skill"] = "softcopy-application"
    cloned["last_updated_by"] = "softcopy-application"
    return cloned


def determine_draft_mode(project_facts: dict, required_facts: dict, feature_map: dict) -> tuple[str, list[str]]:
    facts = project_facts.get("facts", {})
    needs_confirmation = []

    for item in required_facts.get("core_required_facts", []):
        field = item["field"]
        status = facts.get(field, {}).get("status", "missing")
        if status != "confirmed":
            needs_confirmation.append(field)

    publication_status = facts.get("first_publication_status", {})
    if publication_status.get("status") == "confirmed" and publication_status.get("value") == "published":
        publication_date_status = facts.get("first_publication_date", {}).get("status", "missing")
        if publication_date_status != "confirmed":
            needs_confirmation.append("first_publication_date")

    feature_ready = feature_map.get("review_status") == "approved"
    if needs_confirmation or not feature_ready:
        return "provisional", sorted(set(needs_confirmation))
    return "formal", []


def build_main_functions(feature_map: dict, repo_scan: dict) -> list[dict]:
    features = feature_map.get("features", [])
    if feature_map.get("review_status") == "approved" and features:
        results = []
        for feature in features:
            for claim in feature.get("application_claims", []):
                results.append(
                    envelope(
                        claim,
                        "derived",
                        False,
                        "softcopy-application",
                        [
                            {
                                "source_type": "feature_map",
                                "source_ref": f"softcopy/feature_map.yaml#/features/{feature.get('feature_id', 'unknown')}",
                                "authority_level": "B",
                                "confidence": 0.9,
                            }
                        ],
                    )
                )
        return results

    results = []
    for module in repo_scan.get("candidate_modules", [])[:5]:
        results.append(
            envelope(
                f"Candidate module: {module['name']}",
                "candidate",
                False,
                "softcopy-application",
                [
                    {
                        "source_type": "repo_scan",
                        "source_ref": "softcopy/outputs/scan/repo_scan.json#/candidate_modules",
                        "authority_level": "B",
                        "confidence": 0.5,
                    }
                ],
            )
        )
    return results


def build_runtime_environment(project_facts: dict) -> dict:
    profile = project_facts.get("profile", {})
    runtime = profile.get("runtime_environment", {})
    return runtime.get("value", {}) if isinstance(runtime, dict) else {}


def build_application_trace(application_fields: dict) -> dict:
    trace = {"draft_mode": application_fields["draft_mode"], "fields": {}}
    for key, value in application_fields.items():
        if isinstance(value, dict) and "sources" in value:
            trace["fields"][key] = {
                "status": value.get("status"),
                "sources": value.get("sources", []),
            }
    trace["main_functions"] = [
        {"value": item.get("value"), "sources": item.get("sources", [])}
        for item in application_fields.get("main_functions", [])
    ]
    return trace


def render_markdown(application_fields: dict) -> str:
    lines = [
        "# Application Draft",
        "",
        f"- Draft mode: `{application_fields['draft_mode']}`",
        "",
        "## Basic Information",
    ]
    for field in CORE_FIELDS:
        value = application_fields[field]["value"]
        status = application_fields[field]["status"]
        lines.append(f"- `{field}`: `{value}` (status: `{status}`)")

    lines.extend(["", "## Main Functions Summary"])
    if application_fields["main_functions"]:
        for item in application_fields["main_functions"]:
            lines.append(f"- {item['value']} (status: `{item['status']}`)")
    else:
        lines.append("- None")

    lines.extend(["", "## Technical Characteristics Summary"])
    for item in application_fields.get("technical_highlights", []):
        lines.append(f"- {item}")
    if not application_fields.get("technical_highlights"):
        lines.append("- None")

    lines.extend(["", "## Runtime and Deployment Environment"])
    runtime_environment = application_fields.get("runtime_environment", {})
    if runtime_environment:
        for key, value in runtime_environment.items():
            lines.append(f"- `{key}`: {value}")
    else:
        lines.append("- None")

    lines.extend(["", "## Facts Needing Confirmation"])
    if application_fields["needs_confirmation"]:
        for field in application_fields["needs_confirmation"]:
            lines.append(f"- `{field}`")
    else:
        lines.append("- None")

    lines.extend(["", "## Traceability Notes", "- See `application_trace.json`."])
    return "\n".join(lines) + "\n"


def render_checklist(application_fields: dict) -> str:
    lines = [
        "# Application Review Checklist",
        "",
        f"- [ ] Draft mode `{application_fields['draft_mode']}` is expected",
        "- [ ] software name consistency",
        "- [ ] version consistency",
        "- [ ] owner consistency",
        "- [ ] development mode consistency",
        "- [ ] function wording supported by evidence",
        "- [ ] no exaggerated or unsupported claims",
    ]
    if application_fields["needs_confirmation"]:
        lines.extend(["", "## Remaining confirmations"])
        lines.extend(f"- [ ] `{field}`" for field in application_fields["needs_confirmation"])
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=str(ROOT))
    args = parser.parse_args()
    repo_root = Path(args.repo_root).resolve()

    project_facts = load_if_exists_yaml(repo_root / "softcopy" / "project_facts.yaml", {})
    required_facts = load_if_exists_yaml(repo_root / "softcopy" / "contracts" / "required_facts.yaml", {})
    feature_map = load_if_exists_yaml(repo_root / "softcopy" / "feature_map.yaml", {"review_status": "pending_review", "features": []})
    repo_scan = load_if_exists_json(repo_root / "softcopy" / "outputs" / "scan" / "repo_scan.json", {})

    draft_mode, needs_confirmation = determine_draft_mode(project_facts, required_facts, feature_map)
    facts = project_facts.get("facts", {})

    application_fields = {
        "draft_mode": draft_mode,
        "software_name_full": clone_fact_field("software_name_full", facts),
        "software_name_short": clone_fact_field("software_name_short", facts),
        "version": clone_fact_field("version", facts),
        "development_completion_date": clone_fact_field("development_completion_date", facts),
        "first_publication_status": clone_fact_field("first_publication_status", facts),
        "first_publication_date": clone_fact_field("first_publication_date", facts),
        "copyright_owner_type": clone_fact_field("copyright_owner_type", facts),
        "copyright_owners": clone_fact_field("copyright_owners", facts),
        "development_mode": clone_fact_field("development_mode", facts),
        "project_type": clone_fact_field("project_type", facts),
        "main_functions": build_main_functions(feature_map, repo_scan),
        "technical_highlights": project_facts.get("profile", {}).get("technical_highlights", {}).get("value", []),
        "runtime_environment": build_runtime_environment(project_facts),
        "needs_confirmation": needs_confirmation,
    }

    outputs_root = repo_root / "softcopy" / "outputs" / "application"
    write_json(outputs_root / "application_fields.json", application_fields)
    write_json(outputs_root / "application_trace.json", build_application_trace(application_fields))
    write_text(outputs_root / "application_draft.md", render_markdown(application_fields))
    write_text(outputs_root / "application_review_checklist.md", render_checklist(application_fields))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

