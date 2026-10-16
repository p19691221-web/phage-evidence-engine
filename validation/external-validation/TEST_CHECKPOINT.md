# Pre-implementation test checkpoint

Base implementation: 2340d34.
Exception baseline checkpoint: 6fd8925.

Nine synthetic fixtures and five boundary cases are frozen.
The inventory test passes.
The wrapper entry-point assertion fails.
Nine core cases and five boundary cases are skipped because
the wrapper is absent: their behavioral assertions did not run.

Initial availability.log: 1 failed, 1 passed, 9 skipped.
availability-with-boundaries.log: 1 failed, 1 passed, 14 skipped.

These are availability observations, not fourteen differential
RED failures. The separate baseline demonstrates that missing
root records and an injected checker fault share ValueError.

Expected findings are test-owned and are not wrapper inputs.
Cases 5/6 preserve identical source snapshots.
No production implementation or claim change is included.
