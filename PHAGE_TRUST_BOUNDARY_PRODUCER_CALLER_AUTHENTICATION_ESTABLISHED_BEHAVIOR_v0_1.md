# PHAGE Trust Boundary — Producer Caller Authentication ESTABLISHED Behavior v0.1

## Status

Behavioral contract definition only.

Caller-authentication surface: IMPLEMENTED

NOT_ESTABLISHED fail-closed behavior: IMPLEMENTED

ESTABLISHED behavior: NOT YET CHARACTERIZED

Producer-authority state handling:

- UNRESOLVED: IMPLEMENTED
- AUTHORIZED: IMPLEMENTED
- REVOKED: IMPLEMENTED
- UNKNOWN / unsupported: CHARACTERIZED FAIL-CLOSED

This document freezes how established caller authentication composes
with existing producer-authority states.

It does not define an identity or credential system.

---

## Core separation

Caller authentication and producer authorization remain distinct.

```text
ESTABLISHED authentication
!=
AUTHORIZED producer authority
