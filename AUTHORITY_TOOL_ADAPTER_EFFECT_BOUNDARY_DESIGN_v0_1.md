# PHAGE Authority-to-Tool-Adapter Effect Boundary Design v0.1

Status: DESIGN DRAFT — NO IMPLEMENTATION CLAIM

This document defines the initial design boundary for carrying an eligible
PHAGE Authority-to-Execution Integration result into an actual Tool Adapter
invocation and observing whether an effect occurs.

This document does not claim that the existing Tool Adapter has already been
operationally connected to the Authority-to-Execution Integration path.

It does not establish production execution, production authority, legal
authority, production identity trust, institutional policy integration,
meta-governance, or production readiness.

---

## 1. Existing validated boundary

PHAGE currently has regression evidence for the following integration path:

```text
Gateway decision
        ↓
Binding validation
        ↓
effect-time Authority validation
        ↓
tool_adapter_permitted
```

The frozen Authority-to-Execution Integration regression establishes:

```text
A
Gateway ALLOW
+ binding CLEAN
+ effect-time authority CLEAN
→ tool_adapter_permitted = True
→ EFFECT_PATH_ELIGIBLE

B
Gateway BLOCK
→ tool_adapter_permitted = False
→ NOT_EXECUTED

C
missing binding
→ BINDING_UNRESOLVED
→ tool_adapter_permitted = False
→ NOT_EXECUTED

D
changed bound operation
→ BOUND_OPERATION_MISMATCH
→ tool_adapter_permitted = False
→ NOT_EXECUTED

E
binding CLEAN
+ effect-time AUTHORITY_REVOKED
→ tool_adapter_permitted = False
→ NOT_EXECUTED
```

These results establish eligibility gating inside the integration harness.

They do not establish that an existing Tool Adapter was actually invoked.

Therefore:

```text
tool_adapter_permitted = True
≠
Tool Adapter invoked
```

---

## 2. Effect-boundary question

The design question for this document is:

> When the integration layer determines that the Tool Adapter path is eligible,
> can that eligibility be carried into an actual adapter invocation without
> collapsing invocation, effect attempt, and observed effect into one state?

Conceptually:

```text
Gateway
   ↓
Binding
   ↓
effect-time Authority
   ↓
EFFECT_PATH_ELIGIBLE
   ↓
Tool Adapter invocation
   ↓
effect attempt
   ↓
effect observed / no effect
```

This document concerns the final transition from eligibility into an observed
effect boundary.

It does not redefine Gateway, Binding, Authority Engine, or Integration
semantics.

---

## 3. Separation of concerns

The effect boundary must preserve:

```text
tool_adapter_permitted
≠
Tool Adapter invoked
≠
effect attempted
≠
effect occurred
```

Specifically:

```text
EFFECT_PATH_ELIGIBLE
≠
effect occurred
```

and:

```text
Tool Adapter invoked
≠
effect succeeded
```

and:

```text
effect attempted
≠
effect occurred
```

A failure or no-op at a later stage must not be rewritten as a successful
effect merely because an earlier stage was eligible.

Similarly, a successful observed effect must not erase the authority,
binding, or Gateway context that permitted the invocation.

The purpose of this layer is to make the final effect boundary observable,
not to broaden the authority granted upstream.
---

## 4. Initial effect-boundary invariants

Authority-to-Tool-Adapter Effect Boundary v0.1 proposes five initial
invariants:

```text
ELIGIBILITY_REQUIRED_FOR_INVOCATION

BOUND_OPERATION_PRESERVED_TO_ADAPTER

INVOCATION_OBSERVED_EXPLICITLY

EFFECT_OBSERVED_EXPLICITLY

NO_EFFECT_ON_INELIGIBLE_OR_FAILED_PATH
```

These invariants describe the transition from an eligible integration result
to an observable Tool Adapter effect boundary.

They do not redefine the internal semantics of Gateway, Binding, Authority
Engine, Authority-to-Execution Integration, or the existing Tool Adapter.

They also do not introduce a claim that a production effect path exists.

---

## 5. Invariant 1 — ELIGIBILITY_REQUIRED_FOR_INVOCATION

An effect-capable Tool Adapter invocation must not occur unless the upstream
Authority-to-Execution Integration result explicitly permits the adapter path.

Required upstream condition:

```text
tool_adapter_permitted = True

AND

effect_disposition = EFFECT_PATH_ELIGIBLE
```

If the integration result is not eligible:

```text
tool_adapter_permitted = False
```

or:

```text
effect_disposition = NOT_EXECUTED
```

then:

```text
Tool Adapter invoked = False
effect attempted = False
effect occurred = False
```

A Tool Adapter invocation must not be reconstructed from:

