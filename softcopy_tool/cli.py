#!/usr/bin/env python3

from __future__ import annotations

import argparse
from pathlib import Path

from . import __version__
from . import workflow


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="softcopy_tool")
    parser.add_argument("--version", action="version", version=f"softcopy_tool {__version__}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="migrate the skill pack into a target repository")
    init_parser.add_argument("--target", required=True)

    for command in ["intake", "scan", "feature-map", "proof-check", "application", "code-doc", "manual", "validate", "run-all", "clean"]:
        item = subparsers.add_parser(command)
        item.add_argument("--repo-root", default=".")

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
    }
    result = dispatch[args.command](repo_root)
    if args.command == "validate" and isinstance(result, dict):
        print(f"errors={len(result['errors'])} warnings={len(result['warnings'])} ready={result['ready']}")
    else:
        print(f"{args.command} completed for {repo_root}")
    return 0
