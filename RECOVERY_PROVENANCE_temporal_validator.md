# PHAGE Temporal Validator Recovery Provenance

status: RECOVERED_IMPLEMENTATION_FRESHLY_TESTED
date: 2026-08-20

## Recovery boundary

The original `temporal_validator.py` was not located in the recovered artifact set.
`temporal_validator_RECOVERED.py` was reconstructed only from surviving artifacts:

- `lineage.py`
- `phage_validate_temporal_fixture.py`
- `test_df014_windrelay.py`

No historical PASS result was inherited.

## Fresh execution

Test target: `test_df014_windrelay.py`

Result:
- DF-014 temporal defect fixture: PASS
- DF-014 contemporaneous negative control: PASS
- Total: 2/2 PASS
- Process exit code: 0
- Captured stderr bytes: 0

Observed diagnostics:
- `STATE_TRANSITION_UNRESOLVED`
- `INTENT_INFERENCE_UNRESOLVED`

Negative control:
- `CLEAN`
- `evaluation_started = True`
- no diagnostics

## Evidence classification

This supports the recovered implementation only.
It does not prove that the recovered file is byte-identical or behavior-identical
to the unlocated original `temporal_validator.py`.
