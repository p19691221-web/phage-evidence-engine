# PHAGE Trust Boundary — Producer Authority Contract v0.1

## Status

Contract definition only.

Executable enforcement: NOT YET IMPLEMENTED

This document freezes the boundary between producer-caller authority
and existing Trust Evidence Origin provenance verification.

It does not modify G1–G5 semantics.

---

## Purpose

PHAGE Trust Evidence Origin v0.1 currently assumes that access to the
trusted evidence producer path is governed by an external trust boundary.

The existing producer primitive:

`_produce_trusted_evidence(...)`

establishes provenance for evidence produced through that path.

It does not authenticate the caller and does not determine whether the
caller is authorized to invoke trusted evidence production.

This contract defines where producer-authority enforcement belongs.

---

## Core distinctions

The following distinctions are normative:

`caller authentication != caller authorization`

`producer authorization != evidence-origin verification`

`producer authorization != execution authorization`

`assumed genesis producer authority != verified producer authority`

`G4/G5 PASS != producer caller authorization`

---

## Boundary

The intended control flow is:

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
