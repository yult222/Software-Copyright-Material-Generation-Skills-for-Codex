# SoftCopy Verified Review TODO

Execution status: completed.

This file records the verified issues from `review.txt` and the fixes applied in the current checkout. False, outdated, or style-only claims were ignored.

Verification:
- `/opt/miniconda3/bin/python3.13 -m unittest discover -s tests`
- `/opt/miniconda3/bin/python3.13 -m compileall softcopy_tool tests`
- `/opt/miniconda3/bin/python3.13 -m softcopy_tool evals --repo-root .`
- `rg -n "errors=\"ignore\"|line\[:120\]|repo_root / file_ref|mkdtemp|ruby -e" softcopy_tool tests`

## P0: Keep Local `file_ref` Paths Inside `repo_root`

Status: completed.

Evidence:
- `softcopy_tool/workflow.py` validated local ownership evidence with `(repo_root / file_ref).exists()`.
- It did not resolve the path or check containment under `repo_root`.

Implemented:
- Added `_resolve_local_file_ref(repo_root, file_ref)`.
- Rejected absolute local paths.
- Resolved relative paths and required them to remain under `repo_root.resolve()`.
- Kept `http://`, `https://`, and `app://` as external references.
- Added tests for escaping `..` paths and valid in-repo paths.

Acceptance result:
- `../outside.txt` now produces `required_ownership_document_file_ref_invalid` even when the target exists.
- Valid in-repo proof files still pass validation.

## P0: Stop Silently Ignoring Source Encoding Errors

Status: completed.

Evidence:
- `softcopy_tool/workflow.py` read source files with `errors="ignore"` in scan and source-evidence paths.

Implemented:
- Removed silent `errors="ignore"` source reads.
- Added `_read_source_text`, which first tries strict UTF-8.
- Invalid UTF-8 is decoded with replacement only after recording a `source_file_decode_replacement` warning.
- Added scan output warnings to `repo_scan.json` and `repo_scan_report.md`.
- Added a test for invalid UTF-8 source files.

Acceptance result:
- Invalid source encoding no longer disappears silently.
- Scan output records the affected file and warning code.

## P1: Wrap Long PDF Lines Instead of Truncating Them

Status: completed.

Evidence:
- `softcopy_tool/renderers.py` wrote PDF text with `line[:120]`.

Implemented:
- Replaced fixed slicing with `_wrap_pdf_line`.
- Used ReportLab `Canvas.stringWidth` when available.
- Kept a conservative width fallback for tests or nonstandard canvas objects.
- Added a renderer test proving a 180-character line is wrapped and preserved.

Acceptance result:
- PDF rendering preserves all input text instead of dropping characters after position 120.

## P1: Add File-Path Context to YAML and JSON Parse Failures

Status: completed.

Evidence:
- `softcopy_tool/support.py` directly called `json.loads(...)` and `yaml.safe_load(...)`.
- Malformed YAML raised raw parser exceptions without SoftCopy-specific context.

Implemented:
- Added `SoftCopyDataError`.
- Wrapped JSON parse errors, YAML parse errors, and UTF-8 decode errors with file-path context.
- Updated CLI error handling so ordinary data mistakes exit through `argparse` with code 2 and no traceback.
- Added tests for malformed YAML, malformed JSON, and CLI malformed-YAML behavior.

Acceptance result:
- Malformed data errors name the failing file and remain user-facing.

## P2: Report Fallback Font Registration Failures

Status: completed.

Evidence:
- `softcopy_tool/renderers.py` silently swallowed fallback CJK font registration failures.

Implemented:
- Collected fallback font registration failures for `STSong-Light` and candidate font files.
- Included fallback failure details in the final `RenderDependencyError`.
- Preserved the explicit configured-font error path for `SOFTCOPY_CJK_FONT`.
- Added a renderer test proving fallback font failures appear in the error message.

Acceptance result:
- Failed fallback font candidates are visible when PDF rendering cannot find a usable CJK font.

## P2: Add CLI and End-to-End Coverage for Main Workflows

Status: completed.

Evidence:
- The previous suite had 8 tests and no direct `softcopy_tool.cli.main` coverage.

Implemented:
- Added `tests/test_cli.py`.
- Covered `--version`, command dispatch, bad `--formats`, malformed data errors, approved `run-all`, and blocked default `run-all`.
- Added targeted tests for ownership path containment, invalid UTF-8 scan warnings, PDF long-line wrapping, fallback font diagnostics, and structured data parse errors.

Acceptance result:
- The suite now runs 21 tests.
- CLI dispatch and ordinary user error paths are covered.
- The approved fixture becomes ready and the default fixture remains blocked for expected readiness errors.
