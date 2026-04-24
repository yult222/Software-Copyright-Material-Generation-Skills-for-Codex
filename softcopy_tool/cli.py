#!/usr/bin/env python3

from __future__ import annotations

import argparse
from pathlib import Path

from . import __version__
from . import workflow
from .renderers import RenderDependencyError, normalize_formats


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="softcopy_tool")
    parser.add_argument("--version", action="version", version=f"softcopy_tool {__version__}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="migrate the skill pack into a target repository")
    init_parser.add_argument("--target", required=True)

    for command in ["intake", "scan", "feature-map", "proof-check", "application", "validate", "clean", "evals"]:
        item = subparsers.add_parser(command)
        item.add_argument("--repo-root", default=".")

    for command in ["code-doc", "manual", "run-all"]:
        item = subparsers.add_parser(command)
        item.add_argument("--repo-root", default=".")
        item.add_argument("--formats", default="md", help="comma-separated output formats: md,pdf,docx")

    args = parser.parse_args(argv)
    if args.command == "init":
        report = workflow.init_project(Path(args.target))
        print(f"initialized target={report['target']} copied={len(report['copied'])} conflicts={len(report['conflicts'])}")
        return 0

    repo_root = Path(args.repo_root).resolve()
    dispatch = {
        "intake": workflow.intake,
        "scan": workflow.scan,
        "feature-map": workflow.feature_map,
        "proof-check": workflow.proof_check,
        "application": workflow.application,
        "code-doc": workflow.code_doc,
        "manual": workflow.manual,
        "validate": workflow.validate,
        "run-all": workflow.run_all,
        "clean": workflow.clean,
        "evals": workflow.evals,
    }
    try:
        if args.command in {"code-doc", "manual", "run-all"}:
            result = dispatch[args.command](repo_root, formats=normalize_formats(args.formats))
        else:
            result = dispatch[args.command](repo_root)
    except (RenderDependencyError, ValueError) as exc:
        parser.error(str(exc))
        return 2
    if args.command == "validate" and isinstance(result, dict):
        print(f"errors={len(result['errors'])} warnings={len(result['warnings'])} ready={result['ready']}")
    else:
        print(f"{args.command} completed for {repo_root}")
    return 0
