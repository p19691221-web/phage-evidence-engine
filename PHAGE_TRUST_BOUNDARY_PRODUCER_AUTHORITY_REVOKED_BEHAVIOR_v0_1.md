# PHAGE Trust Boundary — Producer Authority REVOKED Behavior v0.1

## Status

Behavioral contract definition only.

UNRESOLVED behavior: IMPLEMENTED

AUTHORIZED behavior: IMPLEMENTED

REVOKED behavior: NOT YET IMPLEMENTED

This document freezes the fail-closed behavior for revoked producer authority.

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
