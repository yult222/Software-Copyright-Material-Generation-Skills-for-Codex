# SoftCopy Code Review TODO

This file records issues verified against the current repository. Items are ordered by practical risk and impact.

Execution status: completed.

Verification:
- `/opt/miniconda3/bin/python3.13 -m compileall softcopy_tool tests`
- `/opt/miniconda3/bin/python3.13 -m unittest discover -s tests`
- `TMPDIR=/private/tmp /opt/miniconda3/bin/python3.13 -m softcopy_tool evals --repo-root .`
- `/opt/miniconda3/bin/python3.13 -m pip install --target /private/tmp/softcopy-install-py313 . --upgrade`
- `PYTHONPATH=/private/tmp/softcopy-install-py313 /private/tmp/softcopy-install-py313/bin/softcopy-tool --version`
- `PYTHONPATH=/private/tmp/softcopy-render-deps /opt/miniconda3/bin/python3.13 -c "... _render_pdf(..., '软件著作权登记') ..."`

## P0: Remove or Harden the Ruby YAML Runtime Dependency

Status: completed.

Evidence:
- `softcopy_tool/support.py` reads and writes YAML by spawning `ruby -e ...`.
- `pyproject.toml` has `dependencies = []`.
- `README.md` documents Ruby as a prerequisite, but the CLI does not preflight Ruby availability and package metadata cannot express this runtime requirement.

Problem:
- A missing Ruby runtime fails at the first YAML operation with a low-level `FileNotFoundError`.
- Every YAML read/write starts a subprocess.
- The dependency policy is ambiguous: the project claims a zero-dependency CLI, but in practice depends on a system Ruby executable.

Recommended solution:
1. Choose one dependency policy.
2. Preferred: move YAML I/O to Python and add `PyYAML>=6` to `dependencies`.
   - Replace `read_yaml` / `write_yaml` in `softcopy_tool/support.py` with `yaml.safe_load` and `yaml.safe_dump(..., allow_unicode=True, sort_keys=False)`.
   - Update README prerequisites to remove Ruby.
   - Add focused tests for UTF-8 Chinese YAML round trips, empty YAML files, and missing-file defaults through `load_yaml`.
3. If zero Python dependencies must be preserved, keep Ruby but add a central preflight:
   - Use `shutil.which("ruby")` before subprocess calls.
   - Raise a project-specific error with installation guidance.
   - Update CLI handling so the message is user-facing and exits with code 2.

Acceptance criteria:
- Running any command without Ruby either succeeds because Python YAML is used, or fails with an explicit actionable SoftCopy error before work starts.
- Chinese text survives YAML read/write round trips.

Implemented:
- Replaced Ruby subprocess YAML I/O with PyYAML.
- Added `PyYAML>=6` to package dependencies.
- Updated README prerequisites and render dependency wording.
- Added unittest coverage for Chinese YAML round trips, empty YAML, and missing-file defaults.

## P0: Clean Up Eval Temporary Directories

Status: completed.

Evidence:
- `_eval_project` in `softcopy_tool/workflow.py` uses `tempfile.mkdtemp(prefix="softcopy-eval-")`.
- Each eval case calls `_eval_project`, but no caller removes the temporary root after the case finishes.

Problem:
- Repeated `softcopy-tool evals` runs leak directories under the system temp folder.
- Failed evals leak the same way because no cleanup path exists.

Recommended solution:
1. Change eval case execution to own a temporary directory context.
2. Prefer a helper that yields an initialized project inside `tempfile.TemporaryDirectory(prefix="softcopy-eval-")`.
3. Keep cleanup outside `_eval_project` only if the caller has a `try/finally` with `shutil.rmtree(temp_root, ignore_errors=True)`.

Acceptance criteria:
- `softcopy-tool evals` leaves no `softcopy-eval-*` directories after success or failure.
- Eval tests still have useful failure messages.

Implemented:
- Converted eval fixture creation to a `TemporaryDirectory` context manager.
- Verified no `softcopy-eval-*` directories remain under `/private/tmp` after evals.

