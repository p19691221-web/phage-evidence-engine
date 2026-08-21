# WHP-002 Fresh Clean Execution Provenance

status: FRESHLY_REPRODUCED_PASS
fixture_id: WHP-002-SEC-CUSTODY-001

## Inputs

- fixture: `WHP-002-SEC-CUSTODY-001.yaml`
- fixture_sha256: `0ebcdb9d375fe918b96c5bd5d1dbe50d08b6e8e42577ef59cfac52c95e97a343`
- validator: `phage_validate_fixture.py`
- validator_sha256: `9af713fd30b05097d1f97542001f577656452070951743dbfe0147f29bec8ff8`
- validator_version: `v0.1-research-preview`

## Clean fresh execution

- differential_result: `PASS`
- exit_code: `0`
- stderr_bytes: `0`
- stdout_file: `WHP-002_fresh_execution_clean.stdout.log`
- stdout_sha256: `57192b5639e9f5f07d45cc84ca839f93b91892a551cde13522abe60ac9d79c21`
- stderr_file: `WHP-002_fresh_execution_clean.stderr.log`
- stderr_sha256: `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- historical PASS inherited: `NO`

## Contract note

The surviving validator's PASS path matches the frozen `validate-fixture` v0.1
contract used by this fixture. A known FAIL-path stdout ordering drift remains.
This clean run exercised the PASS path; no validator code or fixture content was
modified to obtain the result.

## Evidence boundary

This record supports fresh structural differential reproducibility of WHP-002
under the surviving v0.1 validator artifact. It does not establish full
validator/contract conformance on unexecuted failure paths, universal authority
rules, or substantive SEC/legal conclusions.
