# Schema manifest availability baseline

Base revision: e0894ce.
Contract: EXTERNAL_SCHEMA_MANIFEST_CONTRACT.md, PR #129.

Command:
python -m pytest -q -rs test_external_schema.py

Observed: 1 failed, 1 passed, 17 skipped.
The schema entry point is absent.
The frozen fixture inventory check passes.
Seventeen behavioral cases did not execute.
This is not a seventeen-case differential RED record.

The synthetic batch contains three inventoried decisions:
two evaluable controls and one missing adoption root.
One schema contains 38 rules, independent of decision count.
Test-owned expectations contain 84 expansion rows,
15 selection rows and one grouped root finding.

Expected outputs are not production inputs.
No schema implementation or institutional data is included.
Further contract coverage must be checked before implementation.
