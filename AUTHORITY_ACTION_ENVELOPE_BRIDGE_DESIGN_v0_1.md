# PHAGE Authority-to-ActionEnvelope Bridge Design v0.1

Status: DESIGN DRAFT — NO IMPLEMENTATION CLAIM

This document defines the initial bridge semantics between the existing PHAGE
Authority / Binding context and the existing `ActionEnvelope` / governed Tool
Adapter execution path.

It follows the completed operational interface inspection.

The inspection established that the existing Tool Adapter path already exists
and can be operationally exercised in the sandbox.

The unresolved boundary is narrower:

```text
Authority / Binding context
        ↓
explicit bridge semantics
        ↓
existing ActionEnvelope
        ↓
existing governed execution path
        ↓
existing SandboxToolAdapter
```

This document does not modify `ActionEnvelope`.

It does not modify `ExecutionBinding`, `AuthorityGrant`,
`SandboxToolAdapter`, or `phage_executor`.

It does not establish production execution.

---

## 1. Bridge objective

The bridge must preserve the operation that survived upstream Authority and
Binding validation when that operation is represented at the existing
`ActionEnvelope` execution boundary.

The frozen upstream operation contains:

```text
subject_id
action
target
grant_id
```

The existing `ActionEnvelope` contains:

```text
principal
agent
action
target
instruction_source
instruction_principal
authorized_actions
authorized_targets
```

The bridge must therefore answer two previously unresolved questions:

```text
1. Which ActionEnvelope identity field represents ExecutionBinding.subject_id?

2. How is grant context preserved to effect time when grant_id is not a field
   of ActionEnvelope?
```

The bridge must answer these questions without silently expanding the existing
Tool Adapter schema.

---

## 2. Subject identity bridge

For PHAGE Authority-to-ActionEnvelope Bridge v0.1:

```text
ExecutionBinding.subject_id
↔
ActionEnvelope.agent
```

This mapping is frozen for this bridge version.

It is not inferred merely from field names.

The repository evidence supporting this bridge choice is structural:

```text
existing session validation
uses the executing agent identity

effect-time session revalidation
uses:

envelope.agent
envelope.action
```

The inspected revocation regression preserves the same agent identity between
the earlier authorized operation and the downstream effect-time guard.

Therefore the Authority subject for this bridge is the executing agent:

```text
authority subject
=
bound execution subject
=
ActionEnvelope.agent
```

`ActionEnvelope.principal` remains a separate identity dimension.

For this bridge:

```text
subject_id ≠ principal
```

does not mean the principal is irrelevant.

It means `principal` is not used as the Authority subject identifier for the
frozen v0.1 bridge.

The bridge must not silently substitute:

```text
binding.subject_id
→ envelope.principal
```

for:

```text
binding.subject_id
→ envelope.agent
```

---

## 3. Principal preservation

Choosing `ActionEnvelope.agent` as the bridge subject must not erase or rewrite
the existing principal identity.

The existing envelope identity structure remains:

```text
principal = existing principal identity
agent     = executing agent identity
```

Therefore:

```text
Authority subject binding
≠
principal identity replacement
```

The bridge does not authorize:

```text
principal = agent
```

or:

```text
agent = principal
```

unless an upstream fixture explicitly contains identical values.

No identity collapse is introduced by this design.

---

## 4. Grant context preservation

`ExecutionBinding.grant_id` is not present in the inspected `ActionEnvelope`
schema.

Bridge v0.1 therefore does not add `grant_id` to `ActionEnvelope`.

Instead, grant identity remains preserved in explicit bridge context outside
the envelope.

Conceptually:

```text
BridgeContext
├─ binding
├─ grant
├─ grant_id
└─ current effect-time validation context
```

while the existing Tool Adapter continues to receive:

```text
ActionEnvelope
```

The intended separation is:

```text
ActionEnvelope
=
existing governed operation representation

BridgeContext
=
Authority / Binding provenance required for effect-time revalidation
```

Therefore:

```text
grant context preserved
≠
grant_id embedded in ActionEnvelope
```

The grant context must remain associated with the same operation represented
by the envelope.

