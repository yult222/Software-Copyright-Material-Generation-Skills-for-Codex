from __future__ import annotations

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from softcopy_tool import cli, workflow


class CliTests(unittest.TestCase):
    def test_version_command_exits_successfully(self) -> None:
        stdout = io.StringIO()

        with contextlib.redirect_stdout(stdout):
            with self.assertRaises(SystemExit) as raised:
                cli.main(["--version"])

        self.assertEqual(raised.exception.code, 0)
        self.assertIn("softcopy_tool", stdout.getvalue())

    def test_dispatches_main_workflow_commands(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            cases = [
                ("scan", workflow.scan, {}),
                ("application", workflow.application, None),
                ("code-doc", workflow.code_doc, {}),
                ("manual", workflow.manual, {}),
                ("validate", workflow.validate, {"errors": [], "warnings": [], "ready": False}),
            ]
            for command, target, result in cases:
                with self.subTest(command=command):
                    stdout = io.StringIO()
                    with patch.object(workflow, target.__name__, return_value=result) as mocked:
                        with contextlib.redirect_stdout(stdout):
                            exit_code = cli.main([command, "--repo-root", str(repo_root)])

                    self.assertEqual(exit_code, 0)
                    self.assertTrue(mocked.called)

    def test_bad_formats_exit_with_user_facing_error(self) -> None:
        stderr = io.StringIO()

        with contextlib.redirect_stderr(stderr):
            with self.assertRaises(SystemExit) as raised:
                cli.main(["manual", "--formats", "pdf,bad"])

        self.assertEqual(raised.exception.code, 2)
        self.assertIn("Unsupported output format", stderr.getvalue())

    def test_malformed_yaml_exits_without_traceback(self) -> None:
        with workflow._eval_project(Path(__file__).resolve().parents[1]) as project:
            facts_path = project / "softcopy" / "project_facts.yaml"
            facts_path.write_text("facts: [", encoding="utf-8")
            stderr = io.StringIO()

            with contextlib.redirect_stderr(stderr):
                with self.assertRaises(SystemExit) as raised:
                    cli.main(["intake", "--repo-root", str(project)])

        error_text = stderr.getvalue()
        self.assertEqual(raised.exception.code, 2)
        self.assertIn(str(facts_path), error_text)
        self.assertNotIn("Traceback", error_text)

    def test_run_all_approved_fixture_is_ready(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        with workflow._eval_project(repo_root) as project:
            workflow._apply_approved_demo_bundle(project)
            stdout = io.StringIO()

            with contextlib.redirect_stdout(stdout):
                exit_code = cli.main(["run-all", "--repo-root", str(project)])

            ready_flag = project / "softcopy" / "outputs" / "package" / "READY_TO_SUBMIT.flag"
            self.assertEqual(exit_code, 0)
            self.assertTrue(ready_flag.exists())

    def test_run_all_default_fixture_stays_blocked(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        with workflow._eval_project(repo_root) as project:
            stdout = io.StringIO()

            with contextlib.redirect_stdout(stdout):
                exit_code = cli.main(["run-all", "--repo-root", str(project)])

            ready_flag = project / "softcopy" / "outputs" / "package" / "READY_TO_SUBMIT.flag"
            errors_path = project / "softcopy" / "outputs" / "validation" / "errors.json"
            errors = json.loads(errors_path.read_text(encoding="utf-8"))
            self.assertEqual(exit_code, 0)
            self.assertFalse(ready_flag.exists())
            self.assertIn("core_required_fact_not_confirmed", {item["code"] for item in errors})


if __name__ == "__main__":
    unittest.main()
