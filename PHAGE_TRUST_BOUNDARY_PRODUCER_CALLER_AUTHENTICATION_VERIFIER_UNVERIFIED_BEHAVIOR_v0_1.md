# PHAGE Trust Boundary — Producer Caller Authentication Verifier UNVERIFIED Behavior v0.1

## Status

Behavioral contract definition only.

Caller-authentication verifier surface: IMPLEMENTED

Verifier semantics for missing / unverified evidence: NOT YET IMPLEMENTED

Existing caller-authentication behavior:

- NOT_ESTABLISHED + AUTHORIZED: IMPLEMENTED FAIL-CLOSED
- ESTABLISHED + AUTHORIZED: CHARACTERIZED
- ESTABLISHED + non-AUTHORIZED authority: CHARACTERIZED FAIL-CLOSED

This document freezes the first concrete behavior of the trusted
caller-authentication verifier.

It does not define credential syntax or identity-provider semantics.

---

## Core rule

Missing or unverified caller-authentication evidence MUST NOT establish
trusted caller authentication.

Therefore:

```text
missing / unverified authentication evidence
→ verify_caller_authentication(...)
→ NOT_ESTABLISHED
```

and never:

```text
missing / unverified authentication evidence
→ ESTABLISHED
```

---

## Trust boundary

The intended path is:

```text
caller authentication evidence
    |
    v
verify_caller_authentication(...)
    |
    v
NOT_ESTABLISHED
    |
    v
producer-authority composition
```

For unverified evidence, the verifier-controlled result is
`NOT_ESTABLISHED`.

The caller must not be able to self-assert `ESTABLISHED`.

---

## Required verifier behavior

For evidence that is:

- missing;
- unverified;
- unsupported by the current verifier;
- not positively accepted by the trusted verification seam;

the verifier MUST produce:

```text
NOT_ESTABLISHED
```

It MUST NOT produce:

```text
ESTABLISHED
```

---

## Downstream fail-closed invariant

When the verifier result is:

```text
NOT_ESTABLISHED
```

and producer authority is:

```text
AUTHORIZED
```

the existing behavior remains:

```text
NOT_ESTABLISHED + AUTHORIZED
→ fail closed
→ _produce_trusted_evidence(...) not called
→ no new trusted-origin binding
```

The verifier must not bypass or weaken this boundary.

---

## Observable verifier invariant

A future executable regression must be able to establish:

```text
authentication evidence = missing / unverified
```

expected:

```text
verify_caller_authentication(...) == NOT_ESTABLISHED
```

The test must not require any concrete credential format.

---

## Observable downstream invariant

Given:

```text
authentication_result = NOT_ESTABLISHED
authority_status = AUTHORIZED
```

expected:

```text
producer call count = 0
trusted-origin binding count unchanged
```

---

## Preservation constraints

Implementingthis verifier behavior must not silently change:

- caller-authentication verifier surface;
- NOT_ESTABLISHED fail-closed enforcement;
- ESTABLISHED + AUTHORIZED behavior;
- ESTABLISHED + UNRESOLVED behavior;
- ESTABLISHED + REVOKED behavior;
- ESTABLISHED + UNKNOWN behavior;
- producer-authority state semantics;
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

The first executable regression should call:

```text
verify_caller_authentication(...)
```

with missing or otherwise unverified evidence and require:

```text
NOT_ESTABLISHED
```

The expected RED should occur because verifier semantics are not yet
implemented.

It must not fail because of:

- syntax errors;
- import errors;
- missing verifier surface;
- unrelated producer-authority regressions;
- G1–G5 failures.

---

## Not claimed

This document does not define:

- usernames;
- passwords;
- API keys;
- bearer tokens;
- JWTs;
- certificates;
- cryptographic signature algorithms;
- identity providers;
- credential storage;
- session management;
- credential rotation;
- canonical diagnostics;
- canonical reason codes;
- execution authorization.

---

## Closure boundary

This document freezes only:

```text
missing / unverified authentication evidence
→ trusted verifier result = NOT_ESTABLISHED
```

and preserves:

```text
NOT_ESTABLISHED + AUTHORIZED
→ fail closed
```

This does not imply a complete authentication system.
