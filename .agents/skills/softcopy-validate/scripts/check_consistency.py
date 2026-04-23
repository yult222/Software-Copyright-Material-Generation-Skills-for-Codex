#!/usr/bin/env python3

from __future__ import annotations

from typing import Any


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


def error(code: str, message: str, path: str) -> dict[str, str]:
    return {"code": code, "message": message, "path": path, "severity": "ERROR"}


def warning(code: str, message: str, path: str) -> dict[str, str]:
    return {"code": code, "message": message, "path": path, "severity": "WARNING"}


def validate_required_facts(project_facts: dict[str, Any], required_facts: dict[str, Any]) -> list[dict[str, str]]:
    errors = []
    facts = project_facts.get("facts", {})

    for item in required_facts.get("core_required_facts", []):
        field = item["field"]
        status = facts.get(field, {}).get("status", "missing")
        if status != "confirmed":
            errors.append(
                error(
                    "core_required_fact_not_confirmed",
                    f"`{field}` must be confirmed before formal readiness.",
                    f"softcopy/project_facts.yaml#/facts/{field}",
                )
            )

    publication_status = facts.get("first_publication_status", {})
    if publication_status.get("status") == "confirmed" and publication_status.get("value") == "published":
        status = facts.get("first_publication_date", {}).get("status", "missing")
        if status != "confirmed":
            errors.append(
                error(
                    "conditional_required_fact_not_confirmed",
                    "`first_publication_date` must be confirmed when publication status is published.",
                    "softcopy/project_facts.yaml#/facts/first_publication_date",
                )
            )
    return errors


def validate_application_alignment(project_facts: dict[str, Any], application_fields: dict[str, Any]) -> list[dict[str, str]]:
    errors = []
    facts = project_facts.get("facts", {})
    for field in CORE_FIELDS:
        fact_item = facts.get(field, {})
        app_item = application_fields.get(field, {})
        if not app_item:
            errors.append(error("application_field_missing", f"`{field}` missing from application fields.", f"softcopy/outputs/application/application_fields.json#/{field}"))
            continue
        if fact_item.get("value") != app_item.get("value") or fact_item.get("status") != app_item.get("status"):
            errors.append(
                error(
                    "application_field_mismatch",
                    f"`{field}` does not match project facts.",
                    f"softcopy/outputs/application/application_fields.json#/{field}",
                )
            )
    return errors


def validate_formal_dependencies(application_fields: dict[str, Any], feature_map: dict[str, Any], manual_manifest: dict[str, Any]) -> list[dict[str, str]]:
    errors = []
    if application_fields.get("draft_mode") != "formal":
        return errors
    if feature_map.get("review_status") != "approved":
        errors.append(error("feature_map_not_approved_for_formal", "Feature map must be approved for a formal application draft.", "softcopy/feature_map.yaml#/review_status"))
    if manual_manifest and manual_manifest.get("manifest_status") not in {"approved", "pending_review"}:
        errors.append(error("manual_manifest_invalid_state", "Manual manifest state is invalid.", "softcopy/manual_manifest.yaml#/manifest_status"))
    return errors


def validate_traceability(application_fields: dict[str, Any]) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    errors = []
    warnings = []

    for key, value in application_fields.items():
        if not isinstance(value, dict) or "blocking" not in value:
            continue
        if value.get("blocking") and not value.get("sources"):
            errors.append(
                error(
                    "traceability_missing_source",
                    f"Blocking field `{key}` has no trace source.",
                    f"softcopy/outputs/application/application_fields.json#/{key}",
                )
            )

    for index, item in enumerate(application_fields.get("main_functions", [])):
        if not item.get("sources"):
            errors.append(
                error(
                    "main_function_not_traceable",
                    "Application main function is missing evidence.",
                    f"softcopy/outputs/application/application_fields.json#/main_functions/{index}",
                )
            )
        elif item.get("status") == "candidate":
            warnings.append(
                warning(
                    "main_function_candidate_only",
                    "Application main function still relies on candidate evidence.",
                    f"softcopy/outputs/application/application_fields.json#/main_functions/{index}",
                )
            )
    return errors, warnings


def validate_ownership(project_facts: dict[str, Any], ownership_evidence: dict[str, Any]) -> list[dict[str, str]]:
    errors = []
    development_mode = project_facts.get("facts", {}).get("development_mode", {}).get("value", "")
    if not development_mode:
        return errors
    if ownership_evidence.get("development_mode") and ownership_evidence.get("development_mode") != development_mode:
        errors.append(
            error(
                "ownership_development_mode_mismatch",
                "Ownership evidence development mode does not match project facts.",
                "softcopy/ownership_evidence.yaml#/development_mode",
            )
        )
    for index, item in enumerate(ownership_evidence.get("required_documents", [])):
        if item.get("required") and not item.get("provided"):
            errors.append(
                error(
                    "required_ownership_document_missing",
                    f"Required ownership document `{item.get('name', '')}` is missing.",
                    f"softcopy/ownership_evidence.yaml#/required_documents/{index}",
                )
            )
    return errors

