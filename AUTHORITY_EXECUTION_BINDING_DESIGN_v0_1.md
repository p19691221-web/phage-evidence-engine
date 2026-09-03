# PHAGE Authority-to-Execution Binding Design v0.1

Status: DESIGN DRAFT — NO IMPLEMENTATION CLAIM

This document defines the initial design boundary for binding a PHAGE Gateway
decision to the authority context that must still be valid when a real effect
is attempted.

This document does not claim that Authority Engine has already been integrated
into the existing Gateway → Tool Adapter execution path.

It does not establish production authority, legal authority, production
identity trust, institutional policy integration, meta-governance, or
production readiness.

---

## 1. Design objective

PHAGE currently has separate tested prototype boundaries for:

```text
Identity
→ Session
→ Gateway ALLOW / BLOCK
→ Tool Adapter
→ Effect / No Effect
```

PHAGE also has Authority Engine v0.1 structural validation for:

```text
subject
+
action
+
target
+
explicit authority source
+
revocation state
+
expiration state
```

Authority Engine regression currently establishes:

```text
A  explicit valid authority
   → CLEAN

B  missing authority source
   → AUTHORITY_UNRESOLVED

C  scope mismatch
   → AUTHORITY_SCOPE_VIOLATION

D  revoked authority
   → AUTHORITY_REVOKED

E  expired authority
   → AUTHORITY_EXPIRED

F  decision-time CLEAN
   → authority revoked
   → effect-time revalidation
   → AUTHORITY_REVOKED
   → no effect
```

Fixture F is currently validated inside the Authority Engine regression harness.

It does not yet prove that an existing Gateway decision is cryptographically,
structurally, or operationally bound to the authority state revalidated by the
existing Tool Adapter at the real effect boundary.

The design question for this document is:

> How must a Gateway ALLOW be bound to a specific authority context so that a
> later effect attempt cannot silently change, omit, substitute, or reuse that
> authority context?

---

## 2. Separation of concerns

Authority-to-Execution Binding does not collapse existing PHAGE components.

```text
Identity
≠
Session
≠
Authority
≠
Gateway Decision
≠
Execution
```

Identity answers:

> Who or what is presenting the request?

Session answers:

> Is the current authenticated interaction state still valid?

Authority answers:

> What subject is explicitly permitted to perform which action against which
> target under the supplied authority record?

Gateway answers:

> Should this request cross the tested policy boundary?

Binding answers:

> Is the effect attempt still the same authority-scoped operation that the
> Gateway decision referred to?

Execution answers:

> May the real effect occur now?

Therefore:

```text
authenticated
≠
authorized

authorized at decision time
≠
authorized at effect time

Gateway ALLOW
≠
permanent execution capability

same actor
≠
same authority context

same action name
≠
same bound operation
```

---

## 3. Conceptual binding record

Authority-to-Execution Binding v0.1 introduces the concept of an explicit
binding record.

Conceptually:

```text
ExecutionBinding

decision_id
subject_id
action
target
grant_id
decision_time
```

This structure is conceptual only.

It is not yet a frozen Python API.

The binding record exists to preserve the relationship between:

```text
Gateway decision
        ↓
specific subject
specific action
specific target
specific authority grant
        ↓
effect attempt
```

A previous Gateway ALLOW must not be treated as an unscoped bearer capability.

---

## 4. Initial invariants

Authority-to-Execution Binding v0.1 proposes five initial invariants:

```text
BINDING_CONTEXT_EXPLICIT

BOUND_OPERATION_MATCH

BOUND_GRANT_MATCH

EFFECT_TIME_AUTHORITY_REVALIDATION

NO_EFFECT_ON_BINDING_FAILURE
```

These invariants are design proposals until regression fixtures are frozen and
validated.

No implementation claim is made by defining them.
---

## 5. Invariant 1 — BINDING_CONTEXT_EXPLICIT

A Gateway ALLOW that may later lead to an effect must refer to an explicit
authority-scoped operation.

The minimum conceptual binding context is:

```text
decision_id
subject_id
action
target
grant_id
```

None of these elements may be silently inferred at effect time from:

```text
current identity
current session
role name
previous successful execution
action name alone
target type alone
another valid authority grant
```

Example:

```text
Gateway decision D-001

subject_id = agent-A
action     = READ
target     = record-123
grant_id   = G-001
```

The later effect attempt must not reconstruct missing authority context from
ambient state.

If the required binding context is absent or unresolved:

```text
→ BINDING_UNRESOLVED
→ effect = NOT EXECUTED
```

This status describes insufficient binding information.

It does not claim that the requested action is unlawful, malicious, fraudulent,
or legally unauthorized.

---