## P1: Make PDF Rendering Support Chinese Text

Status: completed.

Evidence:
- `_render_pdf` in `softcopy_tool/renderers.py` converts every line through `line.encode("latin-1", "replace").decode("latin-1")`.

Problem:
- Chinese characters are replaced with `?`.
- The PDF format is therefore not usable for the tool's main Chinese software copyright workflow.

Recommended solution:
1. Register and use a CJK-capable font in ReportLab.
2. Provide a deterministic font lookup order:
   - user-configured font path through an environment variable such as `SOFTCOPY_CJK_FONT`;
   - common macOS fonts such as `/System/Library/Fonts/PingFang.ttc`;
   - common Linux fonts such as Noto CJK if present;
   - clear error if `pdf` is requested and no CJK-capable font is available.
3. Remove the Latin-1 lossy conversion.
4. Add a smoke test or script that renders Chinese text and extracts or visually checks that output is not question marks.

Acceptance criteria:
- A generated PDF containing `软件著作权登记` preserves those characters.
- Missing font failures explain how to configure the font.

Implemented:
- Registered ReportLab CJK fonts instead of Latin-1 replacement.
- Added `SOFTCOPY_CJK_FONT` support for explicit font paths.
- Added a renderer unit test proving Chinese text is passed to PDF drawing unchanged.
- Rendered a real PDF smoke file with `软件著作权登记` through ReportLab.

## P1: Honor `accepted_statuses` from `required_facts.yaml`

Status: completed.

Evidence:
- `softcopy/contracts/required_facts.yaml` defines `accepted_statuses.formal_application_ready` and `accepted_statuses.ready_to_submit`.
- `_determine_draft_mode` and `_validate_required` in `softcopy_tool/workflow.py` hard-code `status != "confirmed"` instead of reading those contract values.

Problem:
- The contract file is not the actual machine source of truth for accepted statuses.
- Changing `accepted_statuses` in the contract will not change application or validation behavior.

Recommended solution:
1. Add a helper such as `_accepted_statuses(required_item, gate)` that defaults to `["confirmed"]` if the contract omits the gate.
2. Use it in both `_determine_draft_mode` and `_validate_required`.
3. Apply the same contract-driven logic to `conditional_required_facts`, not only `core_required_facts`.
4. Add eval cases where a non-`confirmed` status is allowed by the contract for one gate and rejected for another.

Acceptance criteria:
- Validation behavior changes when `required_facts.yaml` changes.
- Existing default behavior remains `confirmed` only.

Implemented:
- Added contract-driven accepted-status helpers.
- Applied formal and ready-to-submit gates to core and conditional facts.
- Added an eval case proving one gate can allow a status while another rejects it.

## P2: Remove Unreachable CLI Return

Status: completed.

Evidence:
- `softcopy_tool/cli.py` calls `parser.error(str(exc))` and then has `return 2`.
- `argparse.ArgumentParser.error()` exits by raising `SystemExit(2)`.

Problem:
- The return is dead code and makes the control flow misleading.

Recommended solution:
- Delete the unreachable `return 2`, or replace `parser.error(...)` with explicit `print(..., file=sys.stderr)` plus `return 2`.

Acceptance criteria:
- CLI error handling has one clear exit path.

Implemented:
- Removed the unreachable `return 2` after `parser.error(...)`.

## P2: Replace Fragile Page Artifact Path Construction

Status: completed.

Evidence:
- `_validate_page_window` builds paths with inline conditionals and `kind.split("_")[0]`.

Problem:
- The current result happens to produce `code_pages.json` and `manual_pages.json`, but the logic depends on string splitting rather than an explicit artifact map.
- Adding another page material kind would be easy to break.

Recommended solution:
1. Add an explicit mapping:
   - `code_doc -> softcopy/outputs/code_doc/code_pages.json`
   - `manual_doc -> softcopy/outputs/manual/manual_pages.json`
