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

Status: PASS
PR: #54
Workflow: DF-015 causal restraint
Workflow run: #63
Tested commit: a2e9981e1ab5a3ebdf508729f26f27e2caecc502

PASS: DF-015-A over-linking detected
PASS: DF-015-B under-linking detected
PASS: DF-015-C multi-parent restraint preserved

3/3 DF-015 tests PASSED
DF015_ABC_REGRESSION = PASS_3_OF_3
CURRENT_MAIN_REPRODUCTION = PASS

## Non-claims

- no fixture changes
- no taxonomy changes
- no implementation changes
- no new DF-015 semantics
