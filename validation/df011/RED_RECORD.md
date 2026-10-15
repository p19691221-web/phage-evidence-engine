# DF-011 baseline RED

Baseline: 8212797 (PR #109 merge).
Runner: pytest 9.1.1.
Command: python -m pytest -q -s test_df011_provenance.py
Observed: 3 failed, 1 passed.
Full output: baseline-red.log.

Three unsupported cases fail boundary assertions; control passes.
Each case first independently verifies the CLEAN lineage prerequisite.

execute_baseline calls existing run_gate without provenance input.
This demonstrates missing discrimination at the existing entry point,
not execution of a new provenance gate.
Two counting spies observe gate and evaluator calls.
The sentinel does not establish E/O delta computation.

The initial missing-pytest error is not RED evidence.
No engine implementation or CLAIMS_STATUS promotion is included.
GREEN must exercise the production provenance entry point, with no
test-local provenance decision logic.

## Actual case outputs
self_proposed {"evaluator_calls": 1, "outputs": ["DF011_EVALUATOR_REACHED_V1"], "run_gate_calls": 1, "state": "CLEAN"}
Fthird_party_unsupported {"evaluator_calls": 1, "outputs": ["DF011_EVALUATOR_REACHED_V1"], "run_gate_calls": 1, "state": "CLEAN"}
Fself_approved {"evaluator_calls": 1, "outputs": ["DF011_EVALUATOR_REACHED_V1"], "run_gate_calls": 1, "state": "CLEAN"}
Fsupported_control {"evaluator_calls": 1, "outputs": ["DF011_EVALUATOR_REACHED_V1"], "run_gate_calls": 1, "state": "CLEAN"}
