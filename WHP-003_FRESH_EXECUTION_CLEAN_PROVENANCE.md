# WHP-003 Fresh Clean Execution Provenance

status: FRESHLY_REPRODUCED_PASS
fixture_id: WHP-003-HIPAA-SCOPE-001

- fixture_sha256: `eeb73e7a9e5012657d722d38e1b7a0a4837abaa4fd7d4d9c5b09d07f7a81d3c2`
- validator_sha256: `9af713fd30b05097d1f97542001f577656452070951743dbfe0147f29bec8ff8`
- differential_result: `PASS`
- exit_code: `0`
- stderr_bytes: `0`
- historical PASS inherited: `NO`

Known limitation: the surviving validator has a frozen-contract FAIL-path
stdout ordering drift. This execution exercised only the conforming PASS path.

This record supports structural differential reproducibility only; it does not
establish substantive HIPAA/legal conclusions.
