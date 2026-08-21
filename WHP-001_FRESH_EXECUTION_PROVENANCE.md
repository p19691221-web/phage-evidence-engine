# WHP-001 Fresh Execution Provenance

status: FRESH_REEXECUTION
fixture_id: WHP-001-AUTH-SCOPED-001

## Inputs

- fixture: `WHP-001-AUTH-SCOPED-001.yaml`
- fixture_sha256: `53fc2019ed716d58dddb9137fdad6a52d10b808bd009a22285e86e782f0e9b51`
- validator: `phage_validate_fixture.py`
- validator_sha256: `9af713fd30b05097d1f97542001f577656452070951743dbfe0147f29bec8ff8`
- validator_version: `v0.1-research-preview`

## Fresh execution

- exit_code: `0`
- stderr_bytes: `0`
- differential_result: `PASS`
- historical PASS results inherited: `NO`

## Contract note

The surviving validator's PASS path matches the frozen `validate-fixture` v0.1 contract used by this fixture. A known FAIL-path stdout ordering drift exists: the validator prints `Differential Result: FAIL` before the frozen failure-classification block. This run exercised the PASS path; no validator code was modified before execution.

## Evidence boundary

This record supports only fresh reproducibility of WHP-001 under the surviving v0.1 validator artifact. It does not establish full validator/contract conformance on unexecuted failure paths and does not establish legal liability or universal authority rules.