It must not be reconstructed from:

```text
authorized_actions
authorized_targets
instruction_source
instruction_principal
previous Gateway ALLOW
previous successful execution
```

Those fields may carry existing Gateway semantics, but they are not a
substitute for the frozen Authority grant identity.
---

## 5. Initial bridge invariants

PHAGE Authority-to-ActionEnvelope Bridge v0.1 proposes six initial invariants:

```text
SUBJECT_TO_AGENT_MAPPING_EXPLICIT

PRINCIPAL_IDENTITY_PRESERVED

BOUND_ACTION_TARGET_PRESERVED

GRANT_CONTEXT_PRESERVED_OUT_OF_ENVELOPE

EFFECT_TIME_AUTHORITY_REVALIDATED

SESSION_AND_AUTHORITY_GUARDS_COMPOSE_FAIL_CLOSED
```

These invariants define only the bridge between already-existing PHAGE
Authority / Binding semantics and the already-existing governed Tool Adapter
path.

They do not redefine Gateway, session, Binding, Authority Engine,
ActionEnvelope, SandboxToolAdapter, or effect-boundary semantics.

They do not establish production execution.

---

## 6. Invariant 1 — SUBJECT_TO_AGENT_MAPPING_EXPLICIT

For this bridge version, the Authority / Binding subject must correspond to the
existing executing-agent field:

```text
binding.subject_id
=
envelope.agent
```

The bridge must fail closed if the operation reaching the bridge no longer
preserves that identity.

Conceptually:

```text
binding.subject_id = agent-A

envelope.agent = agent-A
```

may satisfy the subject bridge.

But:

```text
binding.subject_id = agent-A

envelope.agent = agent-B
```

must not be treated as the same bound operation.

Likewise, this bridge must not silently substitute:

```text
envelope.principal
```

for:

```text
envelope.agent
```

when validating the frozen Authority subject.

This invariant establishes only the v0.1 bridge mapping.

It does not claim that `agent` and `principal` can never contain identical
values.

---

## 7. Invariant 2 — PRINCIPAL_IDENTITY_PRESERVED

Mapping the Authority subject to `ActionEnvelope.agent` must not erase,
rewrite, or collapse the existing principal identity.

The bridge must preserve both dimensions:

```text
principal = existing principal identity

agent = executing agent identity
```

Therefore:

```text
Authority subject validated
≠
principal identity replaced
```

The bridge must not manufacture:

```text
principal = agent
```

or:

```text
agent = principal
```

merely to make Authority validation pass.

If the incoming envelope already contains identical values, that fact may be
preserved.

The bridge itself must not create the equality.

---

## 8. Invariant 3 — BOUND_ACTION_TARGET_PRESERVED

The `action` and `target` presented in the existing `ActionEnvelope` must be
the same action and target preserved by the upstream execution binding.

Required bridge relation:

```text
binding.action
=
envelope.action
```

and:

```text
binding.target
=
envelope.target
```

The bridge must not convert:

```text
bound action = READ
```

into:

```text
envelope.action = DELETE
```

or substitute another target after upstream validation.

Where the existing Binding semantics fully express the mismatch, the bridge
must reuse:

```text
BOUND_OPERATION_MISMATCH
```

rather than inventing a new bridge-specific failure taxonomy.

Therefore:

```text
bridge mismatch
≠
permission to reinterpret the operation
```

The existing bound-operation semantics remain authoritative for this
condition.

---

## 9. Invariant 4 — GRANT_CONTEXT_PRESERVED_OUT_OF_ENVELOPE

Grant identity must remain explicit across the bridge even though `grant_id`
is not a field of the existing `ActionEnvelope`.

Conceptually, the bridge must preserve:

```text
binding.grant_id
        =
bridge grant context
        =
the grant used for effect-time Authority validation
```

The bridge must not reconstruct grant identity from:

```text
envelope.authorized_actions
envelope.authorized_targets
envelope.instruction_source
envelope.instruction_principal
previous Gateway ALLOW
previous successful execution
```

Those values do not replace the explicit Authority grant context.

Therefore:

