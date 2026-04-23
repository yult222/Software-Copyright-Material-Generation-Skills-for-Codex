#!/usr/bin/env python3

from __future__ import annotations

import argparse
import re
from collections import Counter
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

from softcopy_support import write_csv, write_json, write_text, write_yaml


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
    "softcopy",
    "evals",
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


def iter_source_files(repo_root: Path) -> list[Path]:
    files: list[Path] = []
    for path in repo_root.rglob("*"):
        if not path.is_file():
            continue
        if any(part in EXCLUDED_DIRS for part in path.relative_to(repo_root).parts[:-1]):
            continue
        if path.suffix.lower() in SOURCE_SUFFIXES:
            files.append(path)
    return sorted(files)


def count_effective_lines(path: Path) -> int:
    count = 0
    for raw_line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith(("#", "//", "/*", "*", "*/", "--")):
            continue
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
        if "express()" in text or "from 'express'" in text or 'from "express"' in text:
            frameworks.add("Express")
        if "createBrowserRouter(" in text or "<Route" in text:
            frameworks.add("React Router")
        if "next.config" in str(path):
            frameworks.add("Next.js")
    return sorted(frameworks)


def detect_entry_points(repo_root: Path, files: list[Path]) -> list[str]:
    candidates = []
    for path in files:
        if path.name in ENTRYPOINT_NAMES:
            candidates.append(str(path.relative_to(repo_root)))
    return candidates[:20]


def extract_routes(text: str) -> list[str]:
    results: list[str] = []
    for pattern in ROUTE_PATTERNS:
        results.extend(pattern.findall(text))
    deduped: list[str] = []
    seen = set()
    for route in results:
        if route not in seen:
            seen.add(route)
            deduped.append(route)
    return deduped


def detect_routes(repo_root: Path, files: list[Path]) -> list[dict[str, str]]:
    records: list[dict[str, str]] = []
    for path in files:
        text = path.read_text(encoding="utf-8", errors="ignore")
        for route in extract_routes(text):
            records.append(
                {
                    "file": str(path.relative_to(repo_root)),
                    "route": route,
                    "kind": "route",
                }
            )
    return records


def detect_modules(repo_root: Path, files: list[Path]) -> list[dict[str, object]]:
    buckets: dict[str, list[Path]] = {}
    for path in files:
        rel = path.relative_to(repo_root)
        parts = rel.parts
        if len(parts) > 1:
            top = parts[0]
        else:
            top = "root"
        buckets.setdefault(top, []).append(path)

    modules = []
    for name, module_files in sorted(buckets.items()):
        total_lines = sum(count_effective_lines(path) for path in module_files)
        modules.append(
            {
                "name": name,
                "paths": [str(path.relative_to(repo_root)) for path in module_files[:10]],
                "effective_code_lines": total_lines,
                "rationale": "Top-level source bucket with repository code.",
            }
        )
    return modules[:20]


def detect_candidate_core_files(repo_root: Path, files: list[Path]) -> list[dict[str, object]]:
    ranked = []
    entry_points = set(detect_entry_points(repo_root, files))
    for path in files:
        rel = str(path.relative_to(repo_root))
        loc = count_effective_lines(path)
        priority = 2 if rel in entry_points else 1
        ranked.append((priority, loc, rel))
    ranked.sort(key=lambda item: (-item[0], -item[1], item[2]))
    return [
        {"path": rel, "effective_code_lines": loc, "priority": priority}
        for priority, loc, rel in ranked[:20]
    ]


def scan_repository(repo_root: Path) -> dict[str, object]:
    files = iter_source_files(repo_root)
    language_counter = Counter(LANGUAGE_BY_SUFFIX[path.suffix.lower()] for path in files)
    code_inventory = []
    for path in files:
        code_inventory.append(
            {
                "path": str(path.relative_to(repo_root)),
                "language": LANGUAGE_BY_SUFFIX[path.suffix.lower()],
                "effective_code_lines": count_effective_lines(path),
            }
        )

    repo_scan = {
        "primary_languages": [name for name, _ in language_counter.most_common()],
        "framework_signals": detect_frameworks(repo_root, files),
        "candidate_entry_points": detect_entry_points(repo_root, files),
        "excluded_directories": sorted(EXCLUDED_DIRS),
        "candidate_modules": detect_modules(repo_root, files),
        "candidate_core_files": detect_candidate_core_files(repo_root, files),
        "detected_routes": detect_routes(repo_root, files),
        "code_line_summary": {
            "total_files": len(code_inventory),
            "total_effective_code_lines": sum(item["effective_code_lines"] for item in code_inventory),
        },
    }
    return {"repo_scan": repo_scan, "code_inventory": code_inventory}


def write_outputs(repo_root: Path, scan_data: dict[str, object]) -> None:
    outputs_root = repo_root / "softcopy" / "outputs" / "scan"
    repo_scan = scan_data["repo_scan"]
    code_inventory = scan_data["code_inventory"]

    write_json(outputs_root / "repo_scan.json", repo_scan)
    write_csv(
        outputs_root / "code_inventory.csv",
        code_inventory,
        ["path", "language", "effective_code_lines"],
    )
    write_csv(
        outputs_root / "route_inventory.csv",
        repo_scan["detected_routes"],
        ["file", "route", "kind"],
    )
    write_yaml(outputs_root / "module_candidates.yaml", {"modules": repo_scan["candidate_modules"]})

    languages = [f"- {item}" for item in repo_scan["primary_languages"]] or ["- None"]
    frameworks = [f"- {item}" for item in repo_scan["framework_signals"]] or ["- None"]
    entry_points = [f"- `{item}`" for item in repo_scan["candidate_entry_points"]] or ["- None"]
    modules = [
        f"- {item['name']}: {item['effective_code_lines']} effective lines"
        for item in repo_scan["candidate_modules"]
    ] or ["- None"]
    route_findings = [
        f"- `{item['route']}` in `{item['file']}`"
        for item in repo_scan["detected_routes"][:20]
    ] or ["- None"]
    core_files = [
        f"- `{item['path']}` ({item['effective_code_lines']} lines, priority {item['priority']})"
        for item in repo_scan["candidate_core_files"]
    ] or ["- None"]

    report = [
        "# Repository Scan Report",
        "",
        "## Overview",
        f"- Total source files: {repo_scan['code_line_summary']['total_files']}",
        f"- Total effective code lines: {repo_scan['code_line_summary']['total_effective_code_lines']}",
        "",
        "## Detected Languages",
        *languages,
        "",
        "## Framework Signals",
        *frameworks,
        "",
        "## Candidate Entry Points",
        *entry_points,
        "",
        "## Candidate Modules",
        *modules,
        "",
        "## Route Findings",
        *route_findings,
        "",
        "## Candidate Core Files",
        *core_files,
        "",
        "## Exclusions",
        *[f"- `{item}`" for item in repo_scan["excluded_directories"]],
    ]
    write_text(outputs_root / "repo_scan_report.md", "\n".join(report) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=str(ROOT))
    args = parser.parse_args()
    repo_root = Path(args.repo_root).resolve()
    scan_data = scan_repository(repo_root)
    write_outputs(repo_root, scan_data)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