## 6. Invariant 2 — BOUND_OPERATION_MATCH

The operation presented at the effect boundary must match the operation bound
to the Gateway decision.

The following dimensions are part of the bound operation:

```text
subject_id
action
target
```

Example:

```text
Gateway ALLOW:

subject_id = agent-A
action     = READ
target     = record-123
grant_id   = G-001
```

The following effect attempt matches:

```text
agent-A
READ
record-123
```

The following do not match:

```text
agent-A
DELETE
record-123
```

```text
agent-A
READ
record-999
```

```text
agent-B
READ
record-123
```

A mismatch must produce:

```text
→ BOUND_OPERATION_MISMATCH
→ effect = NOT EXECUTED
```

A prior Gateway ALLOW for one operation must not be reusable for another
subject, action, or target.

Therefore:

```text
same session
≠
same operation

same actor
≠
same operation

same action name
≠
same operation
```
---

## 7. Invariant 3 — BOUND_GRANT_MATCH

The authority grant presented at the effect boundary must be the grant bound to
the Gateway decision.

Example:

```text
Gateway ALLOW:

decision_id = D-001
subject_id  = agent-A
action      = READ
target      = record-123
grant_id    = G-001
```

At effect time, the following grant matches the binding:

```text
grant_id = G-001
```

The following grant does not match:

```text
grant_id = G-002
```

This remains a mismatch even if G-002 independently authorizes:

```text
subject_id = agent-A
action     = READ
target     = record-123
```

Therefore:

```text
equivalent scope
≠
same bound grant

another valid grant
≠
the grant referenced by the Gateway decision
```

A different grant must not silently replace the grant that was evaluated when
the Gateway decision was created.

If the effect attempt presents a different grant:

```text
→ BOUND_GRANT_MISMATCH
→ effect = NOT EXECUTED
```

This invariant does not claim that the substitute grant is invalid.

It only establishes that the substitute grant is not the authority context
bound to the earlier Gateway decision.
---

## 8. Invariant 4 — EFFECT_TIME_AUTHORITY_REVALIDATION

Matching the binding record is necessary but not sufficient for execution.

The authority grant bound to the Gateway decision must still satisfy the
Authority Engine v0.1 invariants at the actual effect boundary.

Conceptually:

```text
T1
G-001 authorizes:
subject = agent-A
action  = READ
target  = record-123

T2
Gateway evaluates the request
→ Authority Engine = CLEAN
→ Gateway ALLOW

T3
authority state changes

T4
effect attempt reaches the execution boundary
```

At T4, the system must not rely solely on the earlier CLEAN result or Gateway
ALLOW.

It must revalidate the bound authority context:

```text
subject_id
action
target
grant_id
current authority state
current validation time
```

Possible effect-time Authority Engine results remain the existing v0.1
taxonomy:

```text
CLEAN

AUTHORITY_UNRESOLVED

AUTHORITY_SCOPE_VIOLATION

AUTHORITY_REVOKED

AUTHORITY_EXPIRED
```

Authority-to-Execution Binding does not create a new authority status merely
because authority became stale between decision time and effect time.

For example:

```text
T1
G-001 = active

T2
Gateway ALLOW

T3
G-001 = revoked

T4
effect-time authority revalidation

→ AUTHORITY_REVOKED
→ effect = NOT EXECUTED
```

Similarly:

```text
T1
G-001 = active and unexpired

T2
Gateway ALLOW

T3
G-001 expires

T4
effect-time authority revalidation

→ AUTHORITY_EXPIRED
→ effect = NOT EXECUTED
```

If the bound authority record can no longer be resolved:

```text
→ AUTHORITY_UNRESOLVED
→ effect = NOT EXECUTED
```

If the bound authority no longer covers the bound subject, action, or target:

```text
→ AUTHORITY_SCOPE_VIOLATION
→ effect = NOT EXECUTED
```

Therefore:

```text
decision-time CLEAN
≠
effect-time CLEAN

previous Gateway ALLOW
≠
current authority validity
```

This invariant reuses the existing Authority Engine v0.1 result taxonomy.

It does not redefine revocation, expiration, authority scope, or unresolved
authority semantics.

It also does not yet claim that the existing Gateway and Tool Adapter have
been operationally integrated with this revalidation path.
---

## 9. Invariant 5 — NO_EFFECT_ON_BINDING_FAILURE

Any unresolved or violated binding condition must fail closed before the real
effect occurs.

Binding validation and authority validation are separate checks.

Conceptually:

```text
effect attempt
        ↓
binding context present?
        ↓
bound operation matches?
        ↓
bound grant matches?
        ↓
effect-time authority revalidation
        ↓
CLEAN?
        ↓
effect may proceed
```

