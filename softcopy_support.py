#!/usr/bin/env python3

from __future__ import annotations

import csv
import json
import subprocess
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parent


def repo_root() -> Path:
    return ROOT


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    ensure_parent(path)
    path.write_text(content, encoding="utf-8")


def read_json(path: Path) -> Any:
    return json.loads(read_text(path))


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


def load_if_exists_yaml(path: Path, default: Any) -> Any:
    return read_yaml(path) if path.exists() else default


def load_if_exists_json(path: Path, default: Any) -> Any:
    return read_json(path) if path.exists() else default