```text
ActionEnvelope contains authority-related fields
≠
Authority grant identity is established
```

and:

```text
grant_id absent from ActionEnvelope
≠
grant context may be discarded
```

The grant context must remain associated with the same bound operation until
the effect-time validation boundary.

This design does not yet freeze a Python `BridgeContext` class or constructor.

It freezes the required semantics, not a guessed implementation API.
---

## 10. Invariant 5 — EFFECT_TIME_AUTHORITY_REVALIDATED

An Authority decision that was CLEAN before the downstream effect boundary
must not be treated as permanently valid.

The bridge must preserve enough Authority / Binding context to validate the
same bound operation again when the existing Tool Adapter is about to cross
the effect boundary.

Conceptually:

```text
earlier Authority CLEAN
        ↓
operation proceeds toward Tool Adapter
        ↓
time passes / authority state may change
        ↓
effect-time Authority validation
        ↓
effect eligible only if Authority is still valid
```

Therefore:

```text
earlier Authority CLEAN
≠
permanent effect-time authority
```

and:

```text
earlier EFFECT_PATH_ELIGIBLE
≠
permanent execution capability
```

Effect-time validation must use the preserved bridge context for:

```text
binding
grant
grant_id
```

together with the operation represented at the current execution boundary:

```text
subject_id = envelope.agent
action     = envelope.action
target     = envelope.target
```

and the current effect-time validation time.

The bridge must not obtain the effect-time grant identity by reconstructing it
from `ActionEnvelope`.

If the preserved grant is revoked, expired, missing, or no longer authorizes
the current bound operation at effect time, the effect path must fail closed.

Existing Authority taxonomy must be preserved where it already expresses the
condition, including:

```text
AUTHORITY_UNRESOLVED
AUTHORITY_SCOPE_VIOLATION
AUTHORITY_REVOKED
AUTHORITY_EXPIRED
```

This bridge does not introduce a new generic stale-authority taxonomy.

The stale condition is temporal.

The reported result must remain the actual Authority reason observed at
effect time.

---

## 11. Invariant 6 — SESSION_AND_AUTHORITY_GUARDS_COMPOSE_FAIL_CLOSED

The existing effect-time session guard must remain valid after Authority
effect-time validation is introduced.

Authority validation must not replace session validation.

Session validation must not replace Authority validation.

At the effect boundary, the required semantics are:

```text
SESSION_VALID
AND
AUTHORITY_VALID
AND
BOUND_OPERATION_PRESERVED
→ effect may remain eligible
```

Any required condition that fails must prevent the sandbox effect.

Therefore:

```text
SESSION_INVALID
+
AUTHORITY_VALID
→ effect blocked
```

and:

```text
SESSION_VALID
+
AUTHORITY_INVALID
→ effect blocked
```

and:

```text
SESSION_INVALID
+
AUTHORITY_INVALID
→ effect blocked
```

Only:

```text
SESSION_VALID
+
AUTHORITY_VALID
+
BOUND_OPERATION_PRESERVED
```

may allow the existing Tool Adapter effect path to remain eligible.

The bridge must preserve the existing session-revocation invariant:

```text
Gateway ALLOW
        ↓
session revoked
        ↓
effect-time session validation
        ↓
effect not invoked
```

Adding Authority validation must not turn that state into an Authority-only
decision or erase the session failure semantics.

Likewise, a valid session must not convert revoked, expired, unresolved, or
out-of-scope Authority into an allowed effect.

Conceptually:

```text
existing pre-effect boundary
        ↓
composed fail-closed validation
        ├─ session state
        └─ Authority / Binding bridge context
        ↓
ALLOW EFFECT PATH only if all required conditions pass
```

This design freezes logical composition semantics.

It does not yet freeze:

```text
a Python composed-guard class
callback ordering
a new pre_effect_guard signature
a new ActionEnvelope field
```

Implementation must reuse the existing effect-time boundary where possible
without silently changing the existing session, Gateway, Binding, Authority,
or Tool Adapter contracts.

