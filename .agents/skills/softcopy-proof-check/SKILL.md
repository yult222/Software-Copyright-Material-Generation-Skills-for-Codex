---
name: softcopy-proof-check
description: Build and validate ownership evidence checklists from the declared development mode. Use when proof documents are needed for formal review. Do not use for unrelated writing or code analysis.
---

# softcopy-proof-check

## Purpose

Create ownership evidence checklists and missing-proof reports.

## Triggers

- Proof or ownership review is required
- `development_mode` is known or needs checklist generation

## Non-triggers

- Generic drafting
- Repository scan without filing context

## Required outputs

- `softcopy/ownership_evidence.yaml`
- `softcopy/outputs/proof_check/proof_checklist.md`
- `softcopy/outputs/proof_check/missing_proofs.md`

## Hard rules

- Use `development_mode`, never `ownership_mode`
- Distinguish required vs optional documents

## Workflow summary

1. Read confirmed or candidate development mode.
2. Generate proof checklist.
3. Mark missing and provided documents separately.

