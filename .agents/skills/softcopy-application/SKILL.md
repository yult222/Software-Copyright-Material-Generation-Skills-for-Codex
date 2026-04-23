---
name: softcopy-application
description: Build a structured application draft from confirmed facts and traceable feature evidence. Use when application materials are needed after intake. Do not use for marketing copy, README work, or unrelated writing tasks.
---

# softcopy-application

## Purpose

Generate application draft artifacts and trace files.

## Triggers

- `project_facts.yaml` exists
- Application draft is requested

## Non-triggers

- Marketing copy
- README edits
- Unrelated legal writing

## Required inputs

- `softcopy/project_facts.yaml`
- optional `softcopy/feature_map.yaml`
- optional `softcopy/ownership_evidence.yaml`
- optional `softcopy/outputs/scan/repo_scan.json`

## Required outputs

- `softcopy/outputs/application/application_fields.json`
- `softcopy/outputs/application/application_draft.md`
- `softcopy/outputs/application/application_review_checklist.md`
- `softcopy/outputs/application/application_trace.json`

## Hard rules

- Critical facts must come from `confirmed` fields only
- If facts or feature review are incomplete, output `provisional` draft mode
- Keep function claims conservative and traceable

## Workflow summary

1. Read facts and supporting evidence.
2. Determine `provisional` or `formal` draft mode.
3. Build structured fields, narrative draft, checklist, and trace file.

