# PHAGE Trust Boundary L/M reconstructed specification v0.1

Status: RECONSTRUCTED — REVIEW PROPOSAL, NOT FROZEN.
Prepared: 2026-10-03 (Asia/Taipei).

## Source and missing provenance

This document is reconstructed from a user-supplied summary of design
discussions dated 2026-09-07 through 2026-09-08. The original
PHAGE_TRUST_BOUNDARY_INVARIANTS_v0_1 text has not been recovered.
The summary reports specification closure on 2026-09-08; this document
does not reproduce that original frozen text or inherit its approval.
Approval must occur through a new documentation-only PR. Explicit approval
and merge of that PR freezes only the L/M requirements below, effective at
that merge. It does not freeze a reconstructed full G-N specification.

The summary reports eight invariants but retains only five names:
PROPOSAL != EVIDENCE, EVIDENCE_ORIGIN_INVARIANT,
POLICY_MUTATION_INVARIANT, DECISION_FRESHNESS_INVARIANT, DECISION != EFFECT.
The other three names and their wording are UNKNOWN. The original wording
of all eight is unavailable; no missing invariant is supplied here.

## Historical context from the summary

The recorded fixture topics are G (forged Evidence origin), H/H' (policy
self-authorization versus independently authorized mutation), I (decision
freshness), J (AI-supplied evidence), K (decision/effect substitution),
L (forged Decision origin), M (forged or tampered audit receipt), and
N (cyclic authority lineage, fail closed without looping or truncation).
This list is historical context, not executable acceptance criteria for
fixtures outside L/M.

Specification closure is distinct from enforcement closure. The summary
requires executable passing G-N fixtures, implemented Evidence/Decision/
Receipt origin verification, and a real H/H' authority-lineage resolver
before runtime closure. This PR establishes none of those completion claims.

## Proposed common L/M requirements

Origin checking uses opaque objects, module-private origin tokens, and an
explicit verifier, following the recorded G pattern. A caller-created
object or self-declared origin claim cannot establish verified origin.
This in-process mechanism does not establish protection against arbitrary
code execution in the same process or production cryptographic identity.

Keep unverified origin separate from verifier failure:
- G1-style failure: unverified origin, BLOCKED.
- G2-style failure: verifier internal error, separately observable, BLOCKED.
Catch verifier exceptions at the enforcement boundary. Never reclassify
them as unverified origin or verified origin.
G2 regression must use a replaceable fault-injection hook rather than
depend on an actual infrastructure failure.

## L — forged Decision origin

A caller-constructed decision or one whose origin cannot be verified must
not be consumed as a legitimate decision.
Origin rejection returns DECISION_ORIGIN_UNVERIFIED and BLOCKED.
Verifier failure returns DECISION_VERIFICATION_ERROR and BLOCKED.
Tests must distinguish these paths and show that neither permits the
protected operation. A valid-origin positive control is required to
distinguish verification from unconditional rejection.

## M — forged or tampered audit receipt

Verify receipt origin and integrity when the receipt is consumed.
An offline verification performed after use cannot satisfy this requirement.
Forged or tampered receipts return AUDIT_ORIGIN_UNVERIFIED and BLOCKED.
Verifier failure returns AUDIT_VERIFICATION_ERROR and BLOCKED.
Tests must demonstrate verification before protected use, rejection of
post-issuance tampering, a valid-receipt positive control, and an observable
fault-injected verifier-error path.

## Dependency and implementation boundaries

Producer-verifier contract v0.2 was frozen through PR #86 on main 9c069e7,
following implementation PR #85. L/M must consume that contract without
modifying its verifier or contract files to accommodate fixture behavior.
Schedule, Emergency Override, and evidence reuse G6 are outside this PR.

This proposal freezes semantic requirements only. Concrete entry signatures,
object representation, receipt content-binding fields, and the exact
protected-use boundary must be made explicit in the subsequent RED test PR;
they are not reconstructed original API claims.

Sequence: approve and merge this document; review L/M RED tests; implement;
then validate integration. Green tests alone do not establish full runtime
closure, institutional authority, production readiness, or pilot maturity.