```text
previous Gateway ALLOW
previous binding CLEAN
previous authority CLEAN
previous successful execution
ambient request state
```

Therefore:

```text
earlier upstream success
≠
permission to bypass current integration eligibility
```

This invariant preserves the existing fail-closed integration boundary.

---

## 6. Invariant 2 — BOUND_OPERATION_PRESERVED_TO_ADAPTER

The operation presented to the Tool Adapter must be the same operation that
survived Gateway, Binding, and effect-time Authority validation.

The invocation context must preserve at least:

```text
subject_id
action
target
grant_id
```

and must remain associated with the eligible integration result that permitted
the adapter path.

The Tool Adapter boundary must not silently substitute:

```text
subject
action
target
grant
```

after upstream validation has completed.

Conceptually:

```text
eligible integration result
        ↓
bound subject
bound action
bound target
bound grant
        ↓
Tool Adapter invocation
```

must not become:

```text
eligible integration result
        ↓
different subject
different action
different target
different grant
        ↓
Tool Adapter invocation
```

If the operation presented to the adapter no longer matches the eligible bound
operation:

```text
Tool Adapter invoked = False
effect attempted = False
effect occurred = False
```

This design does not yet assign a new failure taxonomy to that condition.

Existing Binding semantics must be reused where they fully express the
mismatch.

Specification expansion must occur explicitly if later regression pressure
shows that the existing Binding result cannot represent the effect-boundary
condition.

---

## 7. Invariant 3 — INVOCATION_OBSERVED_EXPLICITLY

The effect-boundary harness must distinguish permission to invoke from actual
invocation.

Therefore:

```text
tool_adapter_permitted = True
```

does not automatically produce:

```text
tool_adapter_invoked = True
```

The harness must explicitly observe whether the Tool Adapter invocation
occurred.

Conceptually:

```text
EFFECT_PATH_ELIGIBLE
        ↓
invocation decision
        ↓
Tool Adapter invoked?
```

Possible observations include:

```text
tool_adapter_invoked = False

tool_adapter_invoked = True
```

If invocation does not occur:

```text
effect_attempted = False
effect_occurred = False
```

This state is a NO EFFECT observation.

It does not imply:

```text
authority failure
binding failure
Gateway BLOCK
malicious behavior
production failure
```

It establishes only that no adapter invocation was observed at this boundary.

The reason for non-invocation must remain distinguishable from the observation
that no invocation occurred.
---

## 8. Invariant 4 — EFFECT_OBSERVED_EXPLICITLY

An observed Tool Adapter invocation must not automatically be treated as an
observed effect.

The effect-boundary harness must distinguish:

```text
tool_adapter_invoked
effect_attempted
effect_occurred
```

A valid observation may be:

```text
tool_adapter_invoked = True
effect_attempted = True
effect_occurred = True
```

This means that the harness observed an invocation, an effect attempt, and the
expected effect state.

But the following is also valid:

```text
tool_adapter_invoked = True
effect_attempted = True
effect_occurred = False
```

This is a NO EFFECT observation after an attempted operation.

It must not be rewritten as:

```text
effect_occurred = True
```

merely because the Tool Adapter was invoked.

Similarly:

```text
tool_adapter_invoked = True
effect_attempted = False
effect_occurred = False
```

must remain distinguishable from an attempted effect that produced no observed
effect.

Therefore:

```text
invoked
≠
attempted

attempted
≠
occurred
```

The harness must observe the effect using an explicit state boundary rather
than inferring success from a return path, invocation event, or eligibility
decision alone.

Conceptually:

```text
before_state
        ↓
Tool Adapter invocation
        ↓
effect attempt
        ↓
after_state
        ↓
compare
        ↓
effect_occurred = True / False
```

The observation mechanism may be minimal in v0.1, but it must be explicit.

`effect_occurred = True` means only that the frozen test harness observed the
expected state transition for that fixture.

It does not establish:

```text
production execution
legal validity
business correctness
institutional approval
real-world external effect
```

unless those properties are separately validated.

---

## 9. Invariant 5 — NO_EFFECT_ON_INELIGIBLE_OR_FAILED_PATH

An ineligible or failed upstream path must not produce an observed effect.

If the current integration result is not eligible:

```text
tool_adapter_permitted = False
```

or:

```text
effect_disposition = NOT_EXECUTED
```

then the required effect-boundary observation is:

```text
tool_adapter_invoked = False
effect_attempted = False
effect_occurred = False
```

An earlier Gateway ALLOW, Binding CLEAN, Authority CLEAN, or previous
successful Tool Adapter invocation must not override the current failed or
ineligible state.

Therefore:

```text
previous success
+
current ineligibility
≠
permission to invoke
```

and:

