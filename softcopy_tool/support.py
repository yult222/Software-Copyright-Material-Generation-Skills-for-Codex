#!/usr/bin/env python3

from __future__ import annotations

import csv
import json
from json import JSONDecodeError
import shutil
from pathlib import Path
from typing import Any, Iterable

import yaml


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


class SoftCopyDataError(ValueError):
    pass


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def write_text(path: Path, content: str) -> None:
    ensure_parent(path)
    path.write_text(content, encoding="utf-8")


def read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except JSONDecodeError as exc:
        raise SoftCopyDataError(f"Could not parse JSON file `{path}`: {exc.msg}.") from exc
    except UnicodeDecodeError as exc:
        raise SoftCopyDataError(f"Could not decode JSON file `{path}` as UTF-8.") from exc


def write_json(path: Path, data: Any) -> None:
    ensure_parent(path)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def read_yaml(path: Path) -> Any:
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise SoftCopyDataError(f"Could not parse YAML file `{path}`: {exc}.") from exc
    except UnicodeDecodeError as exc:
        raise SoftCopyDataError(f"Could not decode YAML file `{path}` as UTF-8.") from exc


def write_yaml(path: Path, data: Any) -> None:
    ensure_parent(path)
    path.write_text(
        yaml.safe_dump(data, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )


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
