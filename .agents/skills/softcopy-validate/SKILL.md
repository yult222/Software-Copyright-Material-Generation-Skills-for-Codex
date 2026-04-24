---
name: softcopy-validate
description: Validate completeness, consistency, traceability, and submission readiness across generated filing materials. Use after artifacts are produced. Do not use for minor copy-editing or non-filing tasks.
---

# softcopy-validate

## Purpose

Run readiness checks and write validation outputs.

## Triggers

- Application or evidence artifacts already exist
- Submission readiness needs checking

## Non-triggers

- Minor wording edits
- Unrelated repository analysis

## Required outputs

- `softcopy/outputs/validation/validation_report.md`
- `softcopy/outputs/validation/errors.json`
- `softcopy/outputs/validation/warnings.json`
- `softcopy/outputs/traceability/traceability_report.md`

## Conditional output

- `softcopy/outputs/package/READY_TO_SUBMIT.flag` only when no blocking errors remain

## Hard rules

- Core required facts must be `confirmed`
- Feature map, manual manifest, and ownership evidence must be `approved`
- Blocking fields must have trace sources
- Only active rules with complete provenance may emit hard rule errors
- Active page rules must be checked against generated code/manual page traces

## Workflow summary

1. Read contracts, facts, artifacts, and rules.
2. Run contract and consistency checks.
3. Evaluate active rules.
4. Write validation and traceability reports.
