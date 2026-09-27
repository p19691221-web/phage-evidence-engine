# PHAGE Trust Boundary — Producer Authority AUTHORIZED Behavior v0.1

## Status

Behavioral contract definition only.

UNRESOLVED fail-closed behavior: IMPLEMENTED

AUTHORIZED behavior: NOT YET IMPLEMENTED

REVOKED behavior: NOT YET IMPLEMENTED

This document freezes the positive-path behavior for established
producer authority.

It does not modify G1–G5 semantics.

---

## Existing boundary

The control flow remains:

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

`produce_trusted_evidence_authorized(...)` is the gated entry point.

`_produce_trusted_evidence(...)` remains the provenance-producing
primitive.

---

## AUTHORIZED behavioral rule

When producer authority is explicitly established as:

```text
AUTHORIZED
```

the gate MUST permit trusted evidence production.

The permitted call must delegate to:

```text
_produce_trusted_evidence(...)
```

exactly once.

---

## Required behavior

For:

```text
producer authority = AUTHORIZED
```

the following behavior is required:

1. `produce_trusted_evidence_authorized(...)` permits the request.
2. `_produce_trusted_evidence(...)` is invoked exactly once.
3. Producer arguments are forwarded without semantic mutation.
4. Exactly one new trusted-origin binding is created.
5. The returned candidate is the candidate produced by the trusted
   provenance primitive.
6. The returned candidate remains acceptable to the existing
   `evaluate_evidence_origin(...)` path.
7. Existing G1–G5 regression behavior remains unchanged.

---

## Observable regression invariant

A future executable regression must observe the boundary directly.

Before the gated call:

```text
trusted-origin binding count = N
producer call count = 0
```

After:

```text
authority = AUTHORIZED
```

the expected state is:

```text
producer call count = 1
trusted-origin binding count = N + 1
```

The returned candidate must then satisfy the existing trusted-origin
verification behavior.

---

## Delegation invariant

AUTHORIZED behavior must not duplicate provenance generation inside the
gate.

The gate delegates to the existing primitive:

```text
produce_trusted_evidence_authorized(...)
    |
    v
_produce_trusted_evidence(...)
```

Therefore:

```text
producer-authority decision
!=
trusted-origin provenance creation
```

The provenance primitive remains the single provenance-producing seam.

---

## Argument forwarding

The gate must forward the producer inputs required by the existing
primitive without changing their semantic values:

```text
value
source
schedule_ref
policy_version
observed_at
```

The AUTHORIZED decision itself is not part of the evidence-content
snapshot.

---

## Existing origin verification

After AUTHORIZED trusted production, the returned candidate must remain
compatible with:

```text
evaluate_evidence_origin(...)
```

The existing positive-origin behavior must remain valid.

This contract does not redefine the evidence-origin verifier.

---

## Preservation constraints

AUTHORIZED behavior must not silently change:

- G1 forged-evidence rejection semantics;
- G2 verifier-failure semantics;
- G3 public verifier-seam behavior;
- G4 trusted-producer positive-origin behavior;
- G5 post-production tamper detection;
- UNRESOLVED fail-closed behavior;
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
producer authority = AUTHORIZED

expected:
    gated request permitted
    _produce_trusted_evidence(...) called exactly once
    trusted-origin binding count increases by exactly one
    returned candidate verifies as trusted origin
```

The RED must fail because AUTHORIZED delegation is not yet implemented.

It must not fail because of:

- import errors;
- missing gated-entry-point surface;
- syntax or indentation errors;
- unrelated G1–G5 failures;
- UNRESOLVED behavior regression.

---

## Not claimed

This document does not claim:

- REVOKED behavior is implemented;
- caller authentication is implemented;
- caller identity is cryptographically verified;
- a production credential format exists;
- authority grant infrastructure exists;
- authority revocation infrastructure exists;
- a canonical diagnostic exists;
- a canonical reason code exists;
- L/M fixture identifiers exist;
- execution authorization is covered.

---

## Closure boundary

This document freezes only:

```text
AUTHORIZED producer authority
→ permit trusted production
→ provenance primitive exactly once
→ one new trusted-origin binding
→ returned evidence remains origin-verifiable
```

AUTHORIZED behavior closure does not imply complete
producer-authority enforcement closure.