If any binding check fails:

```text
BINDING_UNRESOLVED
BOUND_OPERATION_MISMATCH
BOUND_GRANT_MISMATCH
```

the result must be:

```text
effect = NOT EXECUTED
```

If the binding checks succeed but effect-time Authority Engine validation
returns:

```text
AUTHORITY_UNRESOLVED
AUTHORITY_SCOPE_VIOLATION
AUTHORITY_REVOKED
AUTHORITY_EXPIRED
```

the result must also be:

```text
effect = NOT EXECUTED
```

Only this combination may permit the effect path to continue:

```text
binding context = resolved
bound operation = match
bound grant = match
effect-time authority = CLEAN
```

Even then, Authority-to-Execution Binding v0.1 does not itself claim that all
other Gateway, session, Tool Adapter, policy, or production execution
conditions have been satisfied.

Therefore:

```text
binding CLEAN
≠
global execution authorization

authority CLEAN
≠
automatic effect

Gateway ALLOW
+
binding match
+
authority CLEAN
≠
proof of production readiness
```

The purpose of this invariant is narrower:

> A binding or authority failure must not be converted into a real effect
> merely because an earlier Gateway decision was ALLOW.

---

## 10. Initial result taxonomy

Authority-to-Execution Binding v0.1 proposes one clean result and three binding-specific failure results:
```text
CLEAN

BINDING_UNRESOLVED

BOUND_OPERATION_MISMATCH

BOUND_GRANT_MISMATCH
```

`CLEAN` in this taxonomy means only that the binding-specific structural checks
passed.

It does not replace or merge the existing Authority Engine taxonomy:

```text
CLEAN

AUTHORITY_UNRESOLVED
AUTHORITY_SCOPE_VIOLATION
AUTHORITY_REVOKED
AUTHORITY_EXPIRED
```

Binding results and Authority Engine results must remain distinguishable.

For example:

```text
binding = CLEAN
authority = AUTHORITY_REVOKED
effect = NOT EXECUTED
```

is valid and must not be collapsed into a generic binding failure.

Similarly:

```text
binding = BOUND_GRANT_MISMATCH
authority = NOT EVALUATED
effect = NOT EXECUTED
```

is also valid.

The binding taxonomy does not claim legal invalidity, malicious substitution,
fraud, identity compromise, or policy illegitimacy.
---

## 11. Proposed regression fixtures

Authority-to-Execution Binding v0.1 proposes five initial regression fixtures.

These fixtures are design proposals only.

They must not be changed merely to obtain a green regression.

### Fixture A — matching binding and valid authority

Given:

```text
decision_id = D-001

bound:
subject_id = agent-A
action     = READ
target     = record-123
grant_id   = G-001
```

At the effect boundary:

```text
subject_id = agent-A
action     = READ
target     = record-123
grant_id   = G-001
```

And Authority Engine effect-time validation returns:

```text
CLEAN
```

Expected binding result:

```text
CLEAN
```

Expected effect disposition:

```text
EFFECT_PATH_ELIGIBLE
```

`EFFECT_PATH_ELIGIBLE` does not mean that a production effect has occurred.

It means only that this binding layer has not produced a reason to block the
effect path.

---

### Fixture B — missing binding context

Given a prior Gateway ALLOW but the effect attempt cannot resolve the complete
binding context:

```text
decision_id = D-001
subject_id  = agent-A
action      = READ
target      = record-123
grant_id    = MISSING
```

Expected binding result:

```text
BINDING_UNRESOLVED
```

Expected effect disposition:

```text
NOT EXECUTED
```

The missing grant identifier must not be reconstructed from another valid
grant, current identity, session state, role name, or previous execution.

---

### Fixture C — bound operation mismatch

Given:

```text
Gateway binding:

subject_id = agent-A
action     = READ
target     = record-123
grant_id   = G-001
```

But the effect attempt presents:

```text
subject_id = agent-A
action     = DELETE
target     = record-123
grant_id   = G-001
```

Expected binding result:

```text
BOUND_OPERATION_MISMATCH
```

Expected effect disposition:

```text
NOT EXECUTED
```

A previous ALLOW for READ must not authorize DELETE.

---

### Fixture D — substitute grant with equivalent scope

Given:

```text
Gateway binding:

subject_id = agent-A
action     = READ
target     = record-123
grant_id   = G-001
```

At the effect boundary, G-002 independently authorizes:

```text
subject_id = agent-A
action     = READ
target     = record-123
```

But the effect attempt presents:

```text
grant_id = G-002
```

Expected binding result:

```text
BOUND_GRANT_MISMATCH
```

Expected effect disposition:

```text
NOT EXECUTED
```

