#!/usr/bin/env python3

from __future__ import annotations

import re
import shutil
import tempfile
from collections import Counter
from pathlib import Path
from typing import Any

from .renderers import normalize_formats, render_optional_outputs
from .support import (
    REPO_ROOT,
    clean_outputs as clean_outputs_dir,
    copy_file_if_absent,
    copy_tree_if_absent,
    ensure_output_dirs,
    load_json,
    load_yaml,
    write_csv,
    write_json,
    write_text,
    write_yaml,
)


LANGUAGE_BY_SUFFIX = {
    ".py": "Python",
    ".js": "JavaScript",
    ".jsx": "JavaScript",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    ".java": "Java",
    ".go": "Go",
    ".rs": "Rust",
    ".rb": "Ruby",
    ".php": "PHP",
    ".cs": "C#",
    ".cpp": "C++",
    ".cc": "C++",
    ".c": "C",
    ".swift": "Swift",
    ".kt": "Kotlin",
}
SOURCE_SUFFIXES = set(LANGUAGE_BY_SUFFIX)
EXCLUDED_DIRS = {
    ".git",
    ".agents",
    "softcopy_tool",
    "softcopy",
    "evals",
    "examples",
    "node_modules",
    "dist",
    "build",
    ".next",
    ".nuxt",
    ".venv",
    "venv",
    "target",
    "out",
    "coverage",
    "__pycache__",
}
EXCLUDED_FILES = {
    "softcopy_support.py",
}
ENTRYPOINT_NAMES = {
    "main.py",
    "app.py",
    "server.py",
    "manage.py",
    "main.ts",
    "main.tsx",
    "main.js",
    "server.js",
    "index.js",
    "index.ts",
}
ROUTE_PATTERNS = [
    re.compile(r"@\w+\.(?:get|post|put|delete|patch|route)\(\s*['\"]([^'\"]+)['\"]"),
    re.compile(r"\brouter\.(?:get|post|put|delete|patch)\(\s*['\"]([^'\"]+)['\"]"),
    re.compile(r"\bapp\.(?:get|post|put|delete|patch)\(\s*['\"]([^'\"]+)['\"]"),
    re.compile(r"\bpath\(\s*['\"]([^'\"]+)['\"]"),
]
CORE_FACTS = [
    "software_name_full",
    "version",
    "development_completion_date",
    "first_publication_status",
    "copyright_owner_type",
    "copyright_owners",
    "development_mode",
    "project_type",
]
APPLICATION_FIELDS = [
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
CODE_LINES_PER_PAGE = 50
MANUAL_LINES_PER_PAGE = 30


def envelope(value: Any, status: str, blocking: bool, owner_skill: str, sources: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "value": value,
        "status": status,
        "blocking": blocking,
        "owner_skill": owner_skill,
        "sources": sources,
        "last_updated_by": owner_skill,
    }


def init_project(target: Path) -> dict[str, Any]:
    target = target.resolve()
    target.mkdir(parents=True, exist_ok=True)
    copied: list[str] = []
    conflicts: list[str] = []
    ensure_output_dirs(target)

    copy_file_if_absent(REPO_ROOT / ".agents" / "AGENTS.md", target / ".agents" / "AGENTS.md", conflicts, copied)
    copy_tree_if_absent(REPO_ROOT / ".agents" / "skills", target / ".agents" / "skills", conflicts, copied)
    copy_tree_if_absent(REPO_ROOT / "softcopy_tool", target / "softcopy_tool", conflicts, copied)
    copy_file_if_absent(REPO_ROOT / "softcopy_support.py", target / "softcopy_support.py", conflicts, copied)
    copy_file_if_absent(REPO_ROOT / ".gitignore", target / ".gitignore", conflicts, copied)
    copy_file_if_absent(REPO_ROOT / "docs" / "project_facts_guide.md", target / "docs" / "softcopy_project_facts_guide.md", conflicts, copied)
    copy_tree_if_absent(REPO_ROOT / "softcopy" / "contracts", target / "softcopy" / "contracts", conflicts, copied)
    copy_tree_if_absent(REPO_ROOT / "softcopy" / "rules", target / "softcopy" / "rules", conflicts, copied)
    copy_tree_if_absent(REPO_ROOT / "softcopy" / "schemas", target / "softcopy" / "schemas", conflicts, copied)
    for name in ["project_facts.yaml", "feature_map.yaml", "manual_manifest.yaml", "ownership_evidence.yaml"]:
        copy_file_if_absent(REPO_ROOT / "softcopy" / name, target / "softcopy" / name, conflicts, copied)

    report = {
        "target": str(target),
        "copied": copied,
        "conflicts": conflicts,
        "note": "Existing files are not overwritten. Review conflicts before relying on migrated files.",
    }
    write_json(target / "softcopy" / "outputs" / "intake" / "init_report.json", report)
    write_text(
        target / "softcopy" / "outputs" / "intake" / "init_report.md",
        "# Init Report\n\n"
        f"- Target: `{target}`\n"
        f"- Copied files: {len(copied)}\n"
        f"- Conflicts: {len(conflicts)}\n\n"
        "## Conflicts\n"
        + ("\n".join(f"- `{item}`" for item in conflicts) if conflicts else "- None")
        + "\n",
    )
    return report


def iter_source_files(repo_root: Path) -> list[Path]:
    files: list[Path] = []
    for path in repo_root.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(repo_root)
        if any(part in EXCLUDED_DIRS for part in rel.parts[:-1]):
            continue
        if path.name in EXCLUDED_FILES:
            continue
        if path.suffix.lower() in SOURCE_SUFFIXES:
            files.append(path)
    return sorted(files)


def count_effective_lines(path: Path) -> int:
    count = 0
    for raw_line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = raw_line.strip()
        if line and not line.startswith(("#", "//", "/*", "*", "*/", "--")):
            count += 1
    return count


def detect_frameworks(repo_root: Path, files: list[Path]) -> list[str]:
    frameworks: set[str] = set()
    if (repo_root / "package.json").exists():
        frameworks.add("Node.js")
    if (repo_root / "pyproject.toml").exists() or (repo_root / "requirements.txt").exists():
        frameworks.add("Python")
    if (repo_root / "manage.py").exists():
        frameworks.add("Django")
    if (repo_root / "Cargo.toml").exists():
        frameworks.add("Rust")
    if (repo_root / "go.mod").exists():
        frameworks.add("Go")
    for path in files[:200]:
        text = path.read_text(encoding="utf-8", errors="ignore")
        if "FastAPI(" in text or "APIRouter(" in text:
            frameworks.add("FastAPI")
        if "Flask(" in text or "Blueprint(" in text:
            frameworks.add("Flask")
        if "express()" in text or "from 'express'" in text or 'from \"express\"' in text:
            frameworks.add("Express")
        if "createBrowserRouter(" in text or "<Route" in text:
            frameworks.add("React Router")
    return sorted(frameworks)


def detect_entry_points(repo_root: Path, files: list[Path]) -> list[str]:
    return [str(path.relative_to(repo_root)) for path in files if path.name in ENTRYPOINT_NAMES][:20]


def extract_routes(text: str) -> list[str]:
    seen: set[str] = set()
    routes: list[str] = []
    for pattern in ROUTE_PATTERNS:
        for route in pattern.findall(text):
            if route not in seen:
                seen.add(route)
                routes.append(route)
    return routes


def scan(repo_root: Path) -> dict[str, Any]:
    ensure_output_dirs(repo_root)
    files = iter_source_files(repo_root)
    language_counter = Counter(LANGUAGE_BY_SUFFIX[path.suffix.lower()] for path in files)
    code_inventory = [
        {
            "path": str(path.relative_to(repo_root)),
            "language": LANGUAGE_BY_SUFFIX[path.suffix.lower()],
            "effective_code_lines": count_effective_lines(path),
        }
        for path in files
    ]
    detected_routes = [
        {"file": str(path.relative_to(repo_root)), "route": route, "kind": "route"}
        for path in files
        for route in extract_routes(path.read_text(encoding="utf-8", errors="ignore"))
    ]
    modules = _detect_modules(repo_root, files)
    repo_scan = {
        "primary_languages": [name for name, _ in language_counter.most_common()],
        "framework_signals": detect_frameworks(repo_root, files),
        "candidate_entry_points": detect_entry_points(repo_root, files),
        "excluded_directories": sorted(EXCLUDED_DIRS),
        "candidate_modules": modules,
        "candidate_core_files": _candidate_core_files(repo_root, files),
        "detected_routes": detected_routes,
        "code_line_summary": {
            "total_files": len(code_inventory),
            "total_effective_code_lines": sum(item["effective_code_lines"] for item in code_inventory),
        },
    }
    output_root = repo_root / "softcopy" / "outputs" / "scan"
    write_json(output_root / "repo_scan.json", repo_scan)
    write_csv(output_root / "code_inventory.csv", code_inventory, ["path", "language", "effective_code_lines"])
    write_csv(output_root / "route_inventory.csv", detected_routes, ["file", "route", "kind"])
    write_yaml(output_root / "module_candidates.yaml", {"modules": modules})
    write_text(output_root / "repo_scan_report.md", _render_scan_report(repo_scan))
    return repo_scan


def _detect_modules(repo_root: Path, files: list[Path]) -> list[dict[str, Any]]:
    buckets: dict[str, list[Path]] = {}
    for path in files:
        parts = path.relative_to(repo_root).parts
        buckets.setdefault(parts[0] if len(parts) > 1 else "root", []).append(path)
    modules = []
    for name, module_files in sorted(buckets.items()):
        modules.append(
            {
                "name": name,
                "paths": [str(path.relative_to(repo_root)) for path in module_files[:10]],
                "effective_code_lines": sum(count_effective_lines(path) for path in module_files),
                "rationale": "Top-level source bucket with repository code.",
            }
        )
    return modules[:20]


def _candidate_core_files(repo_root: Path, files: list[Path]) -> list[dict[str, Any]]:
    entry_points = set(detect_entry_points(repo_root, files))
    ranked = []
    for path in files:
        rel = str(path.relative_to(repo_root))
        loc = count_effective_lines(path)
        ranked.append((2 if rel in entry_points else 1, loc, rel))
    ranked.sort(key=lambda item: (-item[0], -item[1], item[2]))
    return [{"path": rel, "effective_code_lines": loc, "priority": priority} for priority, loc, rel in ranked[:20]]


def _render_scan_report(repo_scan: dict[str, Any]) -> str:
    def lines(items: list[str]) -> list[str]:
        return items or ["- None"]

    return "\n".join(
        [
            "# Repository Scan Report",
            "",
            "## Overview",
            f"- Total source files: {repo_scan['code_line_summary']['total_files']}",
            f"- Total effective code lines: {repo_scan['code_line_summary']['total_effective_code_lines']}",
            "",
            "## Detected Languages",
            *lines([f"- {item}" for item in repo_scan["primary_languages"]]),
            "",
            "## Framework Signals",
            *lines([f"- {item}" for item in repo_scan["framework_signals"]]),
            "",
            "## Candidate Entry Points",
            *lines([f"- `{item}`" for item in repo_scan["candidate_entry_points"]]),
            "",
            "## Candidate Modules",
            *lines([f"- {item['name']}: {item['effective_code_lines']} effective lines" for item in repo_scan["candidate_modules"]]),
            "",
            "## Route Findings",
            *lines([f"- `{item['route']}` in `{item['file']}`" for item in repo_scan["detected_routes"][:20]]),
            "",
            "## Candidate Core Files",
            *lines([f"- `{item['path']}` ({item['effective_code_lines']} lines)" for item in repo_scan["candidate_core_files"]]),
            "",
        ]
    ) + "\n"


def intake(repo_root: Path) -> None:
    ensure_output_dirs(repo_root)
    project_facts = load_yaml(repo_root / "softcopy" / "project_facts.yaml", {})
    repo_scan = load_json(repo_root / "softcopy" / "outputs" / "scan" / "repo_scan.json", {})
    facts = project_facts.get("facts", {})
    confirmed = []
    missing = []
    for field in CORE_FACTS:
        item = facts.get(field, {})
        status = item.get("status", "missing")
        value = item.get("value", "")
        if status == "confirmed":
            confirmed.append(f"- `{field}`: `{value}`")
        else:
            missing.append(f"- `{field}` (status: `{status}`)")
    candidates = [f"- Repository folder name: `{repo_root.name}`"]
    if repo_scan.get("primary_languages"):
        candidates.append(f"- Detected primary languages: `{', '.join(repo_scan['primary_languages'])}`")
    conflicts = []
    if facts.get("first_publication_status", {}).get("value") == "unpublished" and facts.get("first_publication_status", {}).get("status") != "confirmed":
        conflicts.append("- `first_publication_status` must not be `unpublished` before confirmation.")
    write_text(
        repo_root / "softcopy" / "outputs" / "intake" / "intake_report.md",
        "# Intake Report\n\n"
        "## Confirmed Facts\n"
        + ("\n".join(confirmed) if confirmed else "- None")
        + "\n\n## Missing Required Facts\n"
        + ("\n".join(missing) if missing else "- None")
        + "\n\n## Candidate Facts From Repository Evidence\n"
        + "\n".join(candidates)
        + "\n\n## Conflicts To Resolve\n"
        + ("\n".join(conflicts) if conflicts else "- None")
        + "\n\n## Recommended Next Step\n- Confirm the missing core facts in `softcopy/project_facts.yaml` before attempting a formal draft.\n",
    )


def feature_map(repo_root: Path) -> None:
    ensure_output_dirs(repo_root)
    module_candidates = load_yaml(repo_root / "softcopy" / "outputs" / "scan" / "module_candidates.yaml", {"modules": []})
    repo_scan = load_json(repo_root / "softcopy" / "outputs" / "scan" / "repo_scan.json", {})
    routes = repo_scan.get("detected_routes", [])
    features = []
    for index, module in enumerate(module_candidates.get("modules", [])[:10], start=1):
        feature_id = f"FEAT-{index:03d}"
        name = module.get("name", f"Module {index}")
        module_routes = [item["route"] for item in routes if item["file"] in module.get("paths", [])][:5]
        features.append(
            {
                "feature_id": feature_id,
                "review_status": "pending_review",
                "name": envelope(name, "derived", False, "softcopy-feature-map", [{"source_type": "repo_scan", "source_ref": "softcopy/outputs/scan/module_candidates.yaml#/modules", "authority_level": "B", "confidence": 0.6}]),
                "summary": envelope(f"Candidate feature derived from module {name}.", "derived", False, "softcopy-feature-map", [{"source_type": "repo_scan", "source_ref": "softcopy/outputs/scan/module_candidates.yaml#/modules", "authority_level": "B", "confidence": 0.6}]),
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
    generated = {"review_status": "pending_review", "features": features}
    output_root = repo_root / "softcopy" / "outputs" / "feature_map"
    write_yaml(output_root / "feature_map.candidate.yaml", generated)
    feature_map_path = repo_root / "softcopy" / "feature_map.yaml"
    if not feature_map_path.exists():
        write_yaml(repo_root / "softcopy" / "feature_map.yaml", generated)
    write_text(repo_root / "softcopy" / "outputs" / "feature_map" / "feature_map_report.md", "# Feature Map Report\n\n- review_status: `pending_review`\n\n## Proposed features\n" + ("\n".join(f"- `{item['feature_id']}` {item['name']['value']}" for item in features) if features else "- None") + "\n")


def proof_check(repo_root: Path) -> None:
    ensure_output_dirs(repo_root)
    documents_by_mode = {
        "independent": [("PROOF-001", "Identity or organization proof", True), ("PROOF-002", "Task assignment or project proof", False)],
        "cooperative": [("PROOF-001", "Identity or organization proof", True), ("PROOF-003", "Cooperative development agreement", True)],
        "entrusted": [("PROOF-001", "Identity or organization proof", True), ("PROOF-004", "Entrusted development agreement", True)],
        "employee": [("PROOF-001", "Identity or organization proof", True), ("PROOF-005", "Internal duty development proof", True)],
    }
    project_facts = load_yaml(repo_root / "softcopy" / "project_facts.yaml", {})
    development_mode = project_facts.get("facts", {}).get("development_mode", {}).get("value", "")
    normalized = development_mode if development_mode in documents_by_mode else "independent"
    docs = [{"doc_id": doc_id, "name": name, "required": required, "provided": False, "file_ref": ""} for doc_id, name, required in documents_by_mode[normalized]]
    generated = {"evidence_status": "pending_review", "development_mode": development_mode, "required_documents": docs, "notes": ""}
    write_yaml(repo_root / "softcopy" / "outputs" / "proof_check" / "ownership_evidence.candidate.yaml", generated)
    ownership_path = repo_root / "softcopy" / "ownership_evidence.yaml"
    if not ownership_path.exists():
        write_yaml(repo_root / "softcopy" / "ownership_evidence.yaml", generated)
    write_text(repo_root / "softcopy" / "outputs" / "proof_check" / "proof_checklist.md", "# Proof Checklist\n\n" + "\n".join(f"- [{' ' if item['required'] else '-'}] `{item['doc_id']}` {item['name']}" for item in docs) + "\n")
    write_text(repo_root / "softcopy" / "outputs" / "proof_check" / "missing_proofs.md", "# Missing Proofs\n\n" + "\n".join(f"- `{item['doc_id']}` {item['name']}" for item in docs if item["required"]) + "\n")


def application(repo_root: Path) -> None:
    ensure_output_dirs(repo_root)
    project_facts = load_yaml(repo_root / "softcopy" / "project_facts.yaml", {})
    required_facts = load_yaml(repo_root / "softcopy" / "contracts" / "required_facts.yaml", {})
    fmap = load_yaml(repo_root / "softcopy" / "feature_map.yaml", {"review_status": "pending_review", "features": []})
    repo_scan = load_json(repo_root / "softcopy" / "outputs" / "scan" / "repo_scan.json", {})
    draft_mode, needs_confirmation = _determine_draft_mode(project_facts, required_facts, fmap)
    facts = project_facts.get("facts", {})
    fields = {field: _clone_fact_field(field, facts) for field in APPLICATION_FIELDS}
    fields.update(
        {
            "draft_mode": draft_mode,
            "main_functions": _main_functions(fmap, repo_scan),
            "technical_highlights": project_facts.get("profile", {}).get("technical_highlights", {}).get("value", []),
            "runtime_environment": project_facts.get("profile", {}).get("runtime_environment", {}).get("value", {}),
            "needs_confirmation": needs_confirmation,
        }
    )
    output_root = repo_root / "softcopy" / "outputs" / "application"
    write_json(output_root / "application_fields.json", fields)
    write_json(output_root / "application_trace.json", _application_trace(fields))
    write_text(output_root / "application_draft.md", _render_application(fields))
    write_text(output_root / "application_review_checklist.md", _render_application_checklist(fields))


def _clone_fact_field(name: str, facts: dict[str, Any]) -> dict[str, Any]:
    item = facts.get(name)
    if item is None:
        return envelope([] if name == "copyright_owners" else "", "missing", name != "software_name_short", "softcopy-application", [])
    cloned = dict(item)
    cloned["owner_skill"] = "softcopy-application"
    cloned["last_updated_by"] = "softcopy-application"
    return cloned


def _determine_draft_mode(project_facts: dict[str, Any], required_facts: dict[str, Any], fmap: dict[str, Any]) -> tuple[str, list[str]]:
    facts = project_facts.get("facts", {})
    needs = [item["field"] for item in required_facts.get("core_required_facts", []) if facts.get(item["field"], {}).get("status", "missing") != "confirmed"]
    publication_status = facts.get("first_publication_status", {})
    if publication_status.get("status") == "confirmed" and publication_status.get("value") == "published" and facts.get("first_publication_date", {}).get("status") != "confirmed":
        needs.append("first_publication_date")
    if needs or fmap.get("review_status") != "approved":
        return "provisional", sorted(set(needs))
    return "formal", []


def _main_functions(fmap: dict[str, Any], repo_scan: dict[str, Any]) -> list[dict[str, Any]]:
    if fmap.get("review_status") == "approved" and fmap.get("features"):
        results = []
        for feature in fmap["features"]:
            for claim in feature.get("application_claims", []):
                results.append(envelope(claim, "derived", False, "softcopy-application", [{"source_type": "feature_map", "source_ref": f"softcopy/feature_map.yaml#/features/{feature.get('feature_id', 'unknown')}", "authority_level": "B", "confidence": 0.9}]))
        return results
    return [
        envelope(f"Candidate module: {module['name']}", "candidate", False, "softcopy-application", [{"source_type": "repo_scan", "source_ref": "softcopy/outputs/scan/repo_scan.json#/candidate_modules", "authority_level": "B", "confidence": 0.5}])
        for module in repo_scan.get("candidate_modules", [])[:5]
    ]


def _application_trace(fields: dict[str, Any]) -> dict[str, Any]:
    return {
        "draft_mode": fields["draft_mode"],
        "fields": {key: {"status": value.get("status"), "sources": value.get("sources", [])} for key, value in fields.items() if isinstance(value, dict) and "sources" in value},
        "main_functions": [{"value": item.get("value"), "sources": item.get("sources", [])} for item in fields.get("main_functions", [])],
    }


def _render_application(fields: dict[str, Any]) -> str:
    lines = ["# Application Draft", "", f"- Draft mode: `{fields['draft_mode']}`", "", "## Basic Information"]
    for field in APPLICATION_FIELDS:
        lines.append(f"- `{field}`: `{fields[field]['value']}` (status: `{fields[field]['status']}`)")
    lines.extend(["", "## Main Functions Summary"])
    lines.extend([f"- {item['value']} (status: `{item['status']}`)" for item in fields["main_functions"]] or ["- None"])
    lines.extend(["", "## Technical Characteristics Summary"])
    lines.extend([f"- {item}" for item in fields.get("technical_highlights", [])] or ["- None"])
    lines.extend(["", "## Runtime and Deployment Environment"])
    runtime = fields.get("runtime_environment", {})
    lines.extend([f"- `{key}`: {value}" for key, value in runtime.items()] or ["- None"])
    lines.extend(["", "## Facts Needing Confirmation"])
    lines.extend([f"- `{field}`" for field in fields["needs_confirmation"]] or ["- None"])
    lines.extend(["", "## Traceability Notes", "- See `application_trace.json`."])
    return "\n".join(lines) + "\n"


def _render_application_checklist(fields: dict[str, Any]) -> str:
    lines = ["# Application Review Checklist", "", f"- [ ] Draft mode `{fields['draft_mode']}` is expected", "- [ ] software name consistency", "- [ ] version consistency", "- [ ] owner consistency", "- [ ] development mode consistency", "- [ ] function wording supported by evidence", "- [ ] no exaggerated or unsupported claims"]
    if fields["needs_confirmation"]:
        lines.extend(["", "## Remaining confirmations"])
        lines.extend(f"- [ ] `{field}`" for field in fields["needs_confirmation"])
    return "\n".join(lines) + "\n"


def code_doc(repo_root: Path, formats: list[str] | None = None) -> dict[str, Any]:
    ensure_output_dirs(repo_root)
    formats = normalize_formats(formats)
    repo_scan = load_json(repo_root / "softcopy" / "outputs" / "scan" / "repo_scan.json", {})
    selected = repo_scan.get("candidate_core_files", [])[:10]
    output_root = repo_root / "softcopy" / "outputs" / "code_doc"
    write_yaml(output_root / "code_selection.yaml", {"selection_status": "pending_review", "selected_files": selected})
    candidate_pages = _build_code_pages(repo_root, selected)
    pages = _select_page_window(candidate_pages)
    page_trace = [
        {
            "page": item["page"],
            "path": item.get("path", ""),
            "line_start": item.get("line_start", 0),
            "line_end": item.get("line_end", 0),
            "effective_line_count": item.get("effective_line_count", 0),
            "source_ref": item.get("source_ref", ""),
            "sources": [{"source_type": "repository_file", "source_ref": item.get("source_ref", ""), "authority_level": "B", "confidence": 0.9}],
        }
        for item in pages
    ]
    page_payload = {
        "page_size_effective_lines": CODE_LINES_PER_PAGE,
        "total_candidate_pages": len(candidate_pages),
        "selected_pages": [item["page"] for item in pages],
        "pages": pages,
    }
    lines = ["# Source Code Evidence Draft", "", "## File Selection Summary"]
    lines.extend([f"- `{item.get('path', '')}` ({item.get('effective_code_lines', 0)} lines)" for item in selected] or ["- None"])
    lines.extend(["", "## Paged Source Material"])
    for page in pages:
        lines.extend([f"### Page {page['page']}: {page['path']} lines {page['line_start']}-{page['line_end']}", "```text"])
        lines.extend(page.get("content_lines", []))
        lines.append("```")
    lines.extend(["", "## Page Trace Notes", "- See `page_trace.json` and `code_pages.json`."])
    markdown_path = output_root / "code_doc.md"
    write_text(markdown_path, "\n".join(lines) + "\n")
    write_json(output_root / "code_pages.json", page_payload)
    write_json(output_root / "page_trace.json", {"pages": page_trace})
    rendered = render_optional_outputs(markdown_path, formats)
    write_text(output_root / "code_doc_report.md", "# Code Doc Report\n\n- Draft source-code evidence was generated from current scan candidates.\n- Review file selection before formal use.\n- Optional rendered outputs: " + (", ".join(f"`{item}`" for item in rendered) if rendered else "None") + "\n")
    return page_payload


def _build_code_pages(repo_root: Path, selected: list[dict[str, Any]]) -> list[dict[str, Any]]:
    pages: list[dict[str, Any]] = []
    page_number = 1
    for item in selected:
        rel = item.get("path", "")
        path = repo_root / rel
        if not rel or not path.exists():
            continue
        effective_lines = _effective_source_lines(path)
        for chunk in _chunks(effective_lines, CODE_LINES_PER_PAGE):
            if not chunk:
                continue
            pages.append(
                {
                    "page": page_number,
                    "path": rel,
                    "line_start": chunk[0][0],
                    "line_end": chunk[-1][0],
                    "effective_line_count": len(chunk),
                    "source_ref": f"{rel}#L{chunk[0][0]}-L{chunk[-1][0]}",
                    "content_lines": [text for _, text in chunk],
                }
            )
            page_number += 1
    return pages


def _effective_source_lines(path: Path) -> list[tuple[int, str]]:
    lines: list[tuple[int, str]] = []
    for number, raw_line in enumerate(path.read_text(encoding="utf-8", errors="ignore").splitlines(), start=1):
        line = raw_line.rstrip()
        stripped = line.strip()
        if stripped and not stripped.startswith(("#", "//", "/*", "*", "*/", "--")):
            lines.append((number, line))
    return lines


def _chunks(items: list[Any], size: int) -> list[list[Any]]:
    return [items[index : index + size] for index in range(0, len(items), size)]


def _select_page_window(candidate_pages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if len(candidate_pages) <= 60:
        return candidate_pages
    return candidate_pages[:30] + candidate_pages[-30:]


def manual(repo_root: Path, formats: list[str] | None = None) -> dict[str, Any]:
    ensure_output_dirs(repo_root)
    formats = normalize_formats(formats)
    project_facts = load_yaml(repo_root / "softcopy" / "project_facts.yaml", {})
    fmap = load_yaml(repo_root / "softcopy" / "feature_map.yaml", {})
    doc_type = _infer_doc_type(project_facts)
    sections = []
    for index, feature in enumerate(fmap.get("features", []), start=1):
        title = feature.get("name", {}).get("value") or f"Feature {index}"
        sections.append({"section_id": f"SEC-{index:03d}", "title": title, "goal": f"Describe how to use {title}.", "prerequisites": [], "steps": [], "expected_result": "", "screenshot_ids": [], "notes": []})
    output_root = repo_root / "softcopy" / "outputs" / "manual"
    stub = {"manifest_status": "pending_review", "doc_type": doc_type, "sections": sections, "screenshots": []}
    write_yaml(output_root / "manual_manifest.stub.yaml", stub)
    manifest_path = repo_root / "softcopy" / "manual_manifest.yaml"
    manifest = load_yaml(manifest_path, {})
    if not manifest_path.exists():
        write_yaml(manifest_path, stub)
        manifest = stub
    write_text(output_root / "manual_outline.md", "# Manual Outline\n\n" + "\n".join(f"- `{item['section_id']}` {item['title']}" for item in sections) + "\n")
    pages = _build_manual_pages(manifest)
    page_payload = {
        "page_size_effective_lines": MANUAL_LINES_PER_PAGE,
        "total_candidate_pages": len(pages),
        "selected_pages": [item["page"] for item in pages],
        "pages": pages,
    }
    lines = ["# Manual Draft", "", f"- manifest_status: `{manifest.get('manifest_status', 'pending_review')}`", "", "## Paged Manual Material"]
    for page in pages:
        lines.extend([f"### Page {page['page']}: {page['section_id']}"])
        lines.extend(page["content_lines"])
    if not pages:
        lines.append("- None")
    markdown_path = output_root / "manual.md"
    write_text(markdown_path, "\n".join(lines) + "\n")
    write_json(output_root / "manual_pages.json", page_payload)
    write_json(output_root / "manual_trace.json", {"sections": [{"section_id": section.get("section_id", ""), "sources": [{"source_type": "manual_manifest", "source_ref": f"softcopy/manual_manifest.yaml#/sections/{section.get('section_id', '')}", "authority_level": "B", "confidence": 0.9}]} for section in manifest.get("sections", [])], "screenshots": manifest.get("screenshots", []), "pages": pages})
    rendered = render_optional_outputs(markdown_path, formats)
    write_text(output_root / "manual_report.md", "# Manual Report\n\n- Draft manual was generated from the current manifest.\n- Fill real steps and screenshot references before formal use.\n- Optional rendered outputs: " + (", ".join(f"`{item}`" for item in rendered) if rendered else "None") + "\n")
    return page_payload


def _build_manual_pages(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    candidate_lines: list[tuple[str, str]] = []
    for section in manifest.get("sections", []):
        section_id = section.get("section_id", "")
        candidate_lines.append((section_id, f"Section {section_id}: {section.get('title', '')}"))
        candidate_lines.append((section_id, f"Goal: {section.get('goal', '')}"))
        for item in section.get("prerequisites", []):
            candidate_lines.append((section_id, f"Prerequisite: {item}"))
        for index, item in enumerate(section.get("steps", []), start=1):
            candidate_lines.append((section_id, f"Step {index}: {item}"))
        candidate_lines.append((section_id, f"Expected result: {section.get('expected_result', '')}"))
        for item in section.get("notes", []):
            candidate_lines.append((section_id, f"Note: {item}"))
        for item in section.get("screenshot_ids", []):
            candidate_lines.append((section_id, f"Screenshot reference: {item}"))

    pages: list[dict[str, Any]] = []
    for index, chunk in enumerate(_chunks(candidate_lines, MANUAL_LINES_PER_PAGE), start=1):
        if not chunk:
            continue
        section_ids = sorted({item[0] for item in chunk if item[0]})
        pages.append(
            {
                "page": index,
                "section_id": ",".join(section_ids),
                "line_start": (index - 1) * MANUAL_LINES_PER_PAGE + 1,
                "line_end": (index - 1) * MANUAL_LINES_PER_PAGE + len(chunk),
                "effective_line_count": len(chunk),
                "source_ref": "softcopy/manual_manifest.yaml#/sections",
                "content_lines": [item[1] for item in chunk],
            }
        )
    return _select_page_window(pages)


def _infer_doc_type(project_facts: dict[str, Any]) -> str:
    project_type = project_facts.get("facts", {}).get("project_type", {}).get("value", "")
    has_gui = project_facts.get("profile", {}).get("has_gui", {}).get("value", False)
    has_api = project_facts.get("profile", {}).get("has_backend_api", {}).get("value", False)
    if has_gui and has_api:
        return "hybrid"
    if has_gui:
        return "user_manual"
    if project_type in {"cli_tool", "sdk", "algorithm_library"}:
        return "design_spec"
    return "api_manual"


def validate(repo_root: Path) -> dict[str, Any]:
    ensure_output_dirs(repo_root)
    project_facts = load_yaml(repo_root / "softcopy" / "project_facts.yaml", {})
    required_facts = load_yaml(repo_root / "softcopy" / "contracts" / "required_facts.yaml", {})
    fmap = load_yaml(repo_root / "softcopy" / "feature_map.yaml", {})
    manual_manifest = load_yaml(repo_root / "softcopy" / "manual_manifest.yaml", {})
    ownership = load_yaml(repo_root / "softcopy" / "ownership_evidence.yaml", {})
    application_fields = load_json(repo_root / "softcopy" / "outputs" / "application" / "application_fields.json", {})
    code_pages = load_json(repo_root / "softcopy" / "outputs" / "code_doc" / "code_pages.json", {})
    manual_pages = load_json(repo_root / "softcopy" / "outputs" / "manual" / "manual_pages.json", {})
    rules = load_yaml(repo_root / "softcopy" / "rules" / "registration_rules.yaml", {})
    errors: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []
    infos: list[dict[str, str]] = []
    _validate_required(project_facts, required_facts, errors)
    _validate_application_alignment(project_facts, application_fields, errors)
    _validate_traceability(application_fields, errors, warnings)
    _validate_review_gates(fmap, manual_manifest, application_fields, errors)
    _validate_ownership(repo_root, project_facts, ownership, errors)
    active, rule_warnings, rule_infos = _active_rules(rules, project_facts.get("filing_context", {}))
    warnings.extend(rule_warnings)
    infos.extend(rule_infos)
    _validate_page_rules(active, code_pages, manual_pages, errors, infos)
    if not active:
        infos.append(_info("no_active_page_rules", "No active page-format rules are currently enforced.", "softcopy/rules/registration_rules.yaml"))
    else:
        infos.append(_info("active_page_rules_loaded", f"Loaded {len(active)} active rule(s).", "softcopy/rules/registration_rules.yaml"))
    ready = not errors
    summary = {"submission_readiness": "ready_to_submit" if ready else "package_validation_failed", "activated_rules": [rule["rule_id"] for rule in active]}
    output_root = repo_root / "softcopy" / "outputs"
    write_json(output_root / "validation" / "errors.json", errors)
    write_json(output_root / "validation" / "warnings.json", warnings)
    write_text(output_root / "validation" / "validation_report.md", _render_validation_report(summary, errors, warnings, infos))
    write_text(output_root / "traceability" / "traceability_report.md", _render_traceability_report(project_facts, application_fields, errors))
    ready_flag = output_root / "package" / "READY_TO_SUBMIT.flag"
    if ready:
        write_text(ready_flag, "READY_TO_SUBMIT\n")
    elif ready_flag.exists():
        ready_flag.unlink()
    return {"errors": errors, "warnings": warnings, "infos": infos, "ready": ready}


def _validate_required(project_facts: dict[str, Any], required_facts: dict[str, Any], errors: list[dict[str, str]]) -> None:
    facts = project_facts.get("facts", {})
    for item in required_facts.get("core_required_facts", []):
        field = item["field"]
        if facts.get(field, {}).get("status", "missing") != "confirmed":
            errors.append(_error("core_required_fact_not_confirmed", f"`{field}` must be confirmed before formal readiness.", f"softcopy/project_facts.yaml#/facts/{field}"))
    publication_status = facts.get("first_publication_status", {})
    if publication_status.get("status") == "confirmed" and publication_status.get("value") == "published" and facts.get("first_publication_date", {}).get("status") != "confirmed":
        errors.append(_error("conditional_required_fact_not_confirmed", "`first_publication_date` must be confirmed when publication status is published.", "softcopy/project_facts.yaml#/facts/first_publication_date"))


def _validate_application_alignment(project_facts: dict[str, Any], fields: dict[str, Any], errors: list[dict[str, str]]) -> None:
    facts = project_facts.get("facts", {})
    for field in CORE_FACTS:
        app_item = fields.get(field, {})
        fact_item = facts.get(field, {})
        if not app_item:
            errors.append(_error("application_field_missing", f"`{field}` missing from application fields.", f"softcopy/outputs/application/application_fields.json#/{field}"))
        elif app_item.get("value") != fact_item.get("value") or app_item.get("status") != fact_item.get("status"):
            errors.append(_error("application_field_mismatch", f"`{field}` does not match project facts.", f"softcopy/outputs/application/application_fields.json#/{field}"))


def _validate_traceability(fields: dict[str, Any], errors: list[dict[str, str]], warnings: list[dict[str, str]]) -> None:
    for key, value in fields.items():
        if isinstance(value, dict) and value.get("blocking") and not value.get("sources"):
            errors.append(_error("traceability_missing_source", f"Blocking field `{key}` has no trace source.", f"softcopy/outputs/application/application_fields.json#/{key}"))
    for index, item in enumerate(fields.get("main_functions", [])):
        if not item.get("sources"):
            errors.append(_error("main_function_not_traceable", "Application main function is missing evidence.", f"softcopy/outputs/application/application_fields.json#/main_functions/{index}"))
        elif item.get("status") == "candidate" and fields.get("draft_mode") == "formal":
            errors.append(_error("formal_main_function_candidate_only", "Formal application main function cannot rely on scan candidate evidence.", f"softcopy/outputs/application/application_fields.json#/main_functions/{index}"))
        elif item.get("status") == "candidate":
            warnings.append(_warning("main_function_candidate_only", "Application main function still relies on candidate evidence.", f"softcopy/outputs/application/application_fields.json#/main_functions/{index}"))


def _validate_review_gates(fmap: dict[str, Any], manual_manifest: dict[str, Any], application_fields: dict[str, Any], errors: list[dict[str, str]]) -> None:
    if fmap.get("review_status") != "approved":
        errors.append(_error("feature_map_not_approved_for_readiness", "Feature map must be approved before ready-to-submit.", "softcopy/feature_map.yaml#/review_status"))
    if not fmap.get("features"):
        errors.append(_error("feature_map_empty_for_readiness", "Feature map must contain approved feature evidence before ready-to-submit.", "softcopy/feature_map.yaml#/features"))
    if manual_manifest.get("manifest_status") != "approved":
        errors.append(_error("manual_manifest_not_approved_for_readiness", "Manual manifest must be approved before ready-to-submit.", "softcopy/manual_manifest.yaml#/manifest_status"))
    if not manual_manifest.get("sections"):
        errors.append(_error("manual_manifest_empty_for_readiness", "Manual manifest must contain reviewed sections before ready-to-submit.", "softcopy/manual_manifest.yaml#/sections"))
    if application_fields.get("draft_mode") == "formal" and fmap.get("review_status") != "approved":
        errors.append(_error("feature_map_not_approved_for_formal", "Feature map must be approved for formal readiness.", "softcopy/feature_map.yaml#/review_status"))


def _validate_ownership(repo_root: Path, project_facts: dict[str, Any], ownership: dict[str, Any], errors: list[dict[str, str]]) -> None:
    mode = project_facts.get("facts", {}).get("development_mode", {}).get("value", "")
    if ownership.get("evidence_status") != "approved":
        errors.append(_error("ownership_evidence_not_approved_for_readiness", "Ownership evidence must be approved before ready-to-submit.", "softcopy/ownership_evidence.yaml#/evidence_status"))
    if not ownership.get("required_documents"):
        errors.append(_error("ownership_evidence_not_reviewed", "Ownership evidence checklist has not been reviewed into canonical ownership_evidence.yaml.", "softcopy/ownership_evidence.yaml#/required_documents"))
        return
    if ownership.get("development_mode") and mode and ownership.get("development_mode") != mode:
        errors.append(_error("ownership_development_mode_mismatch", "Ownership evidence development mode does not match project facts.", "softcopy/ownership_evidence.yaml#/development_mode"))
    for index, item in enumerate(ownership.get("required_documents", [])):
        if item.get("required"):
            if not item.get("provided"):
                errors.append(_error("required_ownership_document_missing", f"Required ownership document `{item.get('name', '')}` is missing.", f"softcopy/ownership_evidence.yaml#/required_documents/{index}"))
            file_ref = item.get("file_ref", "")
            if not file_ref:
                errors.append(_error("required_ownership_document_file_ref_missing", f"Required ownership document `{item.get('name', '')}` must include file_ref.", f"softcopy/ownership_evidence.yaml#/required_documents/{index}/file_ref"))
            elif not _is_external_ref(file_ref) and not (repo_root / file_ref).exists():
                errors.append(_error("required_ownership_document_file_not_found", f"Required ownership document file `{file_ref}` was not found.", f"softcopy/ownership_evidence.yaml#/required_documents/{index}/file_ref"))


def _is_external_ref(value: str) -> bool:
    return value.startswith(("http://", "https://", "app://"))


REQUIRED_RULE_FIELDS = ["rule_id", "rule_status", "severity_default", "authority_level", "source_type", "source_name", "source_ref", "source_locator", "jurisdiction", "scope_level", "effective_version", "effective_from", "last_reviewed_at", "reviewed_by"]


def _active_rules(rules: dict[str, Any], filing_context: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, str]], list[dict[str, str]]]:
    active: list[dict[str, Any]] = []
    warnings: list[dict[str, str]] = []
    infos: list[dict[str, str]] = []
    jurisdiction = filing_context.get("jurisdiction", "")
    office = filing_context.get("office", "")
    for index, rule in enumerate(rules.get("rules", [])):
        path = f"softcopy/rules/registration_rules.yaml#/rules/{index}"
        if rule.get("rule_status") != "active":
            infos.append(_info("rule_not_active", f"Rule `{rule.get('rule_id', '')}` is not active.", path))
            continue
        if not all(rule.get(field) for field in REQUIRED_RULE_FIELDS):
            warnings.append(_warning("rule_provenance_incomplete", f"Rule `{rule.get('rule_id', '')}` is active but lacks complete provenance.", path))
            continue
        if rule.get("jurisdiction") != jurisdiction:
            infos.append(_info("rule_jurisdiction_not_matched", f"Rule `{rule.get('rule_id', '')}` does not match current jurisdiction.", path))
            continue
        if rule.get("scope_level") == "local":
            selectors = rule.get("office_selector", [])
            if not office:
                warnings.append(_warning("local_rule_office_unknown", f"Rule `{rule.get('rule_id', '')}` requires a confirmed filing office.", path))
                continue
            if office not in selectors:
                infos.append(_info("local_rule_not_selected", f"Rule `{rule.get('rule_id', '')}` is not active for the current office.", path))
                continue
        active.append(rule)
    return active, warnings, infos


def _validate_page_rules(active_rules: list[dict[str, Any]], code_pages: dict[str, Any], manual_pages: dict[str, Any], errors: list[dict[str, str]], infos: list[dict[str, str]]) -> None:
    for rule in active_rules:
        applies_to = set(rule.get("applies_to", []))
        title = rule.get("title", "")
        threshold = rule.get("threshold", {})
        if "code_doc" in applies_to and title == "source_code_document_page_window":
            _validate_page_window("code_doc", rule, code_pages, errors)
        elif "code_doc" in applies_to and title == "source_code_lines_per_page":
            _validate_min_lines("code_doc", rule, code_pages, threshold.get("min_lines_per_page", CODE_LINES_PER_PAGE), errors)
        elif "manual_doc" in applies_to and title == "documentation_page_window":
            _validate_page_window("manual_doc", rule, manual_pages, errors)
        elif "manual_doc" in applies_to and title == "documentation_lines_per_page":
            _validate_min_lines("manual_doc", rule, manual_pages, threshold.get("min_lines_per_page", MANUAL_LINES_PER_PAGE), errors)
        elif "printed_materials" in applies_to:
            infos.append(_info("printed_material_rule_not_machine_checked", f"Rule `{rule.get('rule_id', '')}` is active but only checked during rendered/printed review.", "softcopy/rules/registration_rules.yaml"))


def _validate_page_window(kind: str, rule: dict[str, Any], pages_payload: dict[str, Any], errors: list[dict[str, str]]) -> None:
    pages = pages_payload.get("pages", [])
    if not pages:
        errors.append(_error(f"{kind}_pages_missing", f"{kind} pages are missing for rule `{rule.get('rule_id', '')}`.", f"softcopy/outputs/{'code_doc' if kind == 'code_doc' else 'manual'}/{kind.split('_')[0]}_pages.json"))
        return
    total = pages_payload.get("total_candidate_pages", len(pages))
    threshold = rule.get("threshold", {})
    fallback = threshold.get("fallback_if_total_lt", 60)
    front = threshold.get("front_pages", 30)
    back = threshold.get("back_pages", 30)
    expected = list(range(1, total + 1)) if total <= fallback else list(range(1, front + 1)) + list(range(total - back + 1, total + 1))
    actual = pages_payload.get("selected_pages", [item.get("page") for item in pages])
    if actual != expected:
        errors.append(_error(f"{kind}_page_window_mismatch", f"{kind} selected pages do not satisfy rule `{rule.get('rule_id', '')}`.", f"softcopy/outputs/{'code_doc' if kind == 'code_doc' else 'manual'}"))


def _validate_min_lines(kind: str, rule: dict[str, Any], pages_payload: dict[str, Any], min_lines: int, errors: list[dict[str, str]]) -> None:
    pages = pages_payload.get("pages", [])
    if not pages:
        errors.append(_error(f"{kind}_pages_missing", f"{kind} pages are missing for rule `{rule.get('rule_id', '')}`.", f"softcopy/outputs/{'code_doc' if kind == 'code_doc' else 'manual'}"))
        return
    for page in pages:
        if page.get("effective_line_count", 0) < min_lines:
            errors.append(_error(f"{kind}_page_too_short", f"{kind} page {page.get('page')} has fewer than {min_lines} effective lines for rule `{rule.get('rule_id', '')}`.", f"softcopy/outputs/{'code_doc' if kind == 'code_doc' else 'manual'}#/pages/{page.get('page')}"))


def _render_validation_report(summary: dict[str, Any], errors: list[dict[str, str]], warnings: list[dict[str, str]], infos: list[dict[str, str]]) -> str:
    def entries(items: list[dict[str, str]]) -> list[str]:
        return [f"- `{item['code']}`: {item['message']} ({item['path']})" for item in items] or ["- None"]

    trace_errors = [item for item in errors if item["code"] in {"traceability_missing_source", "main_function_not_traceable"}]
    return "\n".join(
        [
            "# Validation Report",
            "",
            "## Summary",
            f"- Errors: {len(errors)}",
            f"- Warnings: {len(warnings)}",
            f"- Infos: {len(infos)}",
            f"- Submission readiness: `{summary['submission_readiness']}`",
            "",
            "## Activated Rules",
            *([f"- `{rule_id}`" for rule_id in summary["activated_rules"]] or ["- None"]),
            "",
            "## Errors",
            *entries(errors),
            "",
            "## Warnings",
            *entries(warnings),
            "",
            "## Informational Notes",
            *entries(infos),
            "",
            "## Traceability Gaps",
            *entries(trace_errors),
            "",
            "## Submission Readiness Conclusion",
            f"- `{summary['submission_readiness']}`",
            "",
            "## Required Next Fixes",
            *([f"- {item['message']}" for item in errors] or ["- None"]),
        ]
    ) + "\n"


def _render_traceability_report(project_facts: dict[str, Any], fields: dict[str, Any], errors: list[dict[str, str]]) -> str:
    lines = ["# Traceability Report", "", "## Scope of Traced Artifacts", "- project facts", "- application fields", "", "## Blocking Facts and Their Sources"]
    for field, value in project_facts.get("facts", {}).items():
        if isinstance(value, dict) and value.get("blocking"):
            refs = [item.get("source_ref", "") for item in value.get("sources", [])]
            lines.append(f"- `{field}` ({value.get('status', 'missing')}): {', '.join(refs) if refs else 'NO_SOURCE'}")
    lines.extend(["", "## Application Field Traces"])
    for field, value in fields.items():
        if isinstance(value, dict) and "sources" in value:
            refs = [item.get("source_ref", "") for item in value.get("sources", [])]
            lines.append(f"- `{field}`: {', '.join(refs) if refs else 'NO_SOURCE'}")
    lines.extend(["", "## Code Page Traces", "- Review `softcopy/outputs/code_doc/page_trace.json` when code-doc outputs exist."])
    lines.extend(["", "## Manual Section and Screenshot Traces", "- Review `softcopy/outputs/manual/manual_trace.json` when manual outputs exist."])
    trace_errors = [item for item in errors if item["code"] in {"traceability_missing_source", "main_function_not_traceable"}]
    lines.extend(["", "## Unresolved Trace Gaps", *([f"- `{item['code']}`: {item['message']}" for item in trace_errors] or ["- None"])])
    lines.extend(["", "## Final Traceability Conclusion", "- Traceability incomplete." if trace_errors else "- Traceability complete for currently generated artifacts."])
    return "\n".join(lines) + "\n"


def _error(code: str, message: str, path: str) -> dict[str, str]:
    return {"code": code, "message": message, "path": path, "severity": "ERROR"}


def _warning(code: str, message: str, path: str) -> dict[str, str]:
    return {"code": code, "message": message, "path": path, "severity": "WARNING"}


def _info(code: str, message: str, path: str) -> dict[str, str]:
    return {"code": code, "message": message, "path": path, "severity": "INFO"}


def run_all(repo_root: Path, formats: list[str] | None = None) -> dict[str, Any]:
    formats = normalize_formats(formats)
    ensure_output_dirs(repo_root)
    scan(repo_root)
    intake(repo_root)
    feature_map(repo_root)
    proof_check(repo_root)
    manual(repo_root, formats=formats)
    application(repo_root)
    code_doc(repo_root, formats=formats)
    return validate(repo_root)


def clean(repo_root: Path) -> None:
    clean_outputs_dir(repo_root)


def evals(repo_root: Path) -> dict[str, Any]:
    ensure_output_dirs(repo_root)
    cases = [
        _eval_default_failure(repo_root),
        _eval_approved_ready(repo_root),
        _eval_core_fact_status_block(repo_root),
        _eval_published_date_required(repo_root),
        _eval_rule_provenance_downgrade(repo_root),
        _eval_manual_pending_blocks(repo_root),
    ]
    passed = [case for case in cases if case["passed"]]
    failed = [case for case in cases if not case["passed"]]
    report = {"passed": len(passed), "failed": len(failed), "cases": cases}
    output_root = repo_root / "softcopy" / "outputs" / "validation"
    write_json(output_root / "eval_report.json", report)
    write_text(output_root / "eval_report.md", _render_eval_report(report))
    return report


def _eval_project(repo_root: Path) -> Path:
    source = repo_root / "examples" / "minimal-project"
    if not source.exists():
        raise RuntimeError("Eval fixture missing: examples/minimal-project")
    temp_root = Path(tempfile.mkdtemp(prefix="softcopy-eval-"))
    target = temp_root / "minimal-project"
    shutil.copytree(source, target)
    init_project(target)
    return target


def _apply_approved_demo_bundle(project: Path) -> None:
    docs = project / "docs"
    shutil.copy2(docs / "project_facts.confirmed.example.yaml", project / "softcopy" / "project_facts.yaml")
    shutil.copy2(docs / "feature_map.approved.example.yaml", project / "softcopy" / "feature_map.yaml")
    shutil.copy2(docs / "manual_manifest.approved.example.yaml", project / "softcopy" / "manual_manifest.yaml")
    shutil.copy2(docs / "ownership_evidence.approved.example.yaml", project / "softcopy" / "ownership_evidence.yaml")


def _eval_case(name: str, check: Any) -> dict[str, Any]:
    try:
        detail = check()
        return {"name": name, "passed": True, "detail": detail}
    except Exception as exc:
        return {"name": name, "passed": False, "detail": str(exc)}


def _eval_default_failure(repo_root: Path) -> dict[str, Any]:
    def check() -> str:
        project = _eval_project(repo_root)
        result = run_all(project, formats=["md"])
        codes = {item["code"] for item in result["errors"]}
        if result["ready"] or "core_required_fact_not_confirmed" not in codes:
            raise AssertionError("Default fixture must fail on unconfirmed core facts.")
        return "default fixture failed as expected"

    return _eval_case("default_facts_fail", check)


def _eval_approved_ready(repo_root: Path) -> dict[str, Any]:
    def check() -> str:
        project = _eval_project(repo_root)
        _apply_approved_demo_bundle(project)
        result = run_all(project, formats=["md"])
        if not result["ready"]:
            raise AssertionError(f"Approved fixture did not become ready: {result['errors']}")
        if not (project / "softcopy" / "outputs" / "package" / "READY_TO_SUBMIT.flag").exists():
            raise AssertionError("READY_TO_SUBMIT.flag missing.")
        return "approved fixture is ready"

    return _eval_case("approved_bundle_ready", check)


def _eval_core_fact_status_block(repo_root: Path) -> dict[str, Any]:
    def check() -> str:
        project = _eval_project(repo_root)
        _apply_approved_demo_bundle(project)
        facts_path = project / "softcopy" / "project_facts.yaml"
        facts = load_yaml(facts_path, {})
        facts["facts"]["version"]["status"] = "derived"
        write_yaml(facts_path, facts)
        run_all(project, formats=["md"])
        result = validate(project)
        if "core_required_fact_not_confirmed" not in {item["code"] for item in result["errors"]}:
            raise AssertionError("Derived core fact was not blocked.")
        return "derived core fact blocked"

    return _eval_case("core_fact_status_block", check)


def _eval_published_date_required(repo_root: Path) -> dict[str, Any]:
    def check() -> str:
        project = _eval_project(repo_root)
        _apply_approved_demo_bundle(project)
        facts_path = project / "softcopy" / "project_facts.yaml"
        facts = load_yaml(facts_path, {})
        facts["facts"]["first_publication_status"]["value"] = "published"
        facts["facts"]["first_publication_date"]["status"] = "needs_confirmation"
        write_yaml(facts_path, facts)
        run_all(project, formats=["md"])
        result = validate(project)
        if "conditional_required_fact_not_confirmed" not in {item["code"] for item in result["errors"]}:
            raise AssertionError("Published-path first publication date was not required.")
        return "published date condition enforced"

    return _eval_case("published_date_required", check)


def _eval_rule_provenance_downgrade(repo_root: Path) -> dict[str, Any]:
    def check() -> str:
        project = _eval_project(repo_root)
        _apply_approved_demo_bundle(project)
        run_all(project, formats=["md"])
        rules_path = project / "softcopy" / "rules" / "registration_rules.yaml"
        rules = load_yaml(rules_path, {})
        rules["rules"][0]["source_ref"] = ""
        write_yaml(rules_path, rules)
        result = validate(project)
        warnings = {item["code"] for item in result["warnings"]}
        if "rule_provenance_incomplete" not in warnings:
            raise AssertionError("Missing rule provenance did not downgrade to warning.")
        if any(item.get("code") == "rule_provenance_incomplete" and item.get("severity") == "ERROR" for item in result["errors"]):
            raise AssertionError("Incomplete provenance produced hard error.")
        return "incomplete rule provenance downgraded"

    return _eval_case("rule_provenance_downgrade", check)


def _eval_manual_pending_blocks(repo_root: Path) -> dict[str, Any]:
    def check() -> str:
        project = _eval_project(repo_root)
        _apply_approved_demo_bundle(project)
        manifest_path = project / "softcopy" / "manual_manifest.yaml"
        manifest = load_yaml(manifest_path, {})
        manifest["manifest_status"] = "pending_review"
        write_yaml(manifest_path, manifest)
        run_all(project, formats=["md"])
        result = validate(project)
        if "manual_manifest_not_approved_for_readiness" not in {item["code"] for item in result["errors"]}:
            raise AssertionError("Pending manual manifest did not block readiness.")
        return "pending manual manifest blocked"

    return _eval_case("manual_pending_blocks", check)


def _render_eval_report(report: dict[str, Any]) -> str:
    lines = ["# Eval Report", "", f"- Passed: {report['passed']}", f"- Failed: {report['failed']}", "", "## Cases"]
    for case in report["cases"]:
        status = "PASS" if case["passed"] else "FAIL"
        lines.append(f"- `{status}` {case['name']}: {case['detail']}")
    return "\n".join(lines) + "\n"
