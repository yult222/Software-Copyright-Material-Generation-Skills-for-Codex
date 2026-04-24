#!/usr/bin/env python3

from __future__ import annotations

import csv
import json
import shutil
import subprocess
from pathlib import Path
from typing import Any, Iterable


REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIRS = [
    "intake",
    "scan",
    "feature_map",
    "application",
    "code_doc",
    "manual",
    "proof_check",
    "validation",
    "traceability",
    "package",
]


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def write_text(path: Path, content: str) -> None:
    ensure_parent(path)
    path.write_text(content, encoding="utf-8")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    ensure_parent(path)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def read_yaml(path: Path) -> Any:
    ruby = r"""
require "yaml"
require "json"
path = ARGV[0]
data = YAML.safe_load(File.read(path), aliases: true)
puts JSON.generate(data)
"""
    result = subprocess.run(
        ["ruby", "-e", ruby, str(path)],
        capture_output=True,
        text=True,
        check=True,
    )
    if not result.stdout.strip():
        return None
    return json.loads(result.stdout)


def write_yaml(path: Path, data: Any) -> None:
    ruby = r"""
require "yaml"
require "json"
data = JSON.parse(STDIN.read)
puts YAML.dump(data)
"""
    ensure_parent(path)
    result = subprocess.run(
        ["ruby", "-e", ruby],
        input=json.dumps(data, ensure_ascii=False),
        capture_output=True,
        text=True,
        check=True,
    )
    path.write_text(result.stdout, encoding="utf-8")


def write_csv(path: Path, rows: Iterable[dict[str, Any]], fieldnames: list[str]) -> None:
    ensure_parent(path)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def load_yaml(path: Path, default: Any) -> Any:
    return read_yaml(path) if path.exists() else default


def load_json(path: Path, default: Any) -> Any:
    return read_json(path) if path.exists() else default


def ensure_output_dirs(repo_root: Path) -> None:
    for name in OUTPUT_DIRS:
        directory = repo_root / "softcopy" / "outputs" / name
        directory.mkdir(parents=True, exist_ok=True)
        (directory / ".gitkeep").touch(exist_ok=True)


def clean_outputs(repo_root: Path) -> None:
    output_root = repo_root / "softcopy" / "outputs"
    for name in OUTPUT_DIRS:
        directory = output_root / name
        if directory.exists():
            for item in directory.iterdir():
                if item.name == ".gitkeep":
                    continue
                if item.is_dir():
                    shutil.rmtree(item)
                else:
                    item.unlink()
        directory.mkdir(parents=True, exist_ok=True)
        (directory / ".gitkeep").touch(exist_ok=True)


def copy_file_if_absent(src: Path, dest: Path, conflicts: list[str], copied: list[str]) -> None:
    if dest.exists():
        conflicts.append(str(dest))
        return
    ensure_parent(dest)
    shutil.copy2(src, dest)
    copied.append(str(dest))


def copy_tree_if_absent(src: Path, dest: Path, conflicts: list[str], copied: list[str]) -> None:
    for src_path in sorted(path for path in src.rglob("*") if path.is_file()):
        rel = src_path.relative_to(src)
        copy_file_if_absent(src_path, dest / rel, conflicts, copied)
