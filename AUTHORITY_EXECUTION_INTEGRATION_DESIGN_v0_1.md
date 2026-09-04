# PHAGE Authority-to-Execution Integration Design v0.1

Status: DESIGN DRAFT — NO IMPLEMENTATION CLAIM

This document defines the initial integration boundary between the existing
PHAGE Gateway, Authority-to-Execution Binding, Authority Engine, and Tool
Adapter prototype components.

This document does not claim that this integration is already implemented or
validated.

It does not establish production authority, legal authority, production
identity trust, institutional policy integration, meta-governance, or
production readiness.

---

## 1. Existing validated boundaries

PHAGE currently has separate regression evidence for:

```text
Identity / Session
        ↓
Gateway ALLOW / BLOCK
        ↓
Tool Adapter
        ↓
Effect / No Effect
```

PHAGE also has Authority Engine v0.1 regression evidence for:

```text
authority source
authority scope
revocation
expiration
effect-time revalidation behavior
```

And Authority-to-Execution Binding v0.1 regression evidence for:

```text
binding context
bound operation
bound grant
binding failure → no effect eligibility
binding CLEAN ≠ authority CLEAN
```

These validated components remain separate.

Their individual regression success does not establish that they are already
connected into one tested execution path.

---

## 2. Integration question

The integration question is:

> Can a Gateway ALLOW be carried through an explicit ExecutionBinding,
> revalidated against the bound AuthorityGrant at effect time, and presented
> to the Tool Adapter such that any binding or authority failure prevents the
> real effect path?

Conceptually:

```text
Request
   ↓
Session validation
   ↓
Authority validation
   ↓
Gateway decision
   ↓
ExecutionBinding
   ↓
Effect-time binding validation
   ↓
Effect-time authority revalidation
   ↓
Tool Adapter
   ↓
Effect / No Effect
```

This document concerns the connections between those boundaries.

It does not redefine the semantics inside the existing Session, Gateway,
Authority Engine, Binding, or Tool Adapter components.

---

## 3. Separation rule

Integration must preserve:

```text
Gateway decision
≠
Binding validation
≠
Authority validation
≠
Execution
```

Therefore:

```text
Gateway ALLOW
≠
effect permission by itself

binding CLEAN
≠
authority CLEAN

authority CLEAN
≠
effect occurred

earlier validation
≠
effect-time validation
```

Integration may connect these results.

Integration must not collapse them.
---

## 4. Initial integration invariants

Authority-to-Execution Integration v0.1 proposes five initial integration
invariants:

```text
ALLOW_REQUIRES_EXPLICIT_BINDING

BOUND_CONTEXT_PRESERVED_TO_EFFECT

EFFECT_TIME_AUTHORITY_REQUIRED

TOOL_ADAPTER_REQUIRES_CLEAN_UPSTREAM_CHAIN

NO_EFFECT_ON_INTEGRATION_FAILURE
```

These invariants describe connections between existing PHAGE boundaries.

They do not redefine the internal result taxonomy of Gateway,
Authority-to-Execution Binding, Authority Engine, or Tool Adapter.

---

## 5. Invariant 1 — ALLOW_REQUIRES_EXPLICIT_BINDING

A Gateway ALLOW that may proceed toward an effect must be associated with an
explicit ExecutionBinding.

Conceptually:

```text
Gateway decision = ALLOW
        ↓
ExecutionBinding
```

The binding must identify the operation already frozen by
Authority-to-Execution Binding v0.1:

```text
decision_id
subject_id
action
target
grant_id
decision_time
```

A Gateway ALLOW must not enter the effect path with no resolvable binding
context.

Therefore:

```text
Gateway ALLOW
+
missing binding
→ effect = NOT EXECUTED
```

The integration layer must not reconstruct a missing binding from:

```text
identity
session
role
ambient request state
previous successful execution
another authority grant
```

Missing binding remains a Binding-layer condition:

```text
BINDING_UNRESOLVED
```

The integration layer does not create a second name for the same failure.

---

## 6. Invariant 2 — BOUND_CONTEXT_PRESERVED_TO_EFFECT

The authority-scoped operation bound after the Gateway decision must remain the
operation presented at the effect boundary.

The following relationship must remain stable:

```text
decision_id
subject_id
action
target
grant_id
```

