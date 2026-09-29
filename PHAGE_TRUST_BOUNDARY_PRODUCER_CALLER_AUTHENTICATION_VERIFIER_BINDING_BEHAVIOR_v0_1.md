# PHAGE Trust Boundary — Producer Caller Authentication Verifier Binding Behavior v0.1

## Status

Behavioral contract definition only.

Caller-authentication verifier surface: IMPLEMENTED

Missing authentication evidence behavior: IMPLEMENTED

Supplied but unverified evidence behavior: IMPLEMENTED

Verifier-positive fixture behavior: IMPLEMENTED

Verifier-to-producer binding enforcement: NOT YET IMPLEMENTED

This document freezes how caller-authentication verification results
become authoritative input to the producer-authority gate.

It does not define a production credential format or identity provider.

---

## Core trust rule

Caller-controlled authentication status MUST NOT be authoritative.

Therefore:

```text
caller-supplied caller_authentication_status
!=
trusted authentication decision
```

The authoritative authentication state must originate from:

```text
authentication evidence
    |
    v
verify_caller_authentication(...)
    |
    v
verifier-controlled authentication status
    |
    v
producer-authority gate
```

---

## Prohibited direct trust path

The following path is not trusted:

```text
caller
→ caller_authentication_status="ESTABLISHED"
→ producer gate
→ trusted production
```

A caller MUST NOT obtain trusted production merely by self-asserting:

```text
ESTABLISHED
```

Presence of that string is not authentication evidence.

---

## Required verifier binding

The producer trust boundary must use the result of:

```text
verify_caller_authentication(authentication_evidence)
```

as the authentication decision consumed by the producer-authority gate.

Conceptually:

```text
authentication_evidence
→ verify_caller_authentication(...)
→ authentication_status
→ producer-authority composition
```

The caller must not independently control the effective
`authentication_status`.

---

## Negative binding behavior

For missing or unverified evidence:

```text
verify_caller_authentication(...)
→ NOT_ESTABLISHED
```

Therefore even if the caller attempts to claim:

```text
caller_authentication_status = ESTABLISHED
authority_status = AUTHORIZED
```

the effective authentication result remains:

```text
NOT_ESTABLISHED
```

and trusted production must fail closed:

```text
_produce_trusted_evidence(...) not called
trusted-origin binding count unchanged
```

---

## Positive binding behavior

For verifier-positive evidence:

```text
verify_caller_authentication(verified_evidence)
→ ESTABLISHED
```

When independently combined with:

```text
authority_status = AUTHORIZED
```

trusted production may proceed:

```text
ESTABLISHED + AUTHORIZED
→ _produce_trusted_evidence(...) exactly once
→ exactly one trusted-origin binding created
→ producer result returned
```

---

## Authentication remains distinct from authorization

Verifier-controlled authentication does not grant producer authority.

Therefore:

```text
ESTABLISHED
!=
AUTHORIZED
```

Existing authority-state semantics remain controlling:

```text
ESTABLISHED + UNRESOLVED
→ fail closed

ESTABLISHED + REVOKED
→ fail closed

ESTABLISHED + UNKNOWN / unsupported
→ fail closed
```

---

## Current verifier semantics preserved

Existing verifier behavior must remain:

```text
missing evidence
→ NOT_ESTABLISHED
```

```text
arbitrary supplied / unverified evidence
→ NOT_ESTABLISHED
```

```text
module-owned verified fixture
→ ESTABLISHED
```

Binding enforcement must consume those results without weakening them.

---

## Observable negative invariant

A future executable regression must demonstrate:

```text
caller claim:
    caller_authentication_status = ESTABLISHED

authentication evidence:
    missing or unverified

authority:
    AUTHORIZED
```

expected:

```text
verifier result = NOT_ESTABLISHED
effective authentication state = NOT_ESTABLISHED
producer call count = 0
trusted-origin binding count unchanged
```

This proves that caller self-assertion is not authoritative.

---

## Observable positive invariant

A future executable regression must demonstrate:

```text
authentication evidence:
    verifier-positive fixture

authority:
    AUTHORIZED
```

expected:

```text
verifier result = ESTABLISHED
effective authentication state = ESTABLISHED
producer call count = 1
trusted-origin binding count += 1
```

---

## Preservation constraints

Verifier binding must not silently change:

- missing-evidence fail-closed behavior;
- supplied-unverified fail-closed behavior;
- verifier-positive fixture behavior;
- NOT_ESTABLISHED + AUTHORIZED fail-closed behavior;
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

## First executable target

The first executable RED should demonstrate that a caller can still
currently self-assert authentication status independently of the
verifier result.

A minimal negative case is:

```text
authentication evidence = missing / unverified
caller_authentication_status = ESTABLISHED
authority_status = AUTHORIZED
```

expected:

```text
effective authentication = NOT_ESTABLISHED
trusted production does not occur
```

The RED should fail because verifier-to-producer binding is not yet
enforced.

It must not fail because of:

- syntax errors;
- import errors;
- missing verifier surface;
- missing verified fixture;
- G1–G5 regression failures;
- existing verifier behavior regressions.

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
- identity providers;
- credential storage;
- session management;
- credential rotation;
- production credential schema;
- canonical diagnostics;
- canonical reason codes;
- execution authorization.

---

## Closure boundary

This document freezes only:

```text
authentication evidence
→ trusted verifier result
→ effective producer authentication state
```

and prohibits:

```text
caller self-asserted ESTABLISHED
→ authoritative authentication
```

Verifier binding closure does not imply a complete production identity
or credential infrastructure.
