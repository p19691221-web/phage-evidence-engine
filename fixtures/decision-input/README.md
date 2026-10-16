# Historical decision-input fixtures — SUPERSEDED

These seven v1 fixtures retain the historical S/V result schema.
They are superseded by fixtures/decision-input-v2 following the
implementation in PR #122 and claim alignment in PR #123.

Historical validation:
- Executed implementation revision: 1686c39.
- Validation record: validation/decision-input/VALIDATION_RECORD.md.
- Subsequent claim update: PR #119.

These fixtures are preserved as evidence, not current-main regression
expectations. Current tests use decision-input-v2.
Running the current checker against v1 expected results produces schema
mismatches; this alone is not evidence of a behavioral regression.

To reproduce historical results, use the recorded implementation and
test revisions and their documented environment.
Do not rewrite these expected results to match the current checker.
