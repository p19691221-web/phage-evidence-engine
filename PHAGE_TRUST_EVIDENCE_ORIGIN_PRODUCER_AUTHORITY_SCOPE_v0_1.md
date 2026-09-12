# PHAGE Trust Evidence Origin — Producer Authority Scope v0.1

## Artifact status

Specification maturity: SCOPE CLARIFICATION  
Executable validation: NOT APPLICABLE TO THIS DOCUMENT  
Producer-authority enforcement maturity: NOT STARTED  
Production assurance: NOT ESTABLISHED  
Independent external review: NOT PERFORMED

This document clarifies an assumption boundary in the PHAGE Trust
Evidence Origin v0.1 research prototype.

It does not introduce a new executable fixture or producer-authority
enforcement mechanism.

---

## Scope question

The existing prototype contains:

`_produce_trusted_evidence(...)`

G4 and G5 validate behavior of evidence produced through that path.

They do NOT establish:

- who is permitted to call that producer
- how the producer caller is authenticated
- how producer authority is granted
- how producer authority is revoked
- how producer identity is established across process boundaries

Therefore:

`TRUSTED_PRODUCER_OUTPUT ≠ TRUSTED_PRODUCER_IDENTITY`

and:

`PRIVATE_FUNCTION_NAMING ≠ PRODUCER_AUTHORITY_ENFORCEMENT`

---

## ASSUMED_GENESIS_PRODUCER_AUTHORITY

PHAGE Trust Evidence Origin v0.1 assumes that access to the trusted
evidence producer path is already governed by an external trust boundary.

The current prototype does not authenticate or authorize callers of:

`_produce_trusted_evidence(...)`

The authority of the entity permitted to invoke the trusted producer
is therefore an assumed genesis condition for this prototype.

This assumption is explicitly named:

`ASSUMED_GENESIS_PRODUCER_AUTHORITY`

---

## Boundary

The current executable Trust Evidence Origin regressions validate:

- G1 — forged-origin fail-closed behavior
- G2 — verifier internal failure fail-closed behavior
- G3 — public-entry-to-verifier-seam delegation
- G4 — trusted-producer positive-origin characterization
- G5 — post-production content-tamper detection

These regressions validate evidence-origin behavior after the producer
path has been invoked.

They do not validate the authority of the caller that invoked the
producer path.

Therefore:

`PRODUCER_OUTPUT_VALIDATION ≠ PRODUCER_CALLER_AUTHORIZATION`

---

## Why no G6 fixture is introduced

A new producer-authority regression would require a meaningful
enforcement boundary.

The current prototype is in-process.

Within that boundary, adding another caller flag, token, private
function convention, or similar mechanism would not establish
production-grade producer authority against an actor already capable
of executing arbitrary code in the same process.

Therefore producer authority is not represented as a new executable
fixture in v0.1.

This is a scope decision, not evidence that the problem is solved.

---

## OUT_OF_SCOPE_v0.1

The following remain outside the Trust Evidence Origin v0.1 prototype:

- producer caller authentication
- producer caller authorization
- cross-process producer identity
- producer service identity
- producer credential issuance
- producer credential revocation
- producer key custody
- production identity infrastructure
- compromised-process resistance
- arbitrary-code-execution resistance
- institutional root-of-trust determination
- ultimate legitimacy of the producer authority

---

## Preserved distinctions

`trusted producer output ≠ trusted producer identity`

`private function ≠ protected authority boundary`

`origin verification ≠ producer authorization`

`content binding ≠ producer authentication`

`producer authentication ≠ producer authorization`

`producer authorization ≠ execution authorization`

`ASSUMED_GENESIS_PRODUCER_AUTHORITY ≠ VERIFIED_PRODUCER_AUTHORITY`

---

## Relationship to G4 and G5

G4 establishes only that, within the current prototype, evidence
created through the trusted producer path can be accepted by the
evidence-origin verifier.

G5 establishes only that the trusted-origin marker is bound to the
tested evidence content and that post-production mutation of that
content fails closed.

Neither result establishes who was authorized to invoke the producer.

Therefore:

`G4 GREEN + G5 GREEN ≠ PRODUCER AUTHORITY VALIDATED`

---

## Explicit non-claims

This scope clarification does NOT establish:

- authenticated producer identity
- authorized producer identity
- production producer access control
- cryptographic producer authentication
- cryptographic producer authorization
- production credential management
- cross-process trust establishment
- service-to-service authentication
- resistance to process compromise
- resistance to arbitrary code execution
- legal or institutional producer authority
- production deployment readiness

---

## Assurance statement

Producer authority in Trust Evidence Origin v0.1 is:

`ASSUMED`

not:

`EXECUTABLY VALIDATED`

and not:

`PRODUCTION ENFORCED`

The assumption is now explicit so that G4/G5 evidence-origin validation
cannot be interpreted as evidence that producer identity or producer
authority has also been established.
