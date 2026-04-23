#!/usr/bin/env python3

from __future__ import annotations

from typing import Any


REQUIRED_PROVENANCE_FIELDS = [
    "rule_id",
    "rule_status",
    "severity_default",
    "authority_level",
    "source_type",
    "source_name",
    "source_ref",
    "source_locator",
    "jurisdiction",
    "scope_level",
    "effective_version",
    "effective_from",
    "last_reviewed_at",
    "reviewed_by",
]


def warning(code: str, message: str, path: str) -> dict[str, str]:
    return {"code": code, "message": message, "path": path, "severity": "WARNING"}


def info(code: str, message: str, path: str) -> dict[str, str]:
    return {"code": code, "message": message, "path": path, "severity": "INFO"}


def complete_provenance(rule: dict[str, Any]) -> bool:
    return all(bool(rule.get(field)) for field in REQUIRED_PROVENANCE_FIELDS)


def active_rules(registration_rules: dict[str, Any], filing_context: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, str]], list[dict[str, str]]]:
    active = []
    warnings = []
    infos = []
    office = filing_context.get("office", "")
    jurisdiction = filing_context.get("jurisdiction", "")

    for index, rule in enumerate(registration_rules.get("rules", [])):
        path = f"softcopy/rules/registration_rules.yaml#/rules/{index}"
        if rule.get("rule_status") != "active":
            infos.append(info("rule_not_active", f"Rule `{rule.get('rule_id', '')}` is not active.", path))
            continue
        if not complete_provenance(rule):
            warnings.append(warning("rule_provenance_incomplete", f"Rule `{rule.get('rule_id', '')}` is active but lacks complete provenance.", path))
            continue
        if rule.get("jurisdiction") != jurisdiction:
            infos.append(info("rule_jurisdiction_not_matched", f"Rule `{rule.get('rule_id', '')}` does not match current jurisdiction.", path))
            continue
        if rule.get("scope_level") == "local":
            selectors = rule.get("office_selector", [])
            if not office:
                warnings.append(warning("local_rule_office_unknown", f"Rule `{rule.get('rule_id', '')}` requires a confirmed filing office.", path))
                continue
            if office not in selectors:
                infos.append(info("local_rule_not_selected", f"Rule `{rule.get('rule_id', '')}` is not active for the current office.", path))
                continue
        active.append(rule)
    return active, warnings, infos


def evaluate_page_rules(active: list[dict[str, Any]]) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    warnings = []
    infos = []
    if not active:
        infos.append(info("no_active_page_rules", "No active page-format rules are currently enforced.", "softcopy/rules/registration_rules.yaml"))
        return warnings, infos
    infos.append(info("active_page_rules_loaded", f"Loaded {len(active)} active rule(s).", "softcopy/rules/registration_rules.yaml"))
    return warnings, infos

