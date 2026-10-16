# Field mapping differential RED

The initial schema implementation passed 21 checks.
A subsequent test renames output.producer to source field author
and declares that source_template in the schema.

Command:
python -m pytest -q test_external_schema.py -k field_source_template

Observed: 1 failed, 21 deselected.
Failure: input_validation / ADAPTED_INPUT_INVALID.
The implementation copies the mapped root but does not apply
individual field mappings when assembling checker arguments.

This checkpoint preserves the failing implementation and test.
It is a concrete differential RED for field mapping only.
Earlier missing-entry runs remain availability baselines.
