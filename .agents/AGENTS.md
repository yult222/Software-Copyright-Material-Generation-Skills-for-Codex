# SoftCopy Agent Rules

This repository contains the SoftCopy Codex Skill Pack for generating and validating software copyright application materials.

## Global rules

1. Always check `softcopy/project_facts.yaml` before drafting any formal materials.
2. Critical application facts must be `confirmed` before they enter formal outputs.
3. Repository scanning results are candidate evidence, not final legal facts.
4. Never default `first_publication_status` to `unpublished`.
5. Never let `candidate`, `derived`, `needs_confirmation`, or `missing` core facts pass formal readiness.
6. Every blocking field must carry traceable `sources`.
7. Validation must separate `ERROR`, `WARNING`, and `INFO`.
8. Only active rules with complete provenance metadata may produce hard rule errors.
9. Do not treat local filing-office guidance as globally active unless the filing office matches.
10. All generated outputs must be written under `softcopy/outputs/`.
11. Prefer structured intermediate files over one-shot prose generation.
12. Never output `READY_TO_SUBMIT` before validation passes.

## Current implementation scope

The repository currently includes:

- contracts
- rules
- schemas
- skill boundaries
- shared `softcopy_tool` CLI and workflow implementation
- migration-safe `init`
- repository scan, intake, feature map, proof check, application, code-doc, manual, validation, clean, and eval commands
- code/manual page trace generation
- optional PDF/DOCX rendering through extras
- strict readiness gate for confirmed facts, approved feature/manual/proof evidence, traceability, and active rule provenance
