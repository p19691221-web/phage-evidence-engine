# DF-016 Digital Custody Design v0.1

## Status

DESIGN DRAFT — NO IMPLEMENTATION CLAIM

This document defines the initial Digital Custody boundary for DF-016.

It does not modify the existing PHAGE Lineage Contract v0.1 and does not
claim that Digital Custody enforcement has been implemented or validated.

---

## 1. Design objective

DF-016 currently validates evidence lineage integrity:

- evidence identity;
- `observed_at`;
- `available_at`;
- `derived_from`;
- epistemic cutoff;
- derivation cutoff;
- missing ancestors;
- lineage cycles;
- lineage depth.

Digital Custody addresses a different question:

> Who handled a digital artifact, when was it handled or transferred,
> and did the artifact remain continuously identifiable and intact?

The purpose of Digital Custody is to represent and validate handling history
without changing the semantic meaning of evidence derivation.

---

## 2. Lineage and Custody are separate dimensions

### Lineage

Lineage answers:

> What evidence or artifact was this item derived from?

Existing relation:

```text
derived evidence
    ↓
derived_from
    ↓
ancestor evidence
```

### Digital Custody

Custody answers:

> Who possessed, handled, transferred, copied, transformed, or verified
> this artifact over time?

Conceptual relation:

```text
artifact
  ↓
custody event
  ↓
custodian / actor
  ↓
next custody event
```

Therefore:

```text
derived_from != custody_chain
```

A transfer of custody does not by itself create a new derivational ancestor.

A derivation does not by itself prove continuous custody.

---

## 3. Scope of v0.1

Digital Custody v0.1 is limited to four invariants:

```text
CUSTODY_CONTINUITY
ARTIFACT_INTEGRITY
EVENT_TRACEABILITY
NO_SILENT_GAP
```

This version does not attempt to model:

- legal admissibility;
- criminal or civil responsibility;
- GDPR or other regulatory compliance;
- whether a custodian was legally entitled to possess evidence;
- organizational authorization policy;
- evidentiary weight;
- truth of the underlying claim;
- identity assurance beyond the identifiers supplied to the fixture.

Those belong to later authority, policy, legal, or identity layers.

---

## 4. Conceptual custody event

A Digital Custody event should be able to represent at least:

```text
CustodyEvent

event_id
artifact_id
event_type
actor_id
timestamp
from_custodian
to_custodian
artifact_fingerprint
previous_event_id
transformation_authorized
details
```

This is a conceptual schema only.

No field in this section is frozen as a Python API by this document.

---

## 5. Event types

The initial event vocabulary may include:

```text
ACQUIRED
RECEIVED
TRANSFERRED
COPIED
TRANSFORMED
VERIFIED
RELEASED
DELETED
```

The exact enum is not frozen by v0.1.

The important requirement is that an event must state what happened to the
artifact rather than silently changing custody state.

---

## 6. Invariant 1 — CUSTODY_CONTINUITY
Each custody transfer must connect to the previous recorded custody state.

Conceptual valid chain:

```text
ACQUIRED by A
→ TRANSFERRED A -> B
→ TRANSFERRED B -> C
```

Invalid example:

```text
ACQUIRED by A
→ TRANSFERRED X -> C
```

where no prior event establishes `X` as the current custodian.

Expected disposition:

```text
CUSTODY_CONTINUITY_VIOLATION
```

Continuity is about recorded possession history.

It does not establish that possession itself was legally authorized.

---

## 7. Invariant 2 — ARTIFACT_INTEGRITY

When custody changes without an explicitly authorized transformation,
the artifact fingerprint must remain stable.

Conceptual valid transfer:

```text
A holds artifact hash H1
→ transfer A -> B
→ B receives artifact hash H1
```

Conceptual integrity failure:

```text
A holds artifact hash H1
→ transfer A -> B
→ B receives artifact hash H2
→ no authorized transformation recorded
```

Expected disposition:

```text
CUSTODY_INTEGRITY_VIOLATION
```

A changed fingerprint is not automatically misconduct or tampering.

The validator only establishes that continuity of artifact identity cannot
be accepted under the supplied custody record.

---

## 8. Authorized transformation

A fingerprint change may be legitimate when a transformation is explicitly
recorded.

Conceptual example:

```text
artifact H1
→ TRANSFORMED
→ artifact H2
→ transformation_authorized = true
```

Digital Custody v0.1 does not determine whether the transformation should
have been authorized.

It only requires the transformation to be explicit rather than silent.

The relationship between transformed artifacts and evidence derivation
remains a separate design question and must not be inferred automatically.

---

## 9. Invariant 3 — EVENT_TRACEABILITY

Every custody event must be attributable to a minimum observable record.

At minimum, an event must identify:

```text
artifact
actor
timestamp
event type
```

If a required event cannot identify the artifact, actor, time, or event
semantics sufficiently to reconstruct the handling sequence, the chain
must not be treated as CLEAN.

Expected disposition:

```text
CUSTODY_UNRESOLVED
```

Traceability does not prove the supplied actor identity is authentic.
It only requires the custody record to identify the claimed actor.

---

## 10. Invariant 4 — NO_SILENT_GAP

Missing custody history must remain unresolved.

Example:

```text
A possesses artifact
→ [unknown interval / missing event]
→ C possesses artifact
```

The validator must not infer:

```text
A -> C
```

unless the supplied custody evidence supports that transition.

Expected disposition:

```text
CUSTODY_UNRESOLVED
```

Absence of a recorded event is not evidence that a valid transfer occurred.

---

## 11. Initial result taxonomy
Digital Custody v0.1 proposes the following minimal result states:

```text
CLEAN

CUSTODY_UNRESOLVED

CUSTODY_CONTINUITY_VIOLATION

CUSTODY_INTEGRITY_VIOLATION
```

These names apply to the Digital Custody design only.

They do not modify the existing `LineageStatus` taxonomy:

```text
CLEAN
EPISTEMIC_BOUNDARY_VIOLATION
DERIVATION_BOUNDARY_VIOLATION
LINEAGE_UNRESOLVED
LINEAGE_CYCLE_DETECTED
LINEAGE_MAX_DEPTH_EXCEEDED
```

The two taxonomies must remain distinguishable until an explicit integration
design is separately validated.

---

## 12. Proposed first regression fixtures

### A — Clean custody transfer

```text
artifact H1

ACQUIRED by Alice
→ TRANSFERRED Alice -> Bob
→ TRANSFERRED Bob -> Carol

fingerprint remains H1
```

Expected:

```text
CLEAN
```

### B — Custody gap

```text
artifact H1

ACQUIRED by Alice
→ missing / unknown custody event
→ Carol receives artifact
```

Expected:

```text
CUSTODY_UNRESOLVED
```

### C — Integrity break

```text
Alice holds artifact H1
→ TRANSFERRED Alice -> Bob
→ Bob receives artifact H2

authorized transformation = false
```

Expected:

```text
CUSTODY_INTEGRITY_VIOLATION
```

### D — Discontinuous custodian

```text
Alice holds artifact H1
→ TRANSFERRED Bob -> Carol
```

No prior custody event establishes Bob as current custodian.

Expected:

```text
CUSTODY_CONTINUITY_VIOLATION
```

No fixture in v0.1 should be changed merely to obtain a green regression.

---

## 13. Relationship to existing DF-016 lineage

Existing DF-016 lineage protects derivational and epistemic structure.

Conceptual combined model:

```text
                 Evidence / Artifact
                  /             \
                 /               \
          Lineage                 Custody
             |                       |
      derived_from[]          custody_events[]
             |                       |
   epistemic ancestry       handling / integrity
```

Examples:

```text
LINEAGE_UNRESOLVED
```

means an evidentiary ancestor is missing.

It does not mean custody history is missing.

Likewise:

```text
CUSTODY_UNRESOLVED
```

means the handling chain cannot be reconstructed from the supplied custody
events.

It does not mean the artifact's evidentiary ancestry is unknown.

---

## 14. Fail-closed semantics
Digital Custody must not convert missing information into CLEAN.

Conceptually:

```text
complete continuous custody + intact artifact
→ CLEAN

missing required custody evidence
→ CUSTODY_UNRESOLVED

known continuity contradiction
→ CUSTODY_CONTINUITY_VIOLATION

known unexplained fingerprint change
→ CUSTODY_INTEGRITY_VIOLATION
```

`UNRESOLVED` must not be interpreted as false, fraudulent, manipulated,
inadmissible, or malicious.

---

## 15. Explicit non-claims

Digital Custody v0.1 does NOT establish:

```text
artifact truth
claim truth
legal admissibility
criminal responsibility
civil responsibility
custodian authorization
regulatory compliance
actor identity authenticity
intentional tampering
evidentiary weight
```

A CLEAN custody result means only that the supplied custody record satisfies
the validated Digital Custody invariants.

It does not make the artifact true, trustworthy, legally admissible,
authorized, or sufficient.

---

## 16. Design freeze discipline

Before implementation:

```text
DO NOT modify existing DF-016 lineage semantics.

DO NOT reuse derived_from as custody history.

DO NOT expand legal or authority policy into Digital Custody v0.1.

DO NOT change the proposed fixture outcomes merely to make implementation pass.

DO NOT interpret UNRESOLVED as a failure of the underlying real-world claim.
```

If implementation pressure reveals that this design cannot express an
important custody condition, record the pressure first.

Specification expansion must occur explicitly rather than being introduced
silently during regression repair.

---

## 17. v0.1 disposition

```text
DF016_EXISTING_LINEAGE_CONTRACT = PRESERVED

DIGITAL_CUSTODY_DESIGN = DRAFT_V0_1

INITIAL_INVARIANTS = 4

CUSTODY_CONTINUITY = DEFINED
ARTIFACT_INTEGRITY = DEFINED
EVENT_TRACEABILITY = DEFINED
NO_SILENT_GAP = DEFINED

INITIAL_TAXONOMY = PROPOSED

IMPLEMENTATION = NOT_STARTED
REGRESSION = NOT_STARTED
PRODUCTION_READINESS = NOT_ESTABLISHED
LEGAL_ADMISSIBILITY = NOT_ESTABLISHED
```

This document freezes the initial Digital Custody design boundary.

Implementation and regression evidence must be introduced in later commits
and validation records rather than broadening the meaning of this design
document retroactively.
