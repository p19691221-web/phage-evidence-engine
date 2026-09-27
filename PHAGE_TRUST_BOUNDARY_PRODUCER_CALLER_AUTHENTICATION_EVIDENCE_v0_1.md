# PHAGE Trust Boundary — Producer Caller Authentication Evidence v0.1

## Status

Behavioral contract definition only.

Caller-authentication surface: IMPLEMENTED

NOT_ESTABLISHED fail-closed behavior: IMPLEMENTED

ESTABLISHED + AUTHORIZED behavior: CHARACTERIZED

Authentication-evidence verification seam: NOT YET IMPLEMENTED

This document freezes the trust boundary between caller-supplied
authentication material and the authentication status consumed by the
producer-authority gate.

It does not define a credential format or identity provider.

---

## Core trust rule

A caller MUST NOT establish its own trusted authentication state merely
by supplying:

```text
caller_authentication_status = ESTABLISHED
```

Therefore:

```text
caller self-asserted ESTABLISHED
!=
trusted authentication result
```

`ESTABLISHED` must ultimately originate from a trusted authentication
verification seam rather than from an unverified caller-controlled
status string.

---

## Required flow

The intended boundary is:

```text
caller authentication evidence
    |
    v
trusted authentication verifier seam
    |
    v
authentication result
    |
    v
producer-authority gate
    |
    v
trusted production
```

The producer-authority gate consumes an authentication result.

It must not itself treat arbitrary caller-supplied authentication claims
as verified identity.

---

## Missing or unverified evidence

For missing, malformed, unsupported, or unverified authentication
evidence:

```text
authentication result MUST NOT be ESTABLISHED
```

Such evidence must not permit trusted production through an
`AUTHORIZED` producer-authority state.

Therefore:

```text
unverified authentication evidence
+
authority_status = AUTHORIZED

→ trusted production MUST NOT occur
```

---

## Verified evidence

Successfully verified authentication evidence:

```text
MAY produce authentication result = ESTABLISHED
```

However:

```text
ESTABLISHED authentication
!=
AUTHORIZED producer authority
```

Authentication and producer authorization remain independent gates.

Trusted production is permitted only when both required conditions are
satisfied independently.

---

## Existing composition semantics

The following existing behavior must remain unchanged:

```text
NOT_ESTABLISHED + AUTHORIZED
→ fail closed
```

```text
ESTABLISHED + AUTHORIZED
→ trusted production permitted
```

```text
ESTABLISHED + UNRESOLVED
→ fail closed
```

```text
ESTABLISHED + REVOKED
→ fail closed
```

```text
ESTABLISHED + UNKNOWN
→ fail closed
```

---

## Verification seam invariant

A future executable surface must expose a trusted authentication
verification seam.

Conceptually:

```text
verify_caller_authentication(authentication_evidence)
    |
    v
ESTABLISHED | NOT_ESTABLISHED
```

The exact function name is not frozen by this document.

Thesemantic invariant is:

```text
authentication evidence
→ verifier-controlled result
→ producer-authority composition
```

not:

```text
caller-controlled status string
→ trusted authentication
```

---

## Observable negative invariant

A future regression must be able to demonstrate:

```text
before request:
    producer call count = 0
    trusted-origin binding count = N
```

For unverified authentication evidence:

```text
after request:
    authentication result != ESTABLISHED
    producer call count = 0
    trusted-origin binding count = N
```

The trusted provenance primitive must not be entered.

---

## Observable positive invariant

For evidence accepted by the trusted authentication verifier:

```text
authentication result = ESTABLISHED
```

This result may then compose with an independently AUTHORIZED producer
authority.

The existing positive producer path remains:

```text
ESTABLISHED
+
AUTHORIZED
→ _produce_trusted_evidence(...) exactly once
```

---

## Preservation constraints

Authentication-evidence enforcement must not silently change:

- NOT_ESTABLISHED fail-closed behavior;
- ESTABLISHED + AUTHORIZED behavior;
- UNRESOLVED producer-authority behavior;
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

The next executable evidence should first determine whether a trusted
authentication-verifier seam already exists.

If no such seam exists, the natural first RED is a surface RED proving
that authentication verification is not yet exposed.

The RED must not invent:

- a credential format;
- a token type;
- an identity provider;
- a cryptographic algorithm;
- a reason-code vocabulary.

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
- canonical diagnostics;
- canonical reason codes;
- execution authorization.

---

## Closure boundary

This document freezes only:

```text
caller-supplied authentication claim
→ MUST NOT itself establish trusted authentication
```

and:

```text
trusted authentication evidence
→ verifier-controlled authentication result
→ producer-authority composition
```

Authentication-evidence closure does not imply a complete identity,
credential, or authorization infrastructure.