If the existing single `pre_effect_guard(ActionEnvelope)` callback cannot
represent the required composition cleanly, that implementation pressure must
be recorded before any interface expansion is introduced.
---

## 12. Proposed bridge regression fixtures

PHAGE Authority-to-ActionEnvelope Bridge v0.1 proposes seven initial
regression fixtures.

These fixtures test bridge semantics only.

They do not by themselves establish that the existing Tool Adapter was
invoked or that an operational effect occurred.

They freeze expected semantic outcomes, not a specific Python bridge API.

No fixture may be changed merely to obtain a green regression.

---

### Fixture A — clean subject, operation, and grant bridge

Given an execution binding:

```text
subject_id = agent-A
action     = READ
target     = record-123
grant_id   = G-001
```

and an existing ActionEnvelope:

```text
principal = user-123
agent     = agent-A
action    = READ
target    = record-123
```

with explicit preserved bridge context:

```text
binding.grant_id = G-001
bridge grant_id  = G-001
grant.grant_id   = G-001
```

and:

```text
session = valid
Authority at effect time = valid
```

Expected preserved results:

```text
BindingStatus = CLEAN
AuthorityStatus = CLEAN
EffectDisposition = EFFECT_PATH_ELIGIBLE
```

Expected identity observations:

```text
binding.subject_id = envelope.agent
envelope.principal = user-123
```

The principal must remain unchanged.

This fixture establishes only clean bridge eligibility.

It does not establish Tool Adapter invocation or effect occurrence.

---

### Fixture B — subject does not match executing agent

Given:

```text
binding.subject_id = agent-A

envelope.agent = agent-B
```

while action, target, and grant context otherwise match.

Expected existing Binding result:

```text
BOUND_OPERATION_MISMATCH
```

Expected disposition:

```text
NOT_EXECUTED
```

The bridge must not retry subject validation using:

```text
envelope.principal
```

merely to make the operation pass.

No new bridge-specific subject-mismatch taxonomy is introduced.

---

### Fixture C — principal differs from agent but bound agent is preserved

Given:

```text
binding.subject_id = agent-A

envelope.agent     = agent-A
envelope.principal = user-123
```

and the action, target, grant context, session, and Authority are all valid.

Expected result:

```text
BindingStatus = CLEAN
AuthorityStatus = CLEAN
EffectDisposition = EFFECT_PATH_ELIGIBLE
```

The bridge must preserve:

```text
envelope.principal = user-123
```

It must not rewrite:

```text
principal = agent-A
```

This fixture establishes that:

```text
principal != agent
```

is not by itself a bridge failure.

It also establishes that the Authority subject for bridge v0.1 is the
executing agent rather than the principal.

---

### Fixture D — bound action or target changes at the envelope boundary

Given a frozen binding:

```text
subject_id = agent-A
action     = READ
target     = record-123
grant_id   = G-001
```

but the current envelope contains:

```text
agent  = agent-A
action = DELETE
target = record-123
```

or a different target.

Expected preserved Binding result:

```text
BOUND_OPERATION_MISMATCH
```

Expected disposition:

```text
NOT_EXECUTED
```

The bridge must reuse existing Binding semantics.

It must not reinterpret or repair the operation.

---

### Fixture E — preserved grant context does not match binding

Given:

```text
binding.grant_id = G-001
```

but the preserved bridge context presents:

```text
grant_id = G-002
```

Expected preserved Binding result:

```text
BOUND_GRANT_MISMATCH
```

Expected disposition:

```text
NOT_EXECUTED
```

The bridge must not reconstruct `G-001` from:

```text
authorized_actions
authorized_targets
instruction_source
instruction_principal
```

or from a previous successful decision.

No new grant-bridge failure taxonomy is introduced.

---

### Fixture F — Authority revoked after earlier clean decision

Given an initially clean bridge:

```text
binding subject/action/target/grant = matched
session = valid
Authority = valid
```

and an earlier result:

```text
AuthorityStatus = CLEAN
EffectDisposition = EFFECT_PATH_ELIGIBLE
```

then, before the effect-time boundary:

```text
grant G-001 is revoked
```

Effect-time Authority validation must observe:

```text
AuthorityStatus = AUTHORITY_REVOKED
EffectDisposition = NOT_EXECUTED
```

The valid session must not override revoked Authority.

Therefore:

```text
earlier Authority CLEAN
≠
effect-time Authority CLEAN
```

This fixture preserves the existing Authority taxonomy.

It does not introduce `STALE_AUTHORITY`.

---

### Fixture G — session revoked while Authority remains valid

Given an initially clean bridge:

```text
binding subject/action/target/grant = matched
session = valid
Authority = valid
```

and an earlier eligible path, then before the effect boundary:

```text
session is revoked
```

while:

```text
Authority remains valid
```

Expected composed-boundary behavior:

```text
effect-time session validation = reject
effect invocation = blocked
```

Authority validity must not override the session failure.

The existing session-revocation semantics must remain preserved.

This fixture does not replace the existing session failure reason with an
Authority failure.

---

## 13. Fixture interpretation restraint

The bridge regression must preserve the distinction between:

```text
bridge eligibility
Tool Adapter invocation
effect attempt
effect observation
production execution
```

Therefore:

```text
EFFECT_PATH_ELIGIBLE
≠
Tool Adapter invoked
```

and:

```text
bridge regression PASS
≠
operational effect regression PASS
```

and:

```text
bridge regression PASS
≠
production execution established
```

The later operational-effect regression remains a separate validation layer.
---

## 14. Design freeze discipline

Before regression or implementation:

```text
DO NOT reinterpret ExecutionBinding.subject_id as ActionEnvelope.principal.

DO NOT silently switch the frozen v0.1 mapping from:
ExecutionBinding.subject_id
→ ActionEnvelope.agent

to another identity field.

DO NOT collapse principal and agent identity merely to make Authority
validation pass.

DO NOT add grant_id to ActionEnvelope merely to simplify the bridge.

DO NOT reconstruct Authority grant identity from authorized_actions,
authorized_targets, instruction_source, instruction_principal, previous
Gateway ALLOW, or previous successful execution.

DO NOT discard preserved grant context merely because ActionEnvelope does not
contain grant_id.

DO NOT permit subject, action, target, or grant substitution after the upstream
operation has been bound.

DO NOT invent a new bridge-specific failure taxonomy where existing Binding or
Authority taxonomy already expresses the condition.

DO NOT introduce a generic STALE_AUTHORITY status.

DO NOT treat an earlier Authority CLEAN result or EFFECT_PATH_ELIGIBLE result
as permanent effect-time authority.

DO NOT replace existing effect-time session validation with Authority
validation.

DO NOT allow valid Authority to override an invalid session.

DO NOT allow a valid session to override invalid Authority.

DO NOT modify existing Gateway, session, Binding, Authority Engine,
Authority-to-Execution Integration, ActionEnvelope, SandboxToolAdapter,
phage_executor, Lineage, or Digital Custody semantics merely to make bridge
fixtures pass.

DO NOT treat EFFECT_PATH_ELIGIBLE as proof that the Tool Adapter was invoked,
an effect was attempted, an effect was observed, or production execution
occurred.

DO NOT change frozen fixture outcomes merely to obtain a green regression.
```

The bridge requires fail-closed logical composition of session, Authority, and
bound-operation validation at the effect boundary.

This design does not yet freeze:

```text
a Python BridgeContext class
a composed-guard class
callback ordering
a new pre_effect_guard signature
a new ActionEnvelope field
```

If implementation pressure shows that the existing interfaces cannot represent
the frozen bridge semantics cleanly, that pressure must be recorded first.

Specification expansion must occur explicitly rather than being introduced
silently during regression repair.

---

## 15. v0.1 disposition

