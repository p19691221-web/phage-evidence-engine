# DF-018 Governance Regression Validation Record

## Validation identity

- Validation ID: DF-018
- Fixture ID: DF018-UBER-BEITOU
- Repository: phage-evidence-engine
- Branch: main
- Workflow: `.github/workflows/df018-governance-regression.yml`
- Trigger: `workflow_dispatch`
- Run: DF-018 Governance Regression #3
- Validation date: 2026-08-24

## Validation inputs

- `DF018_UBER_BEITOU_FIXTURE.json`
- `df018_evaluator.py`
- `df018_validator_v1.py`
- `lineage.py`
- `gate.py`

## Execution result

- GitHub Actions workflow execution: PASS
- DF-018 regression validator execution: PASS
- Regression shape: 4 triggered / 4 silent

The validator executed on the `main` branch through the manually
dispatched DF-018 governance-regression workflow.

## Regression results

### CURRENT_LAW_LEAKAGE

- Leakage case: TRIGGERED
- Control case: SILENT

The validator detected use of unverified or temporally unestablished
statutory text as governing law while leaving the corresponding
control case silent.

### SECTION_IDENTITY_COLLISION

- Leakage case: TRIGGERED
- Control case: SILENT

The validator detected collapse of statutory section identity across
versions while version revalidation remained required. The control
case preserved version sensitivity and remained silent.

### ENTITY_IDENTITY_COLLISION

- Leakage case: TRIGGERED
- Control case: SILENT

The validator detected collapse of distinct legal entities into one
actor. The control case preserved separate entity identity and
remained silent.

### AUTHORITY_CHAIN_PREMATURE_CLOSURE

- Leakage case: TRIGGERED
- Control case: SILENT

The validator detected an attempted closure of CLAIM_1 as SATISFIED
while the regulated category or primary disposition remained
unestablished.

The control case preserved CLAIM_1 as PENDING / UNRESOLVED while S5
remained open.

## Validator output

The fresh execution produced the terminal result:

`DF-018 regression PASS: 4 triggered / 4 silent.`

## Interpretation

This validation establishes that the DF-018 governance regression
package is executable on `main` and that the four locked failure
conditions behave as specified against their corresponding controls.

A successful workflow execution does not establish the substantive
legality of the DF-018 service.

A successful regression result does not convert missing evidence into
a substantive conclusion.

In particular:

- CLAIM_1_CLASSIFICATION_AUTHORITY remains PENDING / UNRESOLVED.
- CLAIM_2_FINAL_LEGALITY remains PENDING / UNRESOLVED.
- S5_REGULATED_CATEGORY_IN_ACTUAL_DISPOSITION remains OPEN.
- S5_PRIMARY_DISPOSITION remains OPEN.
- No final administrative or judicial resolution is established by
  this validation run.

## Governance boundary

The validation result is evidence about validator behavior and
reproducibility.

It must not be phrased as evidence that:

- the challenged service was finally determined unlawful;
- the competent authority for the specific DF-018 disposition has
  been conclusively established;
- the actual regulatory classification used in the disposition has
  been established;
- the missing primary disposition has been reconstructed;
- CLAIM_1 or CLAIM_2 is SATISFIED.

## Final validation status

**REGRESSION PASS — 4 TRIGGERED / 4 SILENT**

Substantive DF-018 claims remain **UNRESOLVED**.
