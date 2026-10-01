# PHAGE Trust Boundary — Producer Authority Verifier Binding Behavior v0.1

## Status

Behavioral contract definition only.

Caller-authentication verifier binding: IMPLEMENTED

Producer-authority verifier binding: NOT YET IMPLEMENTED

This document freezes how producer authority must become authoritative
inside the producer trust boundary.

It does not define a production authorization system, policy engine,
role model, identity provider, or credential format.

---

## Core trust rule

Caller-controlled producer authority MUST NOT be authoritative.

Therefore:

```text
caller-supplied authority_status
!=
trusted authority decision
```

The authoritative producer-authority state must originate from:

```text
authority evidence
    |
    v
verify_producer_authority(...)
    |
    v
verifier-controlled authority state
    |
    v
producer gate
```

---

## Prohibited direct trust path

The following path is not trusted:

```text
caller
→ authority_status="AUTHORIZED"
→ producer gate
→ trusted production
```

A caller MUST NOT obtain trusted production merely by self-asserting:

```text
AUTHORIZED
```

Presence of that string is not authority evidence.

---

## Required authority binding

The producer trust boundary must use the result of:

```text
verify_producer_authority(authority_evidence)
```

as the authority decision consumed by the producer gate.

Conceptually:

```text
authority_evidence
→ verify_producer_authority(...)
→ effective_authority_status
→ producer gate
```

The caller must not independently control the effective authority state.

---

## Authentication remains independently required

Authority verification does not replace authentication.

Trusted production requires both independently established conditions:

```text
authentication result = ESTABLISHED
authority result = AUTHORIZED
```

Expected composition:

```text
ESTABLISHED + AUTHORIZED
→ trusted production permitted
```

Neither state implies the other.

---

## Negative authority behavior

For missing, unresolved, revoked, unsupported, or otherwise unverified
authority evidence:

```text
verify_producer_authority(...)
→ non-AUTHORIZED effective state
```

Therefore even if the caller attempts to claim:

```text
authority_status = AUTHORIZED
```

trusted production must not proceed unless the authority verifier itself
produces:

```text
AUTHORIZED
```

Expected:

```text
_produce_trusted_evidence(...) not called
trusted-origin binding count unchanged
```

---

## Positive authority behavior

For verifier-positive authority evidence:

```text
verify_producer_authority(verified_authority_evidence)
→ AUTHORIZED
```

When independently combined with:

```text
authentication result = ESTABLISHED
```

trusted production may proceed:

```text
ESTABLISHED + AUTHORIZED
→ _produce_trusted_evidence(...) exactly once
→ exactly one trusted-origin binding created
→ producer result returned
```

---

## Existing authority semantics preserved

The current authority-state semantics remain conceptually distinct:

```text
UNRESOLVED
→ fail closed

REVOKED
→ fail closed

UNKNOWN / unsupported
→ fail closed or explicit unsupported-state behavior

AUTHORIZED
→ may proceed only when independently authenticated
```

Binding enforcement must not weaken these semantics.

---

## Observable negative invariant

A future executable regression must demonstrate:

```text
authentication = verifier-established ESTABLISHED

caller claim:
    authority_status = AUTHORIZED

authority evidence:
    missing / unverified
```

expected:

```text
effective authority != AUTHORIZED
producer call count = 0
trusted-origin binding count unchanged
```

This proves that caller self-assertion is not authoritative.

---

## Observable positive invariant

A future executable regression must demonstrate:

```text
authentication evidence:
    verifier-positive

authority evidence:
    verifier-positive
```

expected:

```text
effective authentication = ESTABLISHED
effective authority = AUTHORIZED
producer call count = 1
trusted-origin binding count += 1
```

---

## Preservation constraints

Authority-verifier binding must not silently change:

- caller-authentication verifier behavior;
- missing authentication evidence → NOT_ESTABLISHED;
- supplied unverified authentication evidence → NOT_ESTABLISHED;
- verified authentication fixture → ESTABLISHED;
- caller self-asserted authentication status being non-authoritative;
- UNRESOLVED authority fail-closed behavior;
- REVOKED authority fail-closed behavior;
- UNKNOWN / unsupported authority behavior;
- G1 forged-evidence rejection semantics;
- G2 verifier-failure semantics;
- G3 public verifier-seam behavior;
- G4 trusted-producer positive-origin behavior;
- G5 post-production tamper detection;
- G6 applicable-evidence reuse behavior;
- `_produce_trusted_evidence(...)` provenance semantics;
- `evaluate_evidence_origin(...)` semantics.

Existing Trust Evidence Origin regression must remain:

```text
PASS 5 / 5
```

---

## First executable target

The first executable RED should demonstrate:

```text
authentication evidence = verifier-positive
caller authority_status = AUTHORIZED
authority evidence = missing / unverified
```

expected:

```text
trusted production does not occur
```

The RED should fail because producer-authority verifier binding is not yet
enforced.

It must not fail because of:

- syntax errors;
- import errors;
- authentication verifier regressions;
- missing authentication fixture;
- G1–G5 failures;
- G6 failures.

---

## Not claimed

This document does not define:

- RBAC;
- ABAC;
- roles;
- groups;
- permissions databases;
- JWT authorization claims;
- OAuth scopes;
- certificates;
- policy engines;
- entitlement stores;
- production authorization infrastructure;
- canonical diagnostics;
- canonical reason codes.

---

## Closure boundary

This document freezes only:

```text
authority evidence
→ trusted authority verifier result
→ effective producer authority state
```

and prohibits:

```text
caller self-asserted AUTHORIZED
→ authoritative producer authority
```

Authority-verifier binding closure does not imply a complete production
authorization infrastructure.
