# PHAGE Trust Boundary — Producer Authority Behavior v0.1

## Status

Behavioral contract definition only.

Producer-authority surface: PRESENT

Producer-authority enforcement: NOT YET IMPLEMENTED

This document freezes the first executable behavior expected from the
producer-authority gate introduced before trusted evidence production.

It does not modify G1–G5 semantics.

---

## Existing boundary

The intended control flow remains:

```text
caller context
    |
    v
producer-authority gate
    |
    v
_produce_trusted_evidence(...)
    |
    v
evaluate_evidence_origin(...)
```

The existing `_produce_trusted_evidence(...)` function remains the
trusted-origin provenance primitive.

Producer-authority enforcement occurs before that primitive.

---

## Core behavioral rule

Trusted evidence production requires producer authority to be
established before the provenance-producing primitive is entered.

Therefore:

```text
producer authority unresolved
→ fail closed
→ trusted production does not proceed
```

Fail-closed behavior is mandatory.

---

## Unresolved producer authority

The first executable behavioral case is:

```text
PRODUCER_AUTHORITY = UNRESOLVED
```

When producer authority is unresolved:

1. `produce_trusted_evidence_authorized(...)` MUST reject the request.
2. `_produce_trusted_evidence(...)` MUST NOT be invoked.
3. No trusted-origin token MUST be created.
4. `_TRUSTED_ORIGIN_BINDINGS` MUST NOT gain a new binding.
5. Existing G1–G5 behavior MUST remain unchanged.

---

## Observable regression invariant

A regression fixture for unresolved producer authority must be able to
observe both sides of the boundary:

```text
before call:
    trusted-origin binding count = N

attempt gated trusted production:
    producer authority = UNRESOLVED

after call:
    trusted producer primitive was not entered
    trusted-origin binding count = N
```

The test must not infer denial solely from an exception or return value.

It must also establish that trusted provenance creation did not occur.

---

## Gated entry point

The existing surface is:

```text
produce_trusted_evidence_authorized(...)
```

This function is the producer-authority gate.

It is distinct from:

```text
_produce_trusted_evidence(...)
```

The gated entry point may delegate to the provenance primitive only
after producer authority has been established.

---

## Authority input

This contract requires the gated entry point to receive an explicit
producer-authority decision input.

For v0.1, the minimum behavioral vocabulary is:

```text
AUTHORIZED
UNRESOLVED
REVOKED
```

Only `UNRESOLVED` behavior is frozen by this document.

`AUTHORIZED` and `REVOKED` are reserved for subsequent behavioral
regression work.

This vocabulary does not define a production credential format,
identity provider, or authorization database.

---

## Failure surface

For v0.1, this contract freezes fail-closed behavior but does not freeze
a canonical diagnostic or reason code.

A future regression may require a stable failure representation, but
this document does not yet define whether denial is represented by:

- an exception;
- a structured result;
- a status object;
- another explicit failure type.

The absence of a reason-code contract must not permit trusted
production to proceed.

---

## Preservation constraints

This behavioral contract must not silently change:

- G1 forged-evidence rejection semantics;
- G2 verifier-failure semantics;
- G3 public verifier-seam behavior;
- G4 trusted-producer positive-origin behavior;
- G5 post-production tamper detection;
- `_produce_trusted_evidence(...)` provenance semantics;
- `evaluate_evidence_origin(...)` semantics.

Existing Trust Evidence Origin regression must remain:

```text
PASS 5 / 5
```

---

## First executable RED target

The next regression must establish:

```text
producer authority = UNRESOLVED

expected:
    fail closed
    _produce_trusted_evidence(...) not called
    no trusted-origin binding added
```

The RED must fail because this behavior is not yet implemented.

It must not fail because of:

- import errors;
- missing gated-entry-point surface;
- syntax or indentation errors;
- unrelated G1–G5 regression failures.

---

## Not claimed

This document does not claim:

- producer-authority enforcement is implemented;
- caller authentication is implemented;
- caller identity is cryptographically verified;
- producer credentials exist;
- authority grant is implemented;
- authority revocation is implemented;
- `AUTHORIZED` behavior is implemented;
- `REVOKED` behavior is implemented;
- a canonical diagnostic exists;
- a canonical reason code exists;
- L/M fixture identifiers exist;
- execution authorization is covered.

---

## Closure boundary

This document freezes only the first behavioral requirement:

```text
UNRESOLVED producer authority
→ fail closed before trusted provenance creation
```

Behavior contract closure does not imply enforcement closure.
