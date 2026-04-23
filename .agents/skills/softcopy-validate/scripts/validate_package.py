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

from check_consistency import (
    validate_application_alignment,
    validate_formal_dependencies,
    validate_ownership,
    validate_required_facts,
    validate_traceability,
)
from check_page_rules import active_rules, evaluate_page_rules
from softcopy_support import load_if_exists_json, load_if_exists_yaml, write_json, write_text


def render_validation_report(summary: dict, errors: list[dict], warnings: list[dict], infos: list[dict]) -> str:
    lines = [
        "# Validation Report",
        "",
        "## Summary",
        f"- Errors: {len(errors)}",
        f"- Warnings: {len(warnings)}",
        f"- Infos: {len(infos)}",
        f"- Submission readiness: `{summary['submission_readiness']}`",
        "",
        "## Activated Rules",
    ]
    if summary["activated_rules"]:
        lines.extend(f"- `{rule_id}`" for rule_id in summary["activated_rules"])
    else:
        lines.append("- None")

    lines.extend(["", "## Errors"])
    if errors:
        lines.extend(f"- `{item['code']}`: {item['message']} ({item['path']})" for item in errors)
    else:
        lines.append("- None")

    lines.extend(["", "## Warnings"])
    if warnings:
        lines.extend(f"- `{item['code']}`: {item['message']} ({item['path']})" for item in warnings)
    else:
        lines.append("- None")

    lines.extend(["", "## Informational Notes"])
    if infos:
        lines.extend(f"- `{item['code']}`: {item['message']} ({item['path']})" for item in infos)
    else:
        lines.append("- None")

    lines.extend(
        [
            "",
            "## Traceability Gaps",
            *(
                f"- `{item['code']}`: {item['message']} ({item['path']})"
                for item in errors
                if item["code"] in {"traceability_missing_source", "main_function_not_traceable"}
            ),
        ]
    )
    if not any(item["code"] in {"traceability_missing_source", "main_function_not_traceable"} for item in errors):
        lines.append("- None")

    lines.extend(
        [
            "",
            "## Submission Readiness Conclusion",
            f"- `{summary['submission_readiness']}`",
            "",
            "## Required Next Fixes",
        ]
    )
    if errors:
        lines.extend(f"- {item['message']}" for item in errors)
    else:
        lines.append("- None")
    return "\n".join(lines) + "\n"


def render_traceability_report(project_facts: dict, application_fields: dict, errors: list[dict]) -> str:
    facts = project_facts.get("facts", {})
    lines = [
        "# Traceability Report",
        "",
        "## Scope of Traced Artifacts",
        "- project facts",
        "- application fields",
        "",
        "## Blocking Facts and Their Sources",
    ]

    blocking_found = False
    for field, value in facts.items():
        if isinstance(value, dict) and value.get("blocking"):
            blocking_found = True
            source_refs = [item.get("source_ref", "") for item in value.get("sources", [])]
            lines.append(f"- `{field}` ({value.get('status', 'missing')}): {', '.join(source_refs) if source_refs else 'NO_SOURCE'}")
    if not blocking_found:
        lines.append("- None")

    lines.extend(["", "## Application Field Traces"])
    for field, value in application_fields.items():
        if isinstance(value, dict) and "sources" in value:
            source_refs = [item.get("source_ref", "") for item in value.get("sources", [])]
            lines.append(f"- `{field}`: {', '.join(source_refs) if source_refs else 'NO_SOURCE'}")
    if not any(isinstance(value, dict) and "sources" in value for value in application_fields.values()):
        lines.append("- None")

    lines.extend(["", "## Code Page Traces", "- Not generated in current run."])
    lines.extend(["", "## Manual Section and Screenshot Traces", "- Not generated in current run."])
    lines.extend(["", "## Unresolved Trace Gaps"])

    trace_errors = [item for item in errors if item["code"] in {"traceability_missing_source", "main_function_not_traceable"}]
    if trace_errors:
        lines.extend(f"- `{item['code']}`: {item['message']}" for item in trace_errors)
    else:
        lines.append("- None")

    lines.extend(["", "## Final Traceability Conclusion"])
    if trace_errors:
        lines.append("- Traceability incomplete.")
    else:
        lines.append("- Traceability complete for currently generated artifacts.")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=str(ROOT))
    args = parser.parse_args()
    repo_root = Path(args.repo_root).resolve()

    project_facts = load_if_exists_yaml(repo_root / "softcopy" / "project_facts.yaml", {})
    required_facts = load_if_exists_yaml(repo_root / "softcopy" / "contracts" / "required_facts.yaml", {})
    feature_map = load_if_exists_yaml(repo_root / "softcopy" / "feature_map.yaml", {})
    manual_manifest = load_if_exists_yaml(repo_root / "softcopy" / "manual_manifest.yaml", {})
    ownership_evidence = load_if_exists_yaml(repo_root / "softcopy" / "ownership_evidence.yaml", {})
    application_fields = load_if_exists_json(repo_root / "softcopy" / "outputs" / "application" / "application_fields.json", {})
    registration_rules = load_if_exists_yaml(repo_root / "softcopy" / "rules" / "registration_rules.yaml", {})

    errors = []
    warnings = []
    infos = []

    errors.extend(validate_required_facts(project_facts, required_facts))
    if application_fields:
        errors.extend(validate_application_alignment(project_facts, application_fields))
        errors.extend(validate_formal_dependencies(application_fields, feature_map, manual_manifest))
        trace_errors, trace_warnings = validate_traceability(application_fields)
        errors.extend(trace_errors)
        warnings.extend(trace_warnings)
    else:
        errors.append(
            {
                "code": "application_fields_missing",
                "message": "Application fields are missing.",
                "path": "softcopy/outputs/application/application_fields.json",
                "severity": "ERROR",
            }
        )
    errors.extend(validate_ownership(project_facts, ownership_evidence))

    active, rule_warnings, rule_infos = active_rules(registration_rules, project_facts.get("filing_context", {}))
    page_warnings, page_infos = evaluate_page_rules(active)
    warnings.extend(rule_warnings)
    warnings.extend(page_warnings)
    infos.extend(rule_infos)
    infos.extend(page_infos)

    validation_root = repo_root / "softcopy" / "outputs" / "validation"
    trace_root = repo_root / "softcopy" / "outputs" / "traceability"
    package_flag = repo_root / "softcopy" / "outputs" / "package" / "READY_TO_SUBMIT.flag"
    ready = not errors

    summary = {
        "submission_readiness": "ready_to_submit" if ready else "package_validation_failed",
        "activated_rules": [rule["rule_id"] for rule in active],
    }
    write_json(validation_root / "errors.json", errors)
    write_json(validation_root / "warnings.json", warnings)
    write_text(validation_root / "validation_report.md", render_validation_report(summary, errors, warnings, infos))
    write_text(trace_root / "traceability_report.md", render_traceability_report(project_facts, application_fields, errors))

    if ready:
        package_flag.parent.mkdir(parents=True, exist_ok=True)
        package_flag.write_text("READY_TO_SUBMIT\n", encoding="utf-8")
    elif package_flag.exists():
        package_flag.unlink()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

