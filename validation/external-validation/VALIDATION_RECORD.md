# Synthetic external-shaped validation record

Contract: PR #125.
Test specification: PR #126.
Exception baseline: 6fd8925.
Frozen tests and fixtures: ba8dd65; draft PR #127.

Before implementation:
- root absence and injected checker fault shared ValueError;
- wrapper availability: 1 failed, 1 passed, 14 skipped.
The fourteen behavioral cases did not execute at that stage.
This is not a fourteen-case differential RED record.

After implementation:
- first-execution.log: 16 passed, no skips;
- green-regression.log: 45 passed, no skips.
The latter includes 16 external-wrapper checks and 29 existing
decision-input/DF-011 regression checks.

Executed cases distinguish scoped absence, unmappability,
unknown coverage and fail-loud execution errors.
Cases 5/6 use identical snapshots with different frozen evidence.
Injected checker and persistence exceptions remain distinguishable.
Optional presentation omission preserves the checker result
and a separate source-coverage finding.

Support is limited to the frozen synthetic cases and identity
mapping. This is not institutional or real-workflow validation.
Manifest assertions and source authenticity are supplied assumptions.
General malformed-input and arbitrary-adapter coverage are not
established by these tests. CLAIMS_STATUS is unchanged.

CI now includes test_external_validation.py.
Remote CI remains to be confirmed.