```text
AUTHORITY_ACTION_ENVELOPE_BRIDGE_DESIGN = DRAFT_V0_1

INITIAL_BRIDGE_INVARIANTS = 6

SUBJECT_TO_AGENT_MAPPING_EXPLICIT = DEFINED
PRINCIPAL_IDENTITY_PRESERVED = DEFINED
BOUND_ACTION_TARGET_PRESERVED = DEFINED
GRANT_CONTEXT_PRESERVED_OUT_OF_ENVELOPE = DEFINED
EFFECT_TIME_AUTHORITY_REVALIDATED = DEFINED
SESSION_AND_AUTHORITY_GUARDS_COMPOSE_FAIL_CLOSED = DEFINED

SUBJECT_MAPPING =
EXECUTION_BINDING_SUBJECT_ID_TO_ACTION_ENVELOPE_AGENT

PRINCIPAL_IDENTITY_ROLE = PRESERVED_SEPARATELY

GRANT_CONTEXT_LOCATION = OUT_OF_ENVELOPE_BRIDGE_CONTEXT

GRANT_ID_ADDED_TO_ACTION_ENVELOPE = NO

NEW_BRIDGE_FAILURE_TAXONOMY = NOT_PROPOSED
NEW_STALE_AUTHORITY_TAXONOMY = NOT_PROPOSED

REGRESSION_FIXTURES = PROPOSED_A_THROUGH_G

EXISTING_GATEWAY_SEMANTICS = PRESERVED
EXISTING_SESSION_SEMANTICS = PRESERVED
EXISTING_BINDING_SEMANTICS = PRESERVED
EXISTING_AUTHORITY_ENGINE_SEMANTICS = PRESERVED
EXISTING_AUTHORITY_EXECUTION_INTEGRATION_SEMANTICS = PRESERVED
EXISTING_ACTION_ENVELOPE_SCHEMA = PRESERVED
EXISTING_TOOL_ADAPTER_SEMANTICS = PRESERVED
EXISTING_PRE_EFFECT_SESSION_GUARD = PRESERVED
EXISTING_LINEAGE_SEMANTICS = PRESERVED
EXISTING_DIGITAL_CUSTODY_SEMANTICS = PRESERVED

PYTHON_BRIDGE_CONTEXT_API = NOT_FROZEN
COMPOSED_GUARD_API = NOT_FROZEN
CALLBACK_ORDERING = NOT_FROZEN

BRIDGE_REGRESSION = NOT_STARTED
BRIDGE_IMPLEMENTATION = NOT_STARTED
AUTHORITY_EFFECT_TIME_BRIDGE = NOT_STARTED
SESSION_AUTHORITY_GUARD_COMPOSITION = NOT_STARTED

AUTHORITY_OPERATIONAL_EFFECT_REGRESSION = NOT_STARTED
AUTHORITY_OPERATIONAL_EFFECT_IMPLEMENTATION = NOT_STARTED

PRODUCTION_TOOL_ADAPTER_INTEGRATION = NOT_ESTABLISHED
EXTERNAL_REAL_WORLD_EFFECT = NOT_ESTABLISHED
PRODUCTION_EXECUTION = NOT_ESTABLISHED

PRODUCTION_AUTHORITY = NOT_ESTABLISHED
LEGAL_AUTHORITY = NOT_ESTABLISHED
PRODUCTION_IDENTITY_TRUST = NOT_ESTABLISHED
INSTITUTIONAL_POLICY_INTEGRATION = NOT_ESTABLISHED
META_GOVERNANCE = NOT_ESTABLISHED
PRODUCTION_READINESS = NOT_ESTABLISHED
```

This document freezes the initial PHAGE Authority-to-ActionEnvelope Bridge
design boundary.

For bridge v0.1:

```text
ExecutionBinding.subject_id
→ ActionEnvelope.agent
```

is the explicit subject mapping.

`ActionEnvelope.principal` remains a separate preserved identity dimension.

Authority grant identity remains explicit in preserved bridge context outside
the existing ActionEnvelope schema.

At effect time:

```text
SESSION_VALID
AND
AUTHORITY_VALID
AND
BOUND_OPERATION_PRESERVED
```

is required for the effect path to remain eligible.

A successful bridge regression establishes only that the frozen Authority /
Binding context was preserved consistently into the existing ActionEnvelope
execution boundary.

It does not establish Tool Adapter invocation, operational effect observation,
external real-world effect, or production execution.

Regression evidence and bridge implementation must be introduced in later
commits.
