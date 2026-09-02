# PHAGE Authority Engine Design v0.1

## Status

DESIGN DRAFT — NO IMPLEMENTATION CLAIM

This document defines the initial Authority Engine boundary for PHAGE.

It does not claim that a production authority system, institutional policy
engine, legal authorization system, or production identity trust layer has
been implemented or validated.

Existing PHAGE assessment, lineage, Digital Custody, Gateway, session, and
tool-effect behavior remain separate contracts unless explicitly connected
by later validated integration work.

---

## 1. Design objective

PHAGE already has prototype paths capable of:

```text
assessment
→ Gateway decision
→ ALLOW / BLOCK
→ Tool Adapter
→ effect / no effect
```

and a tested pre-effect session revalidation path that can prevent execution
after session revocation.

The next architectural question is different:

> What gives an actor or session the authority to request a particular action
> against a particular target, and how does PHAGE determine that the authority
> is still valid when execution occurs?

Authority Engine v0.1 defines that boundary.

It does not create institutional policy.

It validates supplied authority records against explicit structural
invariants.

---

## 2. Separation of concerns

PHAGE must preserve the distinction:

```text
Identity
≠ Authority
≠ Gateway Decision
≠ Execution
```

### Identity

Identity answers:

> Who or what is presenting the request?

Successful identity verification does not itself grant permission to act.

### Authority

Authority answers:

> What actions and targets has an identified subject been explicitly
> delegated authority to request?

### Gateway

Gateway answers:

> Given the supplied request and currently valid authority, should this
> action proceed across this policy boundary?

### Execution

Execution answers:

> May the effect still occur at the actual effect boundary?

Therefore:

```text
authenticated ≠ authorized
authorized ≠ permanently authorized
Gateway ALLOW ≠ perpetual execution right
```

---

## 3. Scope of Authority Engine v0.1

The initial Authority Engine is limited to five invariants:

```text
AUTHORITY_SOURCE_EXPLICIT
AUTHORITY_SCOPE_MATCH
AUTHORITY_NOT_REVOKED
AUTHORITY_NOT_EXPIRED
NO_STALE_AUTHORITY_AT_EXECUTION
```

This version does not attempt to decide:

- whether an organization should grant authority;
- whether a law permits the underlying action;
- whether an authority issuer is legally competent;
- employment or organizational hierarchy;
- criminal or civil responsibility;
- actor intent;
- policy correctness;
- production identity authenticity;
- institutional compliance;
- whether an action is substantively good or desirable.

Those remain external governance, legal, identity, or organizational-policy
questions.

---

## 4. Conceptual authority record

Authority Engine v0.1 should be able to reason about a record containing at
least:

```text
AuthorityGrant

grant_id
subject_id
issuer_id
authorized_actions
authorized_targets
issued_at
expires_at
revoked
revoked_at
source_ref
```

This is a conceptual schema only.

No field in this section is frozen as a Python API by this design document.

The essential idea is that authority must be represented as explicit data,
not inferred from identity, role names, session existence, or a previous
Gateway decision.

---

## 5. Invariant 1 — AUTHORITY_SOURCE_EXPLICIT
Authority must have an explicit source that can be identified from the
supplied authority record.

A request must not become authorized merely because:

```text
the subject authenticated successfully
the subject has an active session
the subject has a particular role name
a previous request was allowed
the Gateway previously returned ALLOW
```

Conceptual valid authority:

```text
grant_id = G-001
subject_id = agent-A
issuer_id = authority-service
source_ref = policy-record-17
```

Conceptual unresolved authority:

```text
subject_id = agent-A
authorized_actions = [ACTION_X]

issuer_id = unknown
source_ref = missing
```

Expected disposition:

```text
AUTHORITY_UNRESOLVED
```

The validator does not determine whether the issuer was legally entitled to
issue the grant.

It only requires the asserted authority source to be explicit rather than
silently inferred.

---

## 6. Invariant 2 — AUTHORITY_SCOPE_MATCH

A valid authority grant must cover the requested action and target.

Conceptual valid request:

```text
grant:
  authorized_actions = [READ]
  authorized_targets = [record-123]

request:
  action = READ
  target = record-123
```

Expected:

```text
CLEAN
```

Conceptual action-scope violation:

```text
grant:
  authorized_actions = [READ]

request:
  action = DELETE
```

Conceptual target-scope violation:

```text
grant:
  authorized_targets = [record-123]

request:
  target = record-999
```

Expected disposition:

```text
AUTHORITY_SCOPE_VIOLATION
```

Possession of some authority must not be treated as possession of all
authority.

---

## 7. Invariant 3 — AUTHORITY_NOT_REVOKED

A revoked authority grant must not authorize a new decision or effect.

Conceptual sequence:

```text
grant G-001 = active
→ Gateway evaluates request
→ grant G-001 = revoked
→ execution attempt
```

At the execution boundary, the revoked grant must not remain usable merely
because an earlier Gateway evaluation returned ALLOW.

