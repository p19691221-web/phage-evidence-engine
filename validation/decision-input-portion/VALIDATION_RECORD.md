# Portion support amendment validation

Contract baseline: 7050bda (PR #121).
RED checkpoint: 889da08.
Executed implementation revision: bc1dc4c.
Runner: pytest 9.1.1.

Command:
python -m pytest -q test_decision_input_traceability.py test_decision_input_portions.py test_df011_provenance.py

Observed: 29 passed.
- Current decision-input contract: 9 tests.
- Portion-specific contract and renaming: 9 tests.
- DF-011 regression: 11 tests.
The two decision-input suites overlap across 8 synthetic fixtures.

RED evidence is preserved in RED_RECORD.md, red.log and old-behavior.json.
Old control S/V were matched; consistent renaming changed them to
not_asserted. Amended-schema failures were recorded separately.

Production now reports output_support for every output portion.
A/P/L/C and adopted_support semantics remain unchanged.
Concrete Q7/R9 findings and result renaming equivalence pass.

Support is limited to the executed cases and tested renaming.
No arbitrary-renaming or external-workflow validation is established.
Historical fixtures and execution records retain their original scope.
No existing PHAGE executable component reuse is established.
No actual presentation, source truth or independent human judgment follows.

Remote decision-input CI: SUCCESS.
Evidence: https://github.com/p19691221-web/phage-evidence-engine/actions/runs/38748411045/job/116468039458
This records the observed run, not subsequent revisions.
CLAIMS_STATUS is unchanged in this implementation change.