```text
current ineligibility
→
NO EFFECT
```

If the path is eligible and the Tool Adapter is invoked, but the attempted
operation produces no observed state transition:

```text
tool_adapter_invoked = True
effect_attempted = True
effect_occurred = False
```

this must remain distinguishable from an upstream-blocked path:

```text
tool_adapter_invoked = False
effect_attempted = False
effect_occurred = False
```

Both are NO EFFECT observations.

They are not the same causal state.

The effect-boundary layer must preserve whether no effect resulted from:

```text
upstream ineligibility

no invocation

invocation without effect attempt

effect attempt without observed effect
```

This design does not yet introduce a new generic effect-boundary failure
taxonomy.

Existing Gateway, Binding, Authority, and Integration results must remain
preserved where they explain the upstream cause.

A NO EFFECT observation alone must not be used to infer:

```text
Gateway BLOCK
binding failure
authority failure
adapter defect
malicious behavior
production failure
```

The observation establishes only what happened at the frozen effect boundary.

Cause and observation must remain distinguishable.
---

## 10. Proposed effect-boundary regression fixtures

Authority-to-Tool-Adapter Effect Boundary v0.1 proposes six initial
regression fixtures.

These fixtures test the transition from integration eligibility into an
observable Tool Adapter effect boundary.

They do not establish production execution.

They must not be changed merely to obtain a green regression.

### Fixture A — eligible invocation produces observed effect

Given:

```text
tool_adapter_permitted = True
effect_disposition = EFFECT_PATH_ELIGIBLE
```

The adapter receives the same bound operation:

```text
subject_id = agent-A
action     = READ
target     = record-123
grant_id   = G-001
```

Before invocation:

```text
effect_state = 0
```

The Tool Adapter is invoked and attempts the frozen synthetic effect.

After invocation:

```text
effect_state = 1
```

Expected observations:

```text
tool_adapter_invoked = True
effect_attempted = True
effect_occurred = True
```

`effect_occurred = True` means only that the frozen test harness observed the
expected synthetic state transition.

It does not establish a production or external real-world effect.

---

### Fixture B — ineligible upstream path never invokes adapter

Given:

```text
tool_adapter_permitted = False
effect_disposition = NOT_EXECUTED
```

Expected observations:

```text
tool_adapter_invoked = False
effect_attempted = False
effect_occurred = False
```

Expected state:

```text
before_state = after_state
```

An invocation request must not override current upstream ineligibility.

---

### Fixture C — bound operation changes before adapter invocation

Given an eligible upstream operation:

```text
subject_id = agent-A
action     = READ
target     = record-123
grant_id   = G-001
```

But the operation presented at the Tool Adapter boundary is:

```text
subject_id = agent-A
action     = DELETE
target     = record-123
grant_id   = G-001
```

Expected preserved mismatch:

```text
BOUND_OPERATION_MISMATCH
```

Expected observations:

```text
tool_adapter_invoked = False
effect_attempted = False
effect_occurred = False
```

Expected state:

```text
before_state = after_state
```

The effect-boundary layer must reuse existing Binding semantics where they
fully express the mismatch.

---

### Fixture D — eligible path but adapter invocation does not occur

Given:

```text
tool_adapter_permitted = True
effect_disposition = EFFECT_PATH_ELIGIBLE
```

But no Tool Adapter invocation is observed.

Expected observations:

```text
tool_adapter_invoked = False
effect_attempted = False
effect_occurred = False
```

Expected state:

```text
before_state = after_state
```

This is a NO EFFECT observation.

It must not be rewritten as an authority, binding, Gateway, or production
failure.

---

### Fixture E — adapter invoked but no effect attempt occurs

Given:

```text
tool_adapter_permitted = True
effect_disposition = EFFECT_PATH_ELIGIBLE
```

The Tool Adapter invocation is observed, but the adapter does not begin the
synthetic effect operation.

Expected observations:

```text
tool_adapter_invoked = True
effect_attempted = False
effect_occurred = False
```

Expected state:

```text
before_state = after_state
```

This must remain distinguishable from Fixture D.

```text
invoked but not attempted
≠
not invoked
```

No generic failure taxonomy is introduced by this observation.

---

### Fixture F — effect attempted but no effect is observed

Given:

```text
tool_adapter_permitted = True
effect_disposition = EFFECT_PATH_ELIGIBLE
```

The Tool Adapter is invoked and begins the synthetic effect operation, but the
expected state transition does not occur.

Expected observations:

```text
tool_adapter_invoked = True
effect_attempted = True
effect_occurred = False
```

Expected state:

```text
before_state = after_state
```

This must remain distinguishable from:

```text
upstream blocked
```

and:

```text
invoked but not attempted
```

