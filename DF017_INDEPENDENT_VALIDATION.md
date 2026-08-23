# DF-017 Independent Validation Protocol

## Purpose

DF-017 defines an independent and reproducible validation procedure for the PHAGE Evidence Engine.

The purpose is not to prove that PHAGE is correct.

The purpose is to make PHAGE's claims independently testable and falsifiable.

A validation attempt MAY confirm, contradict, or expose limitations in the current implementation.

---

## Validation Principle

An independent validator SHOULD be able to reproduce the evaluation without assistance from the original implementation author.

The validator MUST be permitted to report:

- PASS
- FAIL
- UNRESOLVED
- implementation error
- specification ambiguity
- non-reproducible result

A negative result MUST NOT be rewritten or discarded merely because it contradicts the expected result.

---

## Frozen Validation Target

Before validation begins, record:

- repository
- branch or tag
- commit SHA
- validation date
- Python version
- operating environment
- fixture identifiers
- fixture hashes, when available

The tested implementation MUST NOT be modified after the validation result is known and then represented as the original validation target.

Any correction requires a new validation run.

---

## Materials Provided to Validator

The validator SHOULD receive enough information to reproduce the test independently, including:

1. source repository
2. frozen commit identifier
3. relevant public fixtures
4. execution instructions
5. expected output schema
6. PASS / FAIL criteria
7. known limitations

Where practical, the validator SHOULD NOT receive an explanation designed to persuade them toward a particular result.

---

## Independent Reproduction Procedure

The validator should:

1. obtain the frozen repository revision;
2. verify the recorded revision identifier;
3. inspect the supplied fixture provenance;
4. execute the documented tests;
5. record stdout, stderr, and exit status;
6. compare observed results against the predefined criteria;
7. record discrepancies without modifying them;
8. produce an independent validation report.

---

## PASS Criteria

A validation run is PASS only when:

- the specified revision can be obtained;
- required inputs are available;
- the procedure executes reproducibly;
- observed outputs satisfy the predefined contract;
- provenance and lineage checks behave as specified;
- no undocumented intervention is required to obtain the result.

---

## FAIL Criteria

A validation run is FAIL when, for example:

- the documented procedure cannot reproduce the claimed result;
- evidence lineage accepted by the system violates the frozen contract;
- tampered or inconsistent evidence is accepted when it should be rejected;
- required provenance cannot be reconstructed;
- observed output contradicts a predefined expected invariant.

FAIL is a valid research result.

---

## UNRESOLVED Criteria

Use UNRESOLVED when available evidence is insufficient to determine PASS or FAIL.

UNRESOLVED MUST NOT automatically be converted to PASS.

Examples include:

- missing source material;
- ambiguous provenance;
- unavailable external evidence;
- insufficient information to reconstruct lineage.

---

## Falsification

DF-017 explicitly permits falsification.

A validator falsifies a tested claim when they provide a reproducible case in which:

1. the frozen implementation is executed according to the documented procedure;
2. the supplied inputs satisfy the stated preconditions;
3. the observed result contradicts a stated invariant or expected contract;
4. the discrepancy can be independently reproduced.

Such a result MUST be preserved as evidence.

---

## External Evidence

Public external sources MAY be used as validation fixtures.

For each external fixture, record where possible:

- source
- stable identifier
- retrieval date
- original URL or reference
- locally preserved representation
- cryptographic hash
- transformation history

External sources are evidence inputs, not endorsements of PHAGE.

---

## Validator Independence

The validation report SHOULD disclose whether the validator:

- contributed to the implementation;
- designed the test;
- knew the expected result beforehand;
- modified the fixture;
- modified the implementation;
- has another material conflict affecting independence.

Independence is a property to document, not assume.

---

## Required Validation Record

Each validation attempt SHOULD preserve:

- validator identifier or pseudonymous identifier
- validation timestamp
- commit SHA
- environment information
- fixture identifiers
- commands executed
- observed outputs
- PASS / FAIL / UNRESOLVED result
- deviations from protocol
- discovered defects or ambiguities

---

## Research Boundary

A successful DF-017 validation demonstrates reproducibility only for the tested revision, fixtures, environment, and stated contract.

It does not establish that PHAGE is universally correct, safe, secure, legally compliant, or suitable for deployment.

Independent validation strengthens evidence about a specific claim; it does not convert that claim into universal proof.
