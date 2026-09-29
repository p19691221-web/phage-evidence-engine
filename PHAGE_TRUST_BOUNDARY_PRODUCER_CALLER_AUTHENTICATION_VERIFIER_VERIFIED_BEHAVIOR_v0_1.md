# PHAGE Trust Boundary — Producer Caller Authentication Verifier VERIFIED Behavior v0.1

## Status

Behavioral contract definition only.

Caller-authentication verifier surface: IMPLEMENTED

Missing authentication evidence behavior: IMPLEMENTED

Supplied but unverified evidence behavior: IMPLEMENTED

Positive verified-evidence behavior: NOT YET IMPLEMENTED

This document freezes the positive trust boundary for caller
authentication verification.

It does not define a credential format, identity provider, or
cryptographic mechanism.

---

## Core rule

Authentication evidence is not trusted merely because it is present.

Therefore:

```text
evidence present
!=
evidence verified
```

and:

```text
caller self-assertion
!=
trusted authentication result
```

Only a positive decision produced by the trusted authentication
verifier may establish:

```text
ESTABLISHED
```

---

## Trusted positive path

The intended positive path is:

```text
caller authentication evidence
    |
    v
verify_caller_authentication(...)
    |
    v
trusted positive verifier decision
    |
    v
ESTABLISHED
```

The `ESTABLISHED` result must originate from verifier-controlled
acceptance.

It must not originate from an arbitrary caller-supplied status value.

---

## VERIFIED behavior

For authentication evidence positively accepted by the trusted verifier:

```text
verify_caller_authentication(verified_evidence)
→ ESTABLISHED
```

This is the only positive authentication result frozen by this
contract.

---

## Verification remains distinct from authorization

Successful authentication does not itself grant producer authority.

Therefore:

```text
ESTABLISHED
!=
AUTHORIZED
```

Trusted production is permitted only when both independently hold:

```text
authentication result = ESTABLISHED
authority_status = AUTHORIZED
```

Expected composition:

```text
ESTABLISHED + AUTHORIZED
→ trusted production permitted
```

---

## Authority preservation

Positive authentication MUST NOT override existing producer-authority
state.

Therefore:

```text
ESTABLISHED + UNRESOLVED
→ fail closed

ESTABLISHED + REVOKED
→ fail closed

ESTABLISHED + UNKNOWN / unsupported
→ fail closed
```

Authentication does not upgrade producer authority.

---

## Existing negative verifier behavior

The following behavior remains frozen:

```text
missing authentication evidence
→ NOT_ESTABLISHED
```

and:

```text
supplied but unverified authentication evidence
→ NOT_ESTABLISHED
```

A positive `ESTABLISHED` result therefore requires an explicit trusted
verifier-positive path.

---

## Observable verifier invariant

A future executable regression must be able to distinguish:

```text
unverified_evidence
→ NOT_ESTABLISHED
```

from:

```text
verified_evidence
→ ESTABLISHED
```

The regression must prove that positive authentication is controlled by
the verifier and is not inferred merely from evidence presence.

---

## Observable producer invariant

Given:

```text
authentication_result = ESTABLISHED
authority_status = AUTHORIZED
```

expected:

```text
_produce_trusted_evidence(...) called exactly once
trusted-origin binding count increases by exactly one
producer result returned
existing origin verification accepts the result
```

---

## Preservation constraints

Positive authentication verification must not silently change:

- missing-evidence fail-closed behavior;
- supplied-unverified fail-closed behavior;
- NOT_ESTABLISHED + AUTHORIZED fail-closed behavior;
- ESTABLISHED + AUTHORIZED producer behavior;
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

The next executable evidence must establish a verifier-controlled
positive path:

```text
verified authentication evidence
→ verify_caller_authentication(...)
→ ESTABLISHED
```

The test must not define a production credential format.

A minimal opaque trusted fixture or verifier-controlled sentinel may be
used solely to distinguish verifier-positive evidence from arbitrary
caller-supplied evidence.

The RED must fail because positive verification semantics are not yet
implemented.

It must not fail because of:

- syntax errors;
- import errors;
- missing verifier surface;
- G1–G5 regression failures;
- missing-evidence regression;
- supplied-unverified regression.

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
trusted verifier-positive evidence
→ ESTABLISHED
```

while preserving:

```text
unverified evidence
→ NOT_ESTABLISHED
```

and:

```text
ESTABLISHED authentication
!=
AUTHORIZED producer authority
```

Positive authentication-verifier closure does not imply a complete
identity, credential, or authorization infrastructure.