Fixture F establishes only:

```text
effect attempt observed
+
expected effect not observed
```

It does not by itself establish:

```text
adapter defect
malicious behavior
authority failure
binding failure
production failure
```

Cause and effect observation remain separate.
---

## 11. Design freeze discipline

Before implementation:

```text
DO NOT treat EFFECT_PATH_ELIGIBLE as proof that the Tool Adapter was invoked.

DO NOT treat tool_adapter_permitted = True as proof that invocation occurred.

DO NOT treat Tool Adapter invocation as proof that an effect was attempted.

DO NOT treat an effect attempt as proof that an effect occurred.

DO NOT infer effect success from a return path, invocation event, or upstream
eligibility result alone.

DO NOT invoke the Tool Adapter when the current integration result is
ineligible.

DO NOT allow a previous Gateway ALLOW, Binding CLEAN, Authority CLEAN, or
successful execution to override current ineligibility.

DO NOT permit subject, action, target, or grant substitution at the Tool
Adapter boundary.

DO NOT convert a bound-operation mismatch into a new effect-boundary taxonomy
when existing Binding semantics already express the condition.

DO NOT collapse upstream-blocked NO EFFECT with invoked-but-no-effect.

DO NOT infer authority failure, binding failure, Gateway BLOCK, adapter defect,
malicious behavior, or production failure from a NO EFFECT observation alone.

DO NOT treat effect_occurred = True as proof of production execution or an
external real-world effect.

DO NOT modify existing Gateway, Binding, Authority Engine,
Authority-to-Execution Integration, Tool Adapter, lineage, or Digital Custody
semantics merely to make later regression fixtures pass.

DO NOT change frozen fixture outcomes merely to obtain a green regression.
```

If implementation pressure reveals a condition that the existing semantics
cannot express, record that pressure first.

Specification expansion must occur explicitly rather than being introduced
silently during regression repair.

---

## 12. v0.1 disposition

```text
AUTHORITY_TOOL_ADAPTER_EFFECT_BOUNDARY_DESIGN = DRAFT_V0_1

INITIAL_EFFECT_BOUNDARY_INVARIANTS = 5

ELIGIBILITY_REQUIRED_FOR_INVOCATION = DEFINED
BOUND_OPERATION_PRESERVED_TO_ADAPTER = DEFINED
INVOCATION_OBSERVED_EXPLICITLY = DEFINED
EFFECT_OBSERVED_EXPLICITLY = DEFINED
NO_EFFECT_ON_INELIGIBLE_OR_FAILED_PATH = DEFINED

NEW_EFFECT_BOUNDARY_FAILURE_TAXONOMY = NOT_PROPOSED

REGRESSION_FIXTURES = PROPOSED_A_THROUGH_F

EXISTING_GATEWAY_SEMANTICS = PRESERVED
EXISTING_BINDING_SEMANTICS = PRESERVED
EXISTING_AUTHORITY_ENGINE_SEMANTICS = PRESERVED
EXISTING_INTEGRATION_SEMANTICS = PRESERVED
EXISTING_TOOL_ADAPTER_SEMANTICS = PRESERVED
EXISTING_LINEAGE_SEMANTICS = PRESERVED
EXISTING_DIGITAL_CUSTODY_SEMANTICS = PRESERVED

IMPLEMENTATION = NOT_STARTED
REGRESSION = NOT_STARTED
ACTUAL_TOOL_ADAPTER_INVOCATION = NOT_STARTED
SYNTHETIC_EFFECT_OBSERVATION = NOT_STARTED
REAL_EFFECT_BOUNDARY_VALIDATION = NOT_STARTED

PRODUCTION_EFFECT_EXECUTION = NOT_ESTABLISHED
EXTERNAL_REAL_WORLD_EFFECT = NOT_ESTABLISHED
PRODUCTION_AUTHORITY = NOT_ESTABLISHED
LEGAL_AUTHORITY = NOT_ESTABLISHED
PRODUCTION_IDENTITY_TRUST = NOT_ESTABLISHED
INSTITUTIONAL_POLICY_INTEGRATION = NOT_ESTABLISHED
META_GOVERNANCE = NOT_ESTABLISHED
PRODUCTION_READINESS = NOT_ESTABLISHED
```

This document freezes the initial PHAGE Authority-to-Tool-Adapter Effect
Boundary design.

Later regression and implementation must preserve the distinction between:

```text
eligibility
invocation
effect attempt
effect observation
```

The effect-boundary harness must observe state transitions explicitly.

A successful synthetic state transition must not be promoted into a production
or external real-world execution claim.

Regression evidence, Tool Adapter invocation, synthetic effect observation,
and real effect-boundary validation must be introduced in later commits.
