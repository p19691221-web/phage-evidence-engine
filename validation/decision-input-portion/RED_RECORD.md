# Portion support RED record

Production/spec baseline: 7050bda.
Production code unchanged during this checkpoint.

Direct observation: old-behavior.json.
Control S/V: matched/matched.
Consistently renamed control S/V: not_asserted/not_asserted.
A/P/L/C remain matched. This independently reproduces the literal-P1 defect.

Command: python -m pytest -q test_decision_input_portions.py
Observed: 9 failed.
Eight v2 fixture comparisons and one concrete renamed-support/equivalence
test fail against production lacking output_support.
These schema failures are distinct from the observed P1 naming defect.

Historical fixtures and logs are retained unchanged.
No implementation fix or claim expansion is included.
