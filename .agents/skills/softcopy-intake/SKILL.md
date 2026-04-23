---
name: softcopy-intake
description: Collect and normalize explicit software copyright application facts. Use when a soft copyright workflow starts or project facts are missing. Do not use for generic debugging, code review, or README summarization.
---

# softcopy-intake

## Purpose

Collect, confirm, and normalize application facts into `softcopy/project_facts.yaml`.

## Triggers

- Start of a software copyright workflow
- Missing or inconsistent `project_facts.yaml`
- Need to confirm legal/application facts before drafting

## Non-triggers

- Generic debugging
- README summarization
- Code review unrelated to filing materials

## Required inputs

- user instructions
- existing project metadata
- repository metadata as candidate evidence only

## Required outputs

- `softcopy/project_facts.yaml`
- `softcopy/outputs/intake/intake_report.md`

## Hard rules

- Never fabricate critical facts
- Never default `first_publication_status` to `unpublished`
- Never use git timestamps as completion date
- Only `confirmed` core facts may later enter formal materials

## Workflow summary

1. Read existing facts if present.
2. Collect explicit facts and candidate evidence.
3. Mark unresolved facts as `needs_confirmation`.
4. Emit a report with confirmed, candidate, missing, and conflicting facts.

