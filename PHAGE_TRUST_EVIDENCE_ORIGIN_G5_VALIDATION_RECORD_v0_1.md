# PHAGE Trust Evidence Origin G5 Validation Record v0.1

## Artifact status

Validation maturity: EXECUTABLE REGRESSION VALIDATED  
Validation scope: G5 ONLY  
Implementation scope: MINIMAL IN-PROCESS CONTENT BINDING  
Production assurance: NOT ESTABLISHED  
Independent external review: NOT PERFORMED

This record documents the G5 post-production evidence tamper regression
and the minimal implementation introduced to satisfy that frozen boundary.

---

## Validation target

Module:

`phage_trust_evidence_origin_v0_1.py`

Regression:

`test_phage_trust_evidence_origin_v0_1.py`

Validated fixture:

- G5 — post-production evidence tamper

---

## Semantic RED evidence

Before content binding was implemented, G1-G4 passed while G5 failed:

`PASS: fixture_G1_forged_evidence_origin`

`PASS: fixture_G2_verifier_internal_failure`

`PASS: fixture_G3_public_entry_uses_verifier_seam`

`PASS: fixture_G4_trusted_producer_positive_origin`

`FAIL: fixture_G5_post_production_evidence_tamper`

Observed failure:

`G5 contract RED: post-production content mutation retained verified origin`

Final RED result:

`PHAGE Trust Evidence Origin regression RED: 1 / 5 failing`

This was semantic RED evidence.

The trusted producer created a candidate, the candidate was copied,
its evidence content was modified while preserving the trusted marker,
and the existing verifier still treated the modified candidate as
verified-origin evidence.

---

## Frozen invariant

`ORIGIN_ATTESTATION_MUST_BIND_TO_CONTENT`

Therefore:

`TRUST_MARKER_PRESENT ≠ CONTENT_ORIGIN_VERIFIED`

A trusted-origin marker alone is insufficient when the evidence content
no longer matches the content originally associated with that marker.

---

## Minimal implementation

The implementation was changed only within the in-process research
prototype boundary.

Each produced evidence object now receives its own opaque token.

The producer records:

`token → content snapshot`

The snapshot currently covers:

- `value`
- `source`
- `schedule_ref`
- `policy_version`
- `observed_at`

The default verifier now requires:

1. the candidate to be a dictionary
2. the token to exist in the in-process trusted-origin binding registry
3. the candidate's current content snapshot to equal the snapshot bound
   to that token at production time

If the content no longer matches, origin verification fails closed.

---

## GREEN evidence

After the minimal content-binding implementation and harness repair,
the executable regression produced:

`PASS: fixture_G1_forged_evidence_origin`

`PASS: fixture_G2_verifier_internal_failure`

`PASS: fixture_G3_public_entry_uses_verifier_seam`

`PASS: fixture_G4_trusted_producer_positive_origin`

`PASS: fixture_G5_post_production_evidence_tamper`

Final observed result:

`PHAGE Trust Evidence Origin regression PASS: 5 / 5`

---

## Validated observations

Within the current in-process prototype:

- an untampered trusted-producer candidate remains
  `EVIDENCE_ORIGIN_VERIFIED`
- post-production mutation of bound evidence content becomes
  `EVIDENCE_ORIGIN_UNVERIFIED`
- the tampered path is `BLOCKED`

G4 remains GREEN while G5 is also GREEN.

---

## Preserved distinctions

`trusted producer output ≠ immutable evidence`

`trusted marker present ≠ content origin verified`

`content binding ≠ cryptographic signature`

`content binding ≠ replay resistance`

`origin verification ≠ Authority`

`EVIDENCE_ORIGIN_VERIFIED ≠ execution authorization`

---

## Explicit non-claims

This validation does NOT establish:

- cryptographic provenance
- digital signatures
- cryptographic attestations
- replay resistance
- resistance to token extraction
- resistance to process compromise
- persistent trust across process restart
- trusted external identity
- production key management
- tamper-resistant storage
- distributed trust establishment
- legal or institutional authority
- execution authorization
- production deployment readiness
- complete PHAGE trust-boundary integration

The binding registry remains an in-process research-prototype mechanism.

---

## Assurance statement

Executable regression support now exists for:

- G1 forged-origin fail-closed behavior
- G2 verifier internal failure fail-closed behavior
- G3 public-entry-to-verifier-se
- G4 trusted-producer positive-origin characterization
- G5 post-production content-tamper detection

G5 establishes only the tested in-process content-binding behavior.

This record must not be generalized into cryptographic provenance,
replay resistance, production identity assurance, or production readiness.
