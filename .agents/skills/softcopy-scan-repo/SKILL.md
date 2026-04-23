---
name: softcopy-scan-repo
description: Analyze a repository for candidate stack, entry points, modules, routes, and code evidence files. Use after intake when repository evidence is needed. Do not use to finalize legal facts.
---

# softcopy-scan-repo

## Purpose

Produce structured candidate evidence from the repository.

## Triggers

- `project_facts.yaml` exists
- Need candidate modules, routes, languages, or code evidence files

## Non-triggers

- Facts-only intake work
- Final application validation without repository changes

## Required outputs

- `softcopy/outputs/scan/repo_scan.json`
- `softcopy/outputs/scan/module_candidates.yaml`
- `softcopy/outputs/scan/code_inventory.csv`
- `softcopy/outputs/scan/route_inventory.csv`
- `softcopy/outputs/scan/repo_scan_report.md`

## Hard rules

- Treat all outputs as candidate evidence
- Exclude tests, third-party code, build artifacts, and generated directories by default
- Do not finalize legal facts here

## Workflow summary

1. Walk the repository with exclusions.
2. Detect languages, entry points, modules, and routes.
3. Count effective lines of code.
4. Write structured evidence files and a summary report.

