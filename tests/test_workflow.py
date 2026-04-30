from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from softcopy_tool import workflow


def _fact(status: str, value: object = "value") -> dict[str, object]:
    return {"status": status, "value": value}


def _required_item(field: str) -> dict[str, object]:
    return {
        "field": field,
        "accepted_statuses": {
            workflow.FORMAL_APPLICATION_GATE: ["confirmed"],
            workflow.READY_TO_SUBMIT_GATE: ["confirmed"],
        },
    }


class WorkflowContractTests(unittest.TestCase):
    def test_draft_mode_uses_formal_gate_accepted_statuses(self) -> None:
        required_facts = {
            "core_required_facts": [_required_item(field) for field in workflow.CORE_FACTS],
            "conditional_required_facts": [],
        }
        for item in required_facts["core_required_facts"]:
            if item["field"] == "version":
                item["accepted_statuses"][workflow.FORMAL_APPLICATION_GATE].append("derived")

        facts = {field: _fact("confirmed") for field in workflow.CORE_FACTS}
        facts["version"] = _fact("derived")

        draft_mode, needs_confirmation = workflow._determine_draft_mode(
            {"facts": facts},
            required_facts,
            {"review_status": "approved"},
        )

        self.assertEqual(draft_mode, "formal")
        self.assertEqual(needs_confirmation, [])

    def test_validate_required_uses_ready_gate_accepted_statuses(self) -> None:
        version = _required_item("version")
        version["accepted_statuses"][workflow.FORMAL_APPLICATION_GATE].append("derived")
        required_facts = {
            "core_required_facts": [version],
            "conditional_required_facts": [],
        }
        project_facts = {"facts": {"version": _fact("derived")}}
        errors: list[dict[str, str]] = []

        workflow._validate_required(project_facts, required_facts, errors)

        self.assertEqual([item["code"] for item in errors], ["core_required_fact_not_confirmed"])

        version["accepted_statuses"][workflow.READY_TO_SUBMIT_GATE].append("derived")
        errors = []
        workflow._validate_required(project_facts, required_facts, errors)

        self.assertEqual(errors, [])

    def test_page_artifact_paths_are_explicit(self) -> None:
        self.assertEqual(
            workflow._page_artifact_path("code_doc"),
            "softcopy/outputs/code_doc/code_pages.json",
        )
        self.assertEqual(
            workflow._page_artifact_path("manual_doc"),
            "softcopy/outputs/manual/manual_pages.json",
        )
        with self.assertRaises(ValueError):
            workflow._page_artifact_path("unknown")


class WorkflowScanTests(unittest.TestCase):
    def test_scan_reads_each_source_file_once(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            source_dir = repo_root / "src"
            source_dir.mkdir()
            first = source_dir / "app.py"
            second = source_dir / "routes.py"
            first.write_text("from fastapi import FastAPI\napp = FastAPI()\n", encoding="utf-8")
            second.write_text("@app.get('/health')\ndef health():\n    return 'ok'\n", encoding="utf-8")
            read_counts: dict[Path, int] = {}
            original_read_text = Path.read_text

            def counted_read_text(path: Path, *args: object, **kwargs: object) -> str:
                if path in {first, second}:
                    read_counts[path] = read_counts.get(path, 0) + 1
                return original_read_text(path, *args, **kwargs)

            with patch.object(Path, "read_text", counted_read_text):
                repo_scan = workflow.scan(repo_root)

            self.assertEqual(read_counts, {first: 1, second: 1})
            self.assertIn("FastAPI", repo_scan["framework_signals"])
            self.assertEqual(repo_scan["detected_routes"][0]["route"], "/health")


if __name__ == "__main__":
    unittest.main()