The fixture must remain a mismatch even though G-002 has equivalent scope.

This fixture does not claim that G-002 is invalid.

---

### Fixture E — bound grant revoked after Gateway ALLOW

Given:

```text
T1
G-001 = active

T2
Gateway evaluates the bound operation
→ Authority Engine = CLEAN
→ Gateway ALLOW

T3
G-001 = revoked

T4
the same bound operation reaches the effect boundary
```

Binding checks at T4 remain:

```text
binding context = resolved
bound operation = match
bound grant = match
```

Expected binding result:

```text
CLEAN
```

Effect-time Authority Engine result:

```text
AUTHORITY_REVOKED
```

Expected effect disposition:

```text
NOT EXECUTED
```

This fixture demonstrates that:

```text
binding CLEAN
≠
authority CLEAN

previous Gateway ALLOW
≠
current execution authority
```

Fixture E must not be converted into `BOUND_GRANT_MISMATCH` merely because the
bound grant has been revoked.

Revocation remains an Authority Engine result.
---

## 12. Design freeze discipline

Before implementation:

```text
DO NOT treat Gateway ALLOW as an unscoped execution capability.

DO NOT infer missing binding context from identity, session, role, ambient
state, previous execution, or another valid grant.

DO NOT allow subject, action, or target substitution after the Gateway
decision.

DO NOT silently substitute another authority grant, even when that grant has
equivalent scope.

DO NOT collapse binding failures into Authority Engine failures.

DO NOT collapse Authority Engine failures into binding failures.

DO NOT introduce STALE_AUTHORITY as a new result merely because authority
changes between decision time and effect time.

DO NOT treat EFFECT_PATH_ELIGIBLE as proof that an effect occurred.

DO NOT modify existing identity, session, Gateway, Authority Engine, lineage,
Digital Custody, or Tool Adapter semantics merely to make later fixtures pass.

DO NOT change frozen fixture outcomes merely to obtain a green regression.
```

If implementation pressure reveals that these invariants cannot express an
important binding condition, record the pressure first.

Specification expansion must occur explicitly rather than being introduced
silently during regression repair.

---

## 13. v0.1 disposition

```text
AUTHORITY_EXECUTION_BINDING_DESIGN = DRAFT_V0_1

INITIAL_INVARIANTS = 5

BINDING_CONTEXT_EXPLICIT = DEFINED
BOUND_OPERATION_MATCH = DEFINED
BOUND_GRANT_MATCH = DEFINED
EFFECT_TIME_AUTHORITY_REVALIDATION = DEFINED
NO_EFFECT_ON_BINDING_FAILURE = DEFINED

BINDING_RESULT_TAXONOMY = PROPOSED

CLEAN = DEFINED
BINDING_UNRESOLVED = DEFINED
BOUND_OPERATION_MISMATCH = DEFINED
BOUND_GRANT_MISMATCH = DEFINED

REGRESSION_FIXTURES = PROPOSED_A_THROUGH_E

EXISTING_IDENTITY_SEMANTICS = PRESERVED
EXISTING_SESSION_SEMANTICS = PRESERVED
EXISTING_GATEWAY_SEMANTICS = PRESERVED
EXISTING_AUTHORITY_ENGINE_SEMANTICS = PRESERVED
EXISTING_LINEAGE_SEMANTICS = PRESERVED
EXISTING_DIGITAL_CUSTODY_SEMANTICS = PRESERVED
EXISTING_TOOL_ADAPTER_SEMANTICS = PRESERVED

IMPLEMENTATION = NOT_STARTED
REGRESSION = NOT_STARTED
GATEWAY_BINDING_INTEGRATION = NOT_STARTED
TOOL_ADAPTER_BINDING_INTEGRATION = NOT_STARTED
REAL_EFFECT_BOUNDARY_VALIDATION = NOT_STARTED

PRODUCTION_AUTHORITY = NOT_ESTABLISHED
LEGAL_AUTHORITY = NOT_ESTABLISHED
PRODUCTION_IDENTITY_TRUST = NOT_ESTABLISHED
INSTITUTIONAL_POLICY_INTEGRATION = NOT_ESTABLISHED
META_GOVERNANCE = NOT_ESTABLISHED
PRODUCTION_READINESS = NOT_ESTABLISHED
```

This document freezes the initial PHAGE Authority-to-Execution Binding design
boundary.

Later regression and implementation must preserve the distinction between:

```text
Gateway decision
Binding validation
Authority validation
Execution
```

and must not convert an earlier Gateway ALLOW into a permanent or transferable
execution capability.

Regression evidence, Gateway integration, Tool Adapter integration, and real
effect-boundary validation must be introduced in later commits.