2. Reuse the same map in `_validate_page_window` and `_validate_min_lines`.
3. Raise a clear internal error if an unknown kind is passed.

Acceptance criteria:
- No validation path is built through `kind.split(...)`.
- Error paths still point to the exact JSON artifact.

Implemented:
- Added explicit `PAGE_ARTIFACTS` mapping and `_page_artifact_path`.
- Reused the mapping in page-window and min-lines validation.
- Added unit coverage for both known artifact paths and unknown kinds.

## P2: Avoid Duplicate Source File Reads During Scan

Status: completed.

Evidence:
- `detect_frameworks` reads up to 200 source files.
- `scan` reads the same source files again for route extraction.
- `_detect_modules` and candidate calculations also recalculate line counts separately.

Problem:
- Small projects are unaffected, but larger repositories pay avoidable repeated I/O.

Recommended solution:
1. In `scan`, build a per-file analysis cache containing relative path, language, text, effective line count, and extracted routes.
2. Pass cached text to framework detection.
3. Reuse cached effective line counts for module summaries.

Acceptance criteria:
- Each scanned source file is read at most once during `scan`.
- `repo_scan.json`, `code_inventory.csv`, `route_inventory.csv`, and `module_candidates.yaml` remain behaviorally equivalent.

Implemented:
- Added `SourceFileAnalysis` cache for text, language, route, and effective-line data.
- Reused cached analysis for framework detection, route extraction, module summaries, and core-file ranking.
- Added unit coverage proving each source file is read once during scan.

## P3: Clarify Packaging Metadata

Status: completed.

Evidence:
- `pyproject.toml` has no `[build-system]` table.

Problem:
- Build backend selection relies on tooling defaults.
- Older or stricter packaging tools may behave inconsistently.

Recommended solution:
1. Add an explicit build system, for example:
   ```toml
   [build-system]
   requires = ["setuptools>=69"]
   build-backend = "setuptools.build_meta"
   ```
2. Verify local install in a clean virtual environment.

Acceptance criteria:
- `python -m pip install .` works in a clean Python 3.10+ environment.
- The console script `softcopy-tool` is installed and runnable.

Implemented:
- Added an explicit `[build-system]`.
- Added explicit setuptools package/module selection to avoid flat-layout discovery failures.
- Updated license metadata to SPDX string form.
- Verified target install and console script version output under Python 3.13.

## P3: Use One Version Source

Status: completed.

Evidence:
- `pyproject.toml` defines version `0.1.0`.
- `softcopy_tool/__init__.py` also defines `__version__ = "0.1.0"`.

Problem:
- Releases can drift if one value is updated and the other is missed.

Recommended solution:
1. Read the installed package version with `importlib.metadata.version("softcopy-codex-skill-pack")`.
2. Keep a development fallback only for direct source-tree execution.
3. Use the same value for `softcopy-tool --version`.

Acceptance criteria:
- Version changes require editing one authoritative source.
- `softcopy-tool --version` still works from an installed package.

Implemented:
- `softcopy_tool.__version__` now reads installed package metadata through `importlib.metadata`.
- Direct source-tree fallback is `0+unknown`, avoiding a second hard-coded release version.

## P3: Split Oversized Lines in `workflow.py`

Status: completed.

Evidence:
- Several lines in `softcopy_tool/workflow.py` exceed 200 characters, especially report construction, trace payload construction, and long validation errors.

Problem:
- These lines make reviews and future changes harder.

Recommended solution:
1. Extract long payloads into named variables.
2. Use multi-line list/dict literals for generated reports.
3. Keep user-facing strings readable without changing generated output.

Acceptance criteria:
- No source line in `softcopy_tool/workflow.py` exceeds the project's chosen limit, for example 120 characters.
- Generated artifacts remain unchanged except for harmless whitespace if explicitly accepted.

Implemented:
- Split oversized report, trace, validation, ownership, page-rule, and eval lines.
- Verified no source line in `softcopy_tool/*.py` or `tests/*.py` exceeds 120 characters.