Integration must not permit silent substitution of:

```text
subject
action
target
grant
```

between Gateway ALLOW and the effect attempt.

If the operation changes:

```text
→ BOUND_OPERATION_MISMATCH
→ effect = NOT EXECUTED
```

If the grant changes:

```text
→ BOUND_GRANT_MISMATCH
→ effect = NOT EXECUTED
```

These remain Binding-layer results.

Integration does not reinterpret them as Authority Engine failures.

Therefore:

```text
same Gateway decision
≠
permission to mutate the bound operation

equivalent authority scope
≠
permission to substitute the bound grant
```

---

## 7. Invariant 3 — EFFECT_TIME_AUTHORITY_REQUIRED

A binding match is necessary but not sufficient for the effect path.

Immediately before the Tool Adapter may produce an effect, the bound authority
context must be revalidated using the existing Authority Engine v0.1
semantics.

Conceptually:

```text
binding = CLEAN
        ↓
effect-time Authority Engine validation
        ↓
CLEAN ?
```

The integration path must preserve the existing Authority Engine outcomes:

```text
CLEAN
AUTHORITY_UNRESOLVED
AUTHORITY_SCOPE_VIOLATION
AUTHORITY_REVOKED
AUTHORITY_EXPIRED
```

If effect-time authority is not CLEAN:

```text
effect = NOT EXECUTED
```

For example:

```text
T1
authority = CLEAN

T2
Gateway ALLOW
ExecutionBinding created

T3
grant revoked

T4
binding = CLEAN
effect-time authority = AUTHORITY_REVOKED

→ effect = NOT EXECUTED
```

The integration layer must not convert this into:

```text
BOUND_GRANT_MISMATCH
```

because the bound grant is still the same grant.

Its authority state changed.

Revocation remains an Authority Engine result.
---

## 8. Invariant 4 — TOOL_ADAPTER_REQUIRES_CLEAN_UPSTREAM_CHAIN

The Tool Adapter must not be reached as an effect-capable boundary merely
because the Gateway previously returned ALLOW.

Before an effect-capable Tool Adapter invocation, the integration path must
have all of the following:

```text
Gateway decision = ALLOW

binding validation = CLEAN

effect-time authority validation = CLEAN
```

Conceptually:

```text
Gateway ALLOW
        ↓
ExecutionBinding present
        ↓
binding = CLEAN
        ↓
effect-time authority = CLEAN
        ↓
Tool Adapter may receive an effect-capable invocation
```

If binding validation returns:

```text
BINDING_UNRESOLVED

BOUND_OPERATION_MISMATCH

BOUND_GRANT_MISMATCH
```

the Tool Adapter must not receive an effect-capable invocation.

If effect-time Authority Engine validation returns:

```text
AUTHORITY_UNRESOLVED

AUTHORITY_SCOPE_VIOLATION

AUTHORITY_REVOKED

AUTHORITY_EXPIRED
```

the Tool Adapter must not receive an effect-capable invocation.

Therefore:

```text
Gateway ALLOW alone
≠
Tool Adapter effect capability

binding CLEAN alone
≠
Tool Adapter effect capability

authority CLEAN without matching binding
≠
Tool Adapter effect capability
```

This invariant does not redefine Tool Adapter internals.

It defines only the upstream conditions that must be satisfied before the
integration path may present an effect-capable operation to the Tool Adapter.

It does not yet claim that the existing Tool Adapter has been operationally
wired to this integration path.

---

## 9. Invariant 5 — NO_EFFECT_ON_INTEGRATION_FAILURE

Any failure in the integrated upstream chain must fail closed before a real
effect is produced.

Conceptually:

```text
Gateway decision
        ↓
ExecutionBinding
        ↓
binding validation
        ↓
effect-time authority validation
        ↓
Tool Adapter
        ↓
Effect
```

The effect path may continue only when:

```text
Gateway decision = ALLOW

AND

binding validation = CLEAN

AND

effect-time authority validation = CLEAN
```

If Gateway returns BLOCK:

```text
→ effect = NOT EXECUTED
```

If binding validation is not CLEAN:

```text
→ effect = NOT EXECUTED
```

If effect-time authority validation is not CLEAN:

```text
→ effect = NOT EXECUTED
```

An earlier successful stage must not override a later failure.

Therefore:

```text
Gateway ALLOW
+
binding failure
→ NOT EXECUTED
```

```text
Gateway ALLOW
+
binding CLEAN
+
authority failure
→ NOT EXECUTED
```

Only:

```text
Gateway ALLOW
+
binding CLEAN
+
effect-time authority CLEAN
```

may make the operation eligible to reach an effect-capable Tool Adapter path.

Eligibility to reach that path does not itself prove that a production effect
occurred.

The integration layer must preserve the observed reason for blocking.

For example:

```text
missing binding
→ BINDING_UNRESOLVED
```

```text
changed operation
→ BOUND_OPERATION_MISMATCH
```

```text
changed grant
→ BOUND_GRANT_MISMATCH
```

```text
revoked grant
→ AUTHORITY_REVOKED
```

```text
expired grant
→ AUTHORITY_EXPIRED
```

Authority-to-Execution Integration v0.1 does not introduce a generic
`INTEGRATION_FAILURE` result that erases those existing reasons.

The integration concern is the fail-closed connection between the existing
boundaries, not a replacement taxonomy.
---

## 10. Proposed integration regression fixtures

Authority-to-Execution Integration v0.1 proposes five initial integration
regression fixtures.

These fixtures test the connections between existing PHAGE boundaries.

They do not redefine the existing Gateway, Binding, Authority Engine, or Tool
Adapter semantics.

They must not be changed merely to obtain a green regression.

### Fixture A — clean integrated path

Given:

```text
Gateway decision = ALLOW

ExecutionBinding = present

binding validation = CLEAN

effect-time authority validation = CLEAN
```

Expected integration behavior:

```text
effect-capable Tool Adapter invocation = PERMITTED
```

Expected final disposition in the integration harness:

```text
EFFECT_PATH_ELIGIBLE
```

This fixture does not by itself claim production effect execution.

It establishes only that the complete tested upstream chain produced no reason
to block the effect-capable Tool Adapter path.

---

### Fixture B — Gateway BLOCK stops the chain

Given:

```text
Gateway decision = BLOCK
```

Even if other supplied state would independently appear valid:

```text
binding context = present

authority state = CLEAN
```

Expected integration behavior:

```text
effect-capable Tool Adapter invocation = NOT PERMITTED
```

Expected final disposition:

```text
NOT EXECUTED
```

A later clean binding or clean authority result must not override Gateway
BLOCK.

---

### Fixture C — Gateway ALLOW with missing binding

Given:

```text
Gateway decision = ALLOW

ExecutionBinding = unresolved
```

Expected Binding result:

```text
BINDING_UNRESOLVED
```

Expected integration behavior:

```text
effect-capable Tool Adapter invocation = NOT PERMITTED
```

Expected final disposition:

```text
NOT EXECUTED
```

The integration layer must preserve `BINDING_UNRESOLVED`.

It must not manufacture a replacement binding or convert the result into a
generic integration failure.

---

### Fixture D — Gateway ALLOW with changed bound operation

Given:

```text
Gateway decision = ALLOW

original binding:
subject = agent-A
action  = READ
target  = record-123
grant   = G-001
```

But the effect attempt presents:

```text
subject = agent-A
action  = DELETE
target  = record-123
grant   = G-001
```

Expected Binding result:

```text
BOUND_OPERATION_MISMATCH
```

Expected integration behavior:

```text
effect-capable Tool Adapter invocation = NOT PERMITTED
```

Expected final disposition:

```text
NOT EXECUTED
```

The earlier Gateway ALLOW must not make the changed operation executable.

---

### Fixture E — authority revoked after clean Gateway and binding stages

Given:

```text
T1
authority = CLEAN

T2
Gateway decision = ALLOW
ExecutionBinding created

T3
bound grant revoked

T4
binding validation = CLEAN
effect-time authority revalidation = AUTHORITY_REVOKED
```

Expected Binding result:

```text
CLEAN
```

Expected Authority Engine result:

```text
AUTHORITY_REVOKED
```

Expected integration behavior:

```text
effect-capable Tool Adapter invocation = NOT PERMITTED
```

Expected final disposition:

```text
NOT EXECUTED
```

Fixture E must preserve:

```text
binding CLEAN
≠
authority CLEAN
```

and must not convert revocation into:

```text
BOUND_GRANT_MISMATCH
```

Revocation remains an Authority Engine result.
---

## 11. Design freeze discipline

Before implementation:

```text
DO NOT treat Gateway ALLOW as sufficient authority to execute.

DO NOT permit an effect-capable Tool Adapter invocation without an explicit
ExecutionBinding.

DO NOT reconstruct missing binding context from identity, session, role,
ambient request state, prior execution, or another authority grant.

DO NOT permit subject, action, target, or grant substitution between Gateway
decision time and the effect boundary.

DO NOT treat binding CLEAN as authority CLEAN.

DO NOT treat authority CLEAN as proof that an effect occurred.

DO NOT allow an earlier successful stage to override a later failure.

DO NOT convert Binding-layer failures into Authority Engine failures.

DO NOT convert Authority Engine failures into Binding-layer failures.

DO NOT introduce a generic INTEGRATION_FAILURE result that erases the existing
Gateway, Binding, Authority Engine, or Tool Adapter reason for blocking.

DO NOT treat EFFECT_PATH_ELIGIBLE as proof of production effect execution.

DO NOT modify existing Session, Gateway, Authority Engine,
Authority-to-Execution Binding, Tool Adapter, lineage, or Digital Custody
semantics merely to make later integration fixtures pass.

DO NOT change frozen fixture outcomes merely to obtain a green regression.
```

If implementation pressure reveals that these invariants cannot express an
important integration condition, record the pressure first.

Specification expansion must occur explicitly rather than being introduced
silently during regression repair.

---

## 12. v0.1 disposition

```text
AUTHORITY_EXECUTION_INTEGRATION_DESIGN = DRAFT_V0_1

INITIAL_INTEGRATION_INVARIANTS = 5

ALLOW_REQUIRES_EXPLICIT_BINDING = DEFINED
BOUND_CONTEXT_PRESERVED_TO_EFFECT = DEFINED
EFFECT_TIME_AUTHORITY_REQUIRED = DEFINED
TOOL_ADAPTER_REQUIRES_CLEAN_UPSTREAM_CHAIN = DEFINED
NO_EFFECT_ON_INTEGRATION_FAILURE = DEFINED

NEW_INTEGRATION_FAILURE_TAXONOMY = NOT_PROPOSED

REGRESSION_FIXTURES = PROPOSED_A_THROUGH_E

EXISTING_SESSION_SEMANTICS = PRESERVED
EXISTING_GATEWAY_SEMANTICS = PRESERVED
EXISTING_BINDING_SEMANTICS = PRESERVED
EXISTING_AUTHORITY_ENGINE_SEMANTICS = PRESERVED
EXISTING_TOOL_ADAPTER_SEMANTICS = PRESERVED
EXISTING_LINEAGE_SEMANTICS = PRESERVED
EXISTING_DIGITAL_CUSTODY_SEMANTICS = PRESERVED

IMPLEMENTATION = NOT_STARTED
REGRESSION = NOT_STARTED
GATEWAY_BINDING_INTEGRATION = NOT_STARTED
EFFECT_TIME_AUTHORITY_INTEGRATION = NOT_STARTED
TOOL_ADAPTER_INTEGRATION = NOT_STARTED
REAL_EFFECT_BOUNDARY_VALIDATION = NOT_STARTED

PRODUCTION_EFFECT_EXECUTION = NOT_ESTABLISHED
PRODUCTION_AUTHORITY = NOT_ESTABLISHED
LEGAL_AUTHORITY = NOT_ESTABLISHED
PRODUCTION_IDENTITY_TRUST = NOT_ESTABLISHED
INSTITUTIONAL_POLICY_INTEGRATION = NOT_ESTABLISHED
META_GOVERNANCE = NOT_ESTABLISHED
PRODUCTION_READINESS = NOT_ESTABLISHED
```

This document freezes the initial PHAGE Authority-to-Execution Integration
design boundary.

Later regression and implementation must preserve the distinction between:

```text
Gateway decision
ExecutionBinding
Binding validation
Authority validation
Tool Adapter eligibility
Execution
```

A successful upstream stage must not erase or override a later failure.

Gateway ALLOW must not be converted into a permanent, transferable, or
standalone execution capability.

Regression evidence, operational integration, and real effect-boundary
validation must be introduced in later commits.
