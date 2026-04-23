---
name: softcopy-manual
description: Build manual artifacts and maintain the semi-automatic manual manifest workflow. Use when formal manual or design documentation is needed after features are reviewed. Do not use to invent screenshots or UI that do not exist.
---

# softcopy-manual

## Purpose

Produce manual drafts, manifest files, and trace records.

## Triggers

- Approved `feature_map.yaml`
- Need user manual, API manual, design spec, or hybrid manual

## Non-triggers

- No feature boundaries
- No screenshot or command evidence

## Required outputs

- `softcopy/outputs/manual/manual_manifest.stub.yaml`
- `softcopy/manual_manifest.yaml`
- `softcopy/outputs/manual/manual_outline.md`
- `softcopy/outputs/manual/manual.md`
- `softcopy/outputs/manual/manual_report.md`
- `softcopy/outputs/manual/manual_trace.json`

## Optional outputs

- `softcopy/outputs/manual/manual.pdf`

## Hard rules

- Do not invent screenshots or pages
- Manifest must distinguish real UI, API diagrams, and command output
- Unapproved manifest cannot support ready-to-submit

## Workflow summary

1. Build a stub manifest.
2. Let the operator fill screenshot paths and actual steps.
3. Normalize to the formal manifest.
4. Render the manual and trace file.

