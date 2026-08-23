# DF-017 Independent Validation Record

## Validation identity

- Validation ID: DF-017
- Fixture ID: DF017-AIID-74
- Incident ID: AIID 74
- Repository: phage-evidence-engine
- Branch: main
- Workflow: `.github/workflows/df017-independent-validation.yml`
- Trigger: `workflow_dispatch`
- Run: DF-017 Independent Validation #3
- Validation date: 2026-08-23
- Commit SHA: - Commit SHA: 115bcfd4b0abdf81f76435e054ff4baf6c177e52

## Validation inputs

- `DF017_AIID_74_FIXTURE.json`
- `DF017_AIID_74_SOURCES.json`
- `DF017_FIXTURE_MANIFEST.json`
- `df017_independent_validator.py`

## Execution result

- Workflow execution: PASS
- Validator execution: completed
- Independent validation result: UNRESOLVED

## Interpretation

The DF-017 frozen validation package executed successfully on the
`main` branch through the manually dispatched independent-validation
workflow.

The successful GitHub Actions run establishes that the validation
package was executable and that the validator completed.

The substantive validation result was `UNRESOLVED`.

A successful workflow execution does not convert an unresolved
validation result into PASS and does not establish the truth of any
substantive PHAGE claim.

AIID and external reports are treated as external evidence inputs,
not as ground truth.

## Evidence

The GitHub Actions run produced a DF-017 validation evidence artifact.

Exact commit SHA and any cryptographic identifiers must be recorded
from the execution metadata rather than inferred.

## Final status

**UNRESOLVED**