Expected disposition:

```text
AUTHORITY_REVOKED
```

Revocation is a change in authority state.

It must not be treated as cosmetic metadata.

---

## 8. Invariant 4 — AUTHORITY_NOT_EXPIRED

Authority must be valid at the time it is relied upon.

Conceptual example:

```text
grant.expires_at = 12:00

request evaluated at 11:59
→ potentially valid

effect attempted at 12:01
→ expired
```

Expected disposition at the later boundary:

```text
AUTHORITY_EXPIRED
```

A grant that was valid when a session was established or when Gateway first
evaluated a request does not remain valid after expiration.

---

## 9. Invariant 5 — NO_STALE_AUTHORITY_AT_EXECUTION

Gateway ALLOW must not function as a permanently reusable authority token.

The execution boundary must re-establish that the authority relied upon for
the decision is still valid for the same:

```text
subject
action
target
grant
```

Conceptual TOCTOU sequence:

```text
T1: grant G-001 authorizes subject A for ACTION_X on TARGET_Y
T2: Gateway returns ALLOW
T3: grant G-001 is revoked, expires, disappears, or is superseded
T4: Tool Adapter attempts effect
```

The effect must not proceed solely on the basis of the T2 ALLOW result.

Expected disposition depends on the observed authority state:

```text
grant missing / cannot be resolved
→ AUTHORITY_UNRESOLVED

grant revoked
→ AUTHORITY_REVOKED

grant expired
→ AUTHORITY_EXPIRED

action or target no longer covered
→ AUTHORITY_SCOPE_VIOLATION
```

The invariant is:

```text
decision-time authority validity
does not imply
effect-time authority validity
```

This design intentionally mirrors the already-tested PHAGE session
revocation lesson:

```text
earlier ALLOW ≠ permanent right to produce an effect
```

Authority must be revalidated at the boundary where it is actually relied
upon.

---

## 10. Initial result taxonomy
Authority Engine v0.1 proposes the following minimal result states:

```text
CLEAN

AUTHORITY_UNRESOLVED

AUTHORITY_SCOPE_VIOLATION

AUTHORITY_REVOKED

AUTHORITY_EXPIRED
```

`NO_STALE_AUTHORITY_AT_EXECUTION` is an execution-time invariant, not a
separate result taxonomy member.

A stale authority condition must resolve to the actual observed reason:

```text
missing authority
→ AUTHORITY_UNRESOLVED

scope no longer matches
→ AUTHORITY_SCOPE_VIOLATION

revoked authority
→ AUTHORITY_REVOKED

expired authority
→ AUTHORITY_EXPIRED
```

This prevents timing mechanism and failure cause from being collapsed into
the same taxonomy layer.

---

## 11. Proposed first regression fixtures

### A — Explicit valid authority

```text
grant:
  grant_id = G-A
  subject_id = agent-A
  issuer_id = authority-service
  authorized_actions = [READ]
  authorized_targets = [record-123]
  revoked = false
  expires_at = future
  source_ref = policy-record-A

request:
  subject = agent-A
  action = READ
  target = record-123
```

Expected:

```text
CLEAN
```

---

### B — Missing authority source

```text
grant:
  grant_id = G-B
  subject_id = agent-A
  issuer_id = missing
  source_ref = missing
  authorized_actions = [READ]
  authorized_targets = [record-123]
```

Expected:

```text
AUTHORITY_UNRESOLVED
```

This fixture does not claim that the authority is legally invalid.

It establishes only that the supplied authority source cannot be explicitly
resolved.

---

### C — Scope mismatch

```text
grant:
  authorized_actions = [READ]
  authorized_targets = [record-123]

request:
  action = DELETE
  target = record-123
```

Expected:

```text
AUTHORITY_SCOPE_VIOLATION
```

The same disposition applies when the requested target is outside the
explicit target scope.

---

### D — Revoked authority

```text
grant:
  grant_id = G-D
  revoked = true

request:
  subject = agent-A
  action = READ
  target = record-123
```

Expected:

```text
AUTHORITY_REVOKED
```

A revoked grant must not be converted into CLEAN because it was previously
valid.

---

### E — Expired authority

```text
grant:
  grant_id = G-E
  expires_at = 12:00

validation_time = 12:01
```

Expected:

```text
AUTHORITY_EXPIRED
```

---

### F — Mid-flight authority revocation

```text
T1:
  grant G-F = active
  subject A is authorized for ACTION_X on TARGET_Y

T2:
  Gateway decision = ALLOW

T3:
  grant G-F = revoked

T4:
  execution boundary revalidates G-F
```

Expected at T4:

```text
AUTHORITY_REVOKED
effect =
This fixture specifically tests that a prior Gateway ALLOW is not treated as
a permanent execution capability.

No fixture in v0.1 should be changed merely to obtain a green regression.

---

## 12. Fail-closed semantics

Authority Engine v0.1 must not convert missing or invalid authority
information into CLEAN.

Conceptually:

```text
explicit source
+ matching subject
+ matching action
+ matching target
+ not revoked
+ not expired
→ CLEAN

