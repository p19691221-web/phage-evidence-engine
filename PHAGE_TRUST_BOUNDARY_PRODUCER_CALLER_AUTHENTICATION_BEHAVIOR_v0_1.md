# PHAGE Trust Boundary — Producer Caller Authentication Behavior v0.1

## Status

Behavioral contract definition only.

Producer-authority state handling:

- UNRESOLVED: IMPLEMENTED
- AUTHORIZED: IMPLEMENTED
- REVOKED: IMPLEMENTED
- UNKNOWN / unsupported: CHARACTERIZED FAIL-CLOSED

Caller authentication enforcement: NOT YET IMPLEMENTED

This document freezes the first caller-authentication boundary that
precedes producer-authority use.

It does not define a production identity or credential system.

---

## Existing authority boundary

The current producer-authority gate distinguishes:

```text
UNRESOLVED
AUTHORIZED
REVOKED
UNKNOWN / unsupported
```

The trusted production path remains:

```text
caller context
    |
    v
caller-authentication boundary
    |
    v
producer-authority decision
    |
    v
produce_trusted_evidence_authorized(...)
    |
    v
_produce_trusted_evidence(...)
```

Caller authentication and producer authority are distinct concerns.

---

## Core rule

A caller whose authentication has not been established MUST NOT be
treated as an AUTHORIZED producer.

Therefore:

```text
caller authentication = NOT_ESTABLISHED
→ producer authority MUST NOT resolve to AUTHORIZED
→ trusted production MUST NOT occur
```

---

## Required behavior

For:

```text
caller authentication = NOT_ESTABLISHED
```

the following requirements are frozen:

1. The caller MUST NOT receive effective `AUTHORIZED` producer authority.
2. `_produce_trusted_evidence(...)` MUST NOT be invoked as a consequence
   of that caller request.
3. No trusted-origin token MUST be created.
4. `_TRUSTED_ORIGIN_BINDINGS` MUST NOT gain a new binding.
5. Existing producer-authority state semantics MUST remain unchanged.
6. Existing G1–G5 behavior MUST remain unchanged.

---

## Authentication is not authorization

This contract explicitly separates:

```text
caller authenticated
```

from:

```text
producer authorized
```

Authentication may be a prerequisite for authorization, but successful
authentication alone does not imply producer authority.

Therefore this contract does NOT establish:

```text
AUTHENTICATED → AUTHORIZED
```

It freezes only the negative direction:

```text
NOT_ESTABLISHED authentication
→ MUST NOT become AUTHORIZED
```

---

## Observable boundary invariant

A future executable regression must be able to observe:

```text
before request:
    trusted-origin binding count = N
    producer primitive call count = 0
```

For an unauthenticated / authentication-not-established caller:

```text
after request:
    effective producer authority != AUTHORIZED
    producer primitive call count = 0
    trusted-origin binding count = N
```

Theregression must prove that trusted production was not entered.

---

## Preservation constraints

Caller-authentication enforcement must not silently change:

- UNRESOLVED producer-authority behavior;
- AUTHORIZED producer-authority behavior;
- REVOKED producer-authority behavior;
- UNKNOWN / unsupported fail-closed behavior;
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

## First executable target

The first executable regression for this boundary must establish:

```text
caller authentication = NOT_ESTABLISHED

expected:
    effective producer authority is not AUTHORIZED
    _produce_trusted_evidence(...) not called
    trusted-origin binding count unchanged
```

Whether this first regression is RED or characterization GREEN depends
on the current implementation surface.

A RED must not be manufactured by introducing requirements that are not
frozen by this contract.

---

## Not claimed

This document does not define:

- usernames or accounts;
- passwords;
- API keys;
- bearer tokens;
- JWTs;
- certificates;
- cryptographic signature algorithms;
- an identity provider;
- credential storage;
- session management;
- credential rotation;
- canonical diagnostics;
- canonical reason codes;
- L/M fixture identifiers;
- execution authorization.

---

## Closure boundary

This document freezes only:

```text
caller authentication NOT_ESTABLISHED
→ caller MUST NOT obtain effective AUTHORIZED producer authority
→ trusted production MUST NOT occur
```

Caller-authentication contract closure does not imply a complete
authentication or authorization system.
