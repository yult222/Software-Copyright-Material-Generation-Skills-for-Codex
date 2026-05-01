from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from softcopy_tool.support import SoftCopyDataError, load_yaml, read_json, read_yaml, write_yaml


class SupportYamlTests(unittest.TestCase):
    def test_yaml_round_trip_preserves_chinese_text(self) -> None:
        payload = {
            "facts": {
                "software_name_full": {
                    "value": "软件著作权材料生成工具",
                    "status": "confirmed",
                }
            },
            "notes": ["中文内容", "ASCII content"],
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "facts.yaml"

            write_yaml(path, payload)

            self.assertEqual(read_yaml(path), payload)
            self.assertIn("软件著作权材料生成工具", path.read_text(encoding="utf-8"))

    def test_read_yaml_empty_file_returns_none(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "empty.yaml"
            path.write_text("", encoding="utf-8")

            self.assertIsNone(read_yaml(path))

    def test_load_yaml_missing_file_returns_default(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            default = {"status": "missing"}

            self.assertEqual(load_yaml(Path(temp_dir) / "missing.yaml", default), default)

    def test_read_yaml_error_includes_path(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "bad.yaml"
            path.write_text("facts: [", encoding="utf-8")

            with self.assertRaises(SoftCopyDataError) as raised:
                read_yaml(path)

            self.assertIn(str(path), str(raised.exception))
            self.assertIn("Could not parse YAML", str(raised.exception))

    def test_read_json_error_includes_path(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "bad.json"
            path.write_text("{", encoding="utf-8")

            with self.assertRaises(SoftCopyDataError) as raised:
                read_json(path)

            self.assertIn(str(path), str(raised.exception))
            self.assertIn("Could not parse JSON", str(raised.exception))


if __name__ == "__main__":
    unittest.main()
