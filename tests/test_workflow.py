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


class WorkflowOwnershipTests(unittest.TestCase):
    def test_local_file_ref_must_stay_inside_repo_root(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            repo_root = base / "repo"
            repo_root.mkdir()
            outside = base / "outside.txt"
            outside.write_text("secret", encoding="utf-8")
            ownership = {
                "evidence_status": "approved",
                "required_documents": [
                    {
                        "required": True,
                        "provided": True,
                        "name": "Owner proof",
                        "file_ref": "../outside.txt",
                    }
                ],
            }
            errors: list[dict[str, str]] = []

            workflow._validate_ownership(
                repo_root,
                {"facts": {"development_mode": {"value": "original"}}},
                ownership,
                errors,
            )

            self.assertIn("required_ownership_document_file_ref_invalid", {item["code"] for item in errors})

    def test_valid_local_file_ref_passes_existence_check(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            proof = repo_root / "docs" / "owner.txt"
            proof.parent.mkdir()
            proof.write_text("owner", encoding="utf-8")
            ownership = {
                "evidence_status": "approved",
                "required_documents": [
                    {
                        "required": True,
                        "provided": True,
                        "name": "Owner proof",
                        "file_ref": "docs/owner.txt",
                    }
                ],
            }
            errors: list[dict[str, str]] = []

            workflow._validate_ownership(
                repo_root,
                {"facts": {"development_mode": {"value": "original"}}},
                ownership,
                errors,
            )

            self.assertEqual(errors, [])


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

    def test_scan_reports_invalid_utf8_source_warning(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            source_dir = repo_root / "src"
            source_dir.mkdir()
            broken = source_dir / "bad.py"
            broken.write_bytes(b"print('ok')\xff\n")

            repo_scan = workflow.scan(repo_root)

            self.assertEqual(
                [item["code"] for item in repo_scan["warnings"]],
                ["source_file_decode_replacement"],
            )
            report = repo_root / "softcopy" / "outputs" / "scan" / "repo_scan_report.md"
            self.assertIn("source_file_decode_replacement", report.read_text(encoding="utf-8"))


class WorkflowChineseMaterialTests(unittest.TestCase):
    def test_formal_materials_use_chinese_titles(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        with workflow._eval_project(repo_root) as project:
            workflow._apply_approved_demo_bundle(project)
            workflow.run_all(project, formats=["md"])

            application = (
                project / "softcopy" / "outputs" / "application" / "application_draft.md"
            ).read_text(encoding="utf-8")
            code_doc = (
                project / "softcopy" / "outputs" / "code_doc" / "code_doc.md"
            ).read_text(encoding="utf-8")
            manual = (
                project / "softcopy" / "outputs" / "manual" / "manual.md"
            ).read_text(encoding="utf-8")

        self.assertIn("# 软件著作权登记申请表草稿", application)
        self.assertIn("# 源程序鉴别材料", code_doc)
        self.assertIn("# 接口说明文档", manual)
        combined = "\n".join([application, code_doc, manual])
        self.assertNotIn("Application Draft", combined)
        self.assertNotIn("Source Code Evidence Draft", combined)
        self.assertNotIn("Manual Draft", combined)
        self.assertNotIn("Describe how to use", combined)
        self.assertNotIn("- None", combined)

    def test_manual_stub_goal_is_chinese(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            softcopy = repo_root / "softcopy"
            softcopy.mkdir()
            workflow.write_yaml(
                softcopy / "project_facts.yaml",
                {"facts": {"project_type": {"value": "backend_service"}}},
            )
            workflow.write_yaml(
                softcopy / "feature_map.yaml",
                {
                    "review_status": "approved",
                    "features": [
                        {
                            "name": {"value": "数据查询"},
                        }
                    ],
                },
            )

            workflow.manual(repo_root, formats=["md"])

            stub = (
                repo_root / "softcopy" / "outputs" / "manual" / "manual_manifest.stub.yaml"
            ).read_text(encoding="utf-8")

        self.assertIn("说明如何使用或调用", stub)
        self.assertNotIn("Describe how to use", stub)


if __name__ == "__main__":
    unittest.main()