missing or unresolvable authority source
→ AUTHORITY_UNRESOLVED

action or target outside explicit scope
→ AUTHORITY_SCOPE_VIOLATION

revoked grant
→ AUTHORITY_REVOKED

expired grant
→ AUTHORITY_EXPIRED
```

Unknown authority must not be inferred from:

```text
authentication success
session existence
role name
previous Gateway ALLOW
previous successful execution
```

`AUTHORITY_UNRESOLVED` does not mean:

```text
illegal
fraudulent
unauthorized under law
malicious
false identity
```

It means only that the supplied authority record is insufficient to establish
the Authority Engine v0.1 invariants.

---

## 13. Relationship to existing PHAGE execution controls
Existing PHAGE controls already include:

```text
identity / handshake
session validation
Gateway ALLOW / BLOCK
Tool Adapter execution boundary
pre-effect session revalidation
```

Authority Engine v0.1 does not replace those controls.

It introduces a separate authority-validity dimension:

```text
identity valid
        ↓
session valid
        ↓
authority valid for subject/action/target
        ↓
Gateway decision
        ↓
effect-time authority revalidation
        ↓
effect / no effect
```

A request may therefore fail even when identity and session checks succeed.

Examples:

```text
identity valid
session valid
authority missing
→ AUTHORITY_UNRESOLVED
```

```text
identity valid
session valid
authority revoked
→ AUTHORITY_REVOKED
```

```text
identity valid
session valid
authority valid
scope mismatch
→ AUTHORITY_SCOPE_VIOLATION
```

This design does not merge authority state into session state.

Session revocation and authority revocation remain distinct conditions.

---

## 14. Explicit non-claims

Authority Engine v0.1 does NOT establish:

```text
legal authority
legal admissibility
organizational legitimacy
issuer competence under law
actor identity authenticity
policy correctness
ethical correctness
criminal responsibility
civil responsibility
institutional compliance
production readiness
```

A CLEAN authority result means only that the supplied authority record
satisfies the Authority Engine v0.1 structural invariants for the evaluated
subject, action, target, and validation time.

It does not mean the action is lawful, ethical, desirable, institutionally
approved, or legally admissible.

---

## 15. Design freeze discipline

Before implementation:

```text
DO NOT infer authority from identity.

DO NOT infer authority from session existence.

DO NOT infer authority from role names.

DO NOT treat Gateway ALLOW as permanent authority.

DO NOT collapse session revocation and authority revocation into one state.

DO NOT modify existing Gateway, session, lineage, or Digital Custody semantics
merely to make Authority Engine fixtures pass.

DO NOT change fixture outcomes merely to obtain a green regression.
```

If implementation pressure reveals that these invariants cannot express an
important authority condition, record the pressure first.

Specification expansion must occur explicitly rather than being introduced
silently during regression repair.

---

## 16. v0.1 disposition
```text
AUTHORITY_ENGINE_DESIGN = DRAFT_V0_1

INITIAL_INVARIANTS = 5

AUTHORITY_SOURCE_EXPLICIT = DEFINED
AUTHORITY_SCOPE_MATCH = DEFINED
AUTHORITY_NOT_REVOKED = DEFINED
AUTHORITY_NOT_EXPIRED = DEFINED
NO_STALE_AUTHORITY_AT_EXECUTION = DEFINED

INITIAL_TAXONOMY = PROPOSED

REGRESSION_FIXTURES = PROPOSED_A_THROUGH_F

EXISTING_IDENTITY_SEMANTICS = PRESERVED
EXISTING_SESSION_SEMANTICS = PRESERVED
EXISTING_GATEWAY_SEMANTICS = PRESERVED
EXISTING_LINEAGE_SEMANTICS = PRESERVED
EXISTING_DIGITAL_CUSTODY_SEMANTICS = PRESERVED

IMPLEMENTATION = NOT_STARTED
REGRESSION = NOT_STARTED
GATEWAY_AUTHORITY_INTEGRATION = NOT_STARTED
EFFECT_TIME_AUTHORITY_REVALIDATION = NOT_STARTED

PRODUCTION_AUTHORITY = NOT_ESTABLISHED
LEGAL_AUTHORITY = NOT_ESTABLISHED
PRODUCTION_IDENTITY_TRUST = NOT_ESTABLISHED
INSTITUTIONAL_POLICY_INTEGRATION = NOT_ESTABLISHED
META_GOVERNANCE = NOT_ESTABLISHED
PRODUCTION_READINESS = NOT_ESTABLISHED
```

This document freezes the initial PHAGE Authority Engine design boundary.

Later implementation must validate the frozen authority invariants without
silently broadening identity, session, Gateway, lineage, Digital Custody, or
legal-policy semantics.

Regression evidence and execution-boundary integration must be introduced in
later commits and validation records.
