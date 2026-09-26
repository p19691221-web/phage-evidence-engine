# DF-015 A/B/C Current-Main Reproduction — 2026-09-26

## Purpose

Reproduce the frozen DF-015 A/B/C regression against current main.

This record does not modify DF-015 fixtures, taxonomy, implementation,
or expected semantics.

## Baseline

Previous frozen evidence:

- DF015_VALIDATION_RECORD_2026-09-01.md
- DF015_ABC_REGRESSION = PASS_3_OF_3

Expected outputs:

- DF-015-A over-linking detected
- DF-015-B under-linking detected
- DF-015-C multi-parent restraint preserved
- 3/3 DF-015 tests PASSED

## Current-main reproduction

Status: PENDING CI

Branch:
df015-abc-regression-outputs-v0_1

Regression command:

python test_df015_causal_compression.py

## Non-claims

- no fixture changes
- no taxonomy changes
- no implementation changes
- no new DF-015 semantics
