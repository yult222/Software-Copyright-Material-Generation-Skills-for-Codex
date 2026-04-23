---
name: softcopy-feature-map
description: Build a reviewed feature map that connects functions to code, manual sections, screenshots, and application claims. Use after repository scanning when formal function boundaries are needed. Do not use for simple provisional drafting without feature review.
---

# softcopy-feature-map

## Purpose

Create `softcopy/feature_map.yaml` as the formal feature boundary file.

## Triggers

- Scan results exist
- Formal function mapping is needed

## Non-triggers

- Facts intake
- Simple provisional application drafting without reviewed feature boundaries

## Required outputs

- `softcopy/feature_map.yaml`
- `softcopy/outputs/feature_map/feature_map_report.md`

## Hard rules

- Each feature must map to code, application claims, and manual sections
- Unapproved feature maps cannot support formal readiness

## Workflow summary

1. Convert scan candidates into feature proposals.
2. Add cross-links to code, manual, and application layers.
3. Mark the feature map pending review until human approval.

