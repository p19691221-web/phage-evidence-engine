# Decision input relationship validation

Hypothesis baseline: 2e2dbaa.
Semantic specification baseline: 081a09e.
Test contract baseline: 80e1a27.
Missing-entry checkpoint: a67b3d6 (Draft PR #117).
Executed implementation revision: 1686c39.
Runner: pytest 9.1.1.

Command:
python -m pytest -q -rs test_decision_input_traceability.py test_df011_provenance.py

Results: 19 passed, no skipped cases.
Decision input: entry check plus seven differential cases (8 passed).
DF-011 regression: 11 passed.
Raw output: green.log.

Baseline was 1 failed and 7 skipped: entry absent, no differential
execution. See BASELINE.md and baseline-pytest.log.

The new checker matches the frozen relationship findings, preserves
inputs and passes the assertion forbidding assessment gate invocation.
It reports record consistency, not actual presentation or human judgment.

This provides synthetic support for the binding/registry pattern.
No existing PHAGE executable component reuse was established.
DF-011 evidence is not transferred.

Scope: seven fixed synthetic cases in an in-memory model.
Identity and registry authenticity are supplied assumptions.
Source truth, verification independence, attention, comprehension,
decision quality and institutional authority are not established.
Malformed-input coverage is not established by these seven cases.

Dedicated remote CI is added but not yet confirmed.
Decision input traceability remains OPEN pending separate claim review.
