---
name: softcopy-code-doc
description: Generate source code evidence materials from approved features and repository evidence. Use when formal source code materials are needed. Do not use before feature boundaries are approved.
---

# softcopy-code-doc

## Purpose

Create source-code evidence selections and rendered materials.

## Triggers

- Approved `feature_map.yaml`
- Code evidence package is required

## Non-triggers

- Provisional drafting only
- Missing or unreviewed feature map

## Required outputs

- `softcopy/outputs/code_doc/code_selection.yaml`
- `softcopy/outputs/code_doc/code_doc.md`
- `softcopy/outputs/code_doc/code_pages.json`
- `softcopy/outputs/code_doc/code_doc_report.md`
- `softcopy/outputs/code_doc/page_trace.json`

## Optional outputs

- `softcopy/outputs/code_doc/code_doc.pdf`
- `softcopy/outputs/code_doc/code_doc.docx`

## Hard rules

- Prefer core business files, not tests or third-party code
- Every page must trace `path`, line range, effective line count, and source ref
- Page rules come only from active `registration_rules.yaml` entries

## Workflow summary

1. Select candidate files from scan and feature map.
2. Paginate code excerpts.
3. Render material and page trace files.
