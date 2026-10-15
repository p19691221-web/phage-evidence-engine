# DF-011 validation record

Support rules baseline: 471f791 (PR #108).
Control specification baseline: 8212797 (PR #109).
Baseline RED checkpoint: 66bd0e2 (Draft PR #110).
Executed implementation and test revision: 7773080.
Runner: pytest 9.1.1.
Command: python -m pytest -q -s test_df011_provenance.py

## Results

Baseline: 3 failed, 1 passed; see baseline-red.log and RED_RECORD.md.
Production entry point: 11 passed; see green.log.

The three unsupported fixtures stop before run_gate:
run_gate calls=0, evaluator calls=0, state=UNRESOLVED.
The supported control reaches run_gate and evaluator once each,
returns CLEAN and records DF011_EVALUATOR_REACHED_V1.
Seven additional negative tests break source resolution, grantee,
permission, approval scope, authority version/content or actor identity.

## Scope

The baseline adapter and production entry point differ explicitly.
GREEN invokes run_expectation_gate, not test-local provenance logic.
Existing gate signatures and result structure are unchanged.
The evaluator sentinel is not an E/O delta computation.

Support is limited to these synthetic cases and supplied policy records.
Principal identity, source authenticity and independence are assumptions.
No real-world legitimacy, revocation, concurrency, operational authority,
production readiness or pilot validation is established.

Evidence/Gap structural assessment is a separate claim.
No CLAIMS_STATUS promotion is made in this change.

CI workflow added: df011-provenance.yml.
Remote DF-011 CI: SUCCESS.
Evidence: https://github.com/p19691221-web/phage-evidence-engine/actions/runs/38705112576/job/116322493245
This records the observed run, not any subsequent revision.
