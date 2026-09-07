# PHAGE Principle 0 — Emergency Override Design v0.1

Status: DESIGN DRAFT — NO IMPLEMENTATION CLAIM

This document defines the initial PHAGE Emergency Override boundary for
Principle 0 Schedule governance.

It does not implement an Emergency Override engine, modify the existing
Authority Engine, modify the Schedule implementation, modify ActionEnvelope,
or establish production emergency execution.

It freezes the semantic boundary that later regression and implementation must
preserve.

---

## 1. Design objective

Principle 0 currently requires the operational validation order:

```text
Schedule
↓
Space / Context
↓
Authority
↓
Gateway
↓
Execution boundary
```

Emergency conditions create a narrower question:

```text
Can a normally ineligible Schedule condition be exceptionally admitted
without turning "emergency" into an unrestricted bypass?
```

PHAGE Emergency Override v0.1 answers this by treating Override as a separately
governed authorization path.

Conceptually:

```text
normal Schedule evaluation
↓
SCHEDULE_NO_MATCH
↓
explicit Emergency Override request
↓
Override Authority validation
↓
Override scope validation
↓
Gateway
↓
pre-effect revalidation
↓
effect path eligible or blocked
```

Emergency Override does not erase the original Schedule result.

Therefore:

```text
SCHEDULE_NO_MATCH
+
valid Emergency Override
≠
SCHEDULE_MATCH
```

The original Schedule evaluation remains historically true.

The Override is a separate reason why an operation may remain eligible.

---

## 2. Core separation

PHAGE Emergency Override v0.1 distinguishes:

```text
Emergency condition
≠
Emergency declaration
≠
Emergency Override Authority
≠
Override decision
≠
Gateway ALLOW
≠
Execution
```

An emergency observation does not itself create authority.

A declaration of emergency does not itself create authority.

Possession of ordinary operational Authority does not automatically create
Emergency Override Authority.

Therefore:

```text
EMERGENCY_EXISTS
≠
OVERRIDE_AUTHORIZED
```

and:

```text
ordinary Authority
≠
Emergency Override Authority
```

and:

```text
Override authorized
≠
permanent execution right
```

---

## 3. Emergency Override is not a governance bypass

Emergency Override is itself a governed move.

It must not mean:

```text
ignore Schedule
ignore Authority
ignore identity/session state
ignore target scope
ignore effect-time revalidation
ignore auditability
```

For v0.1, the governing restraint is:

```text
Override may create a narrow exception to a frozen operational boundary.

Override may not dissolve the governance system that defines that boundary.
```

Therefore, PHAGE must never infer Emergency Override merely from:

```text
urgency
high risk
operator request
Agent confidence
Gateway history
previous successful execution
ordinary role name
ordinary AuthorityGrant
```

An Emergency Override must have an explicit governed source.
---

## 4. EmergencyOverrideGrant

Emergency Override authority must be represented explicitly.

For design v0.1, the conceptual record is:

```text
EmergencyOverrideGrant
├─ override_id
├─ subject_id
├─ issuer_id
├─ authorized_action
├─ authorized_target
├─ schedule_ref
├─ override_dimensions
├─ emergency_ref
├─ issued_at
├─ expires_at
├─ revoked
├─ revoked_at
└─ source_ref
```

This structure is conceptual.

It does not freeze a Python class, constructor, persistence model, policy
language, or production issuer system.

### Explicit subject, action, and target

An EmergencyOverrideGrant must identify the subject that may use it.

It must also explicitly bind the action and target to which the exception
applies.

Therefore:

```text
override for subject A
≠
override for subject B
```

and:

```text
override for READ
≠
override for DELETE
```

and:

```text
override for target X
≠
override for target Y
```

Emergency scope must not expand merely because the underlying situation is
urgent.

### Explicit Schedule reference

The override must remain associated with the Schedule boundary against which
the exceptional condition is being evaluated.

Conceptually:

```text
schedule_ref
├─ schedule_id
└─ version
```

An Emergency Override does not rewrite that ScheduleDefinition.

Therefore:

```text
SCHEDULE_NO_MATCH under schedule-OR-7 / v17
+
valid EmergencyOverrideGrant
```

does not become:

```text
SCHEDULE_MATCH under schedule-OR-7 / v17
```

The Schedule result remains `SCHEDULE_NO_MATCH`.

The separate Override path may determine whether that resolved mismatch is
exceptionally admissible for the bound operation.

### Explicit override dimensions

An Override must identify which Schedule dimensions it is permitted to
exception.

Conceptually:

```text
override_dimensions =
{
    TIME,
    SPACE,
    CONTEXT
}
```

The set may contain only the explicitly authorized dimensions.

For example:

```text
override_dimensions = {TIME}
```

must not silently authorize a known `SPACE` mismatch.

Likewise:

```text
override_dimensions = {SPACE}
```

must not silently authorize a known `CONTEXT` mismatch.

Therefore:

```text
some Schedule exception authority
≠
all Schedule exception authority
```

### Explicit emergency reference

`emergency_ref` records the emergency declaration, observation, incident, or
other source context supplied to the Override boundary.

It is a reference.

It does not by itself prove:

```text
that an emergency objectively exists
that the declaration is truthful
that the declaration is lawful
that the issuer has ultimate institutional legitimacy
```

Those claims remain outside Emergency Override v0.1.

### Explicit governed source

Emergency Override Authority must include an explicit issuer and source.

Therefore, PHAGE must not infer Override Authority merely from:

```text
authenticated identity
active session
ordinary AuthorityGrant
role name
high-risk label
emergency_ref alone
prior Gateway ALLOW
prior successful override
```

Missing or unresolvable Override source must fail closed.

### Time-bounded authority

Emergency Override Authority must be temporally bounded.

For design v0.1:

```text
issued_at
expires_at
```

are mandatory conceptual dimensions.

An Override that has expired must not remain usable merely because it was valid
earlier.

Likewise, revocation must take effect independently of its original expiration
time.

Therefore:

```text
earlier Override validity
≠
current Override validity
```

and:

```text
earlier Gateway ALLOW
≠
permanent Override-derived execution right
```

---

## 5. What Emergency Override may and may not override

For v0.1, Emergency Override is narrowly scoped to a resolved Schedule
ineligibility.

The admissible starting condition is:

```text
SCHEDULE_NO_MATCH
```

with sufficient evidence to know why the Schedule did not match.

Emergency Override v0.1 does not convert unresolved state
 into permission.

Therefore:

```text
SCHEDULE_UNRESOLVED
+
Emergency Override request
→ fail closed
```

Not:

```text
SCHEDULE_UNRESOLVED
→ assume mismatch
→ override it
```

This preserves the existing Principle 0 restraint:

```text
unknown
≠
false
```

and:

```text
absence of reliable observation
≠
evidence of Schedule mismatch
```

### Ordinary Authority remains required

Emergency Override Authority does not replace ordinary operational Authority.

For an operation to remain eligible:

```text
ordinary Authority valid
+
Emergency Override Authority valid
```

must both hold where both dimensions are required.

Therefore:

```text
AUTHORITY_UNRESOLVED
```

cannot be repaired by Emergency Override.

Likewise:

```text
AUTHORITY_SCOPE_VIOLATION
AUTHORITY_REVOKED
AUTHORITY_EXPIRED
```

must not be silently converted into permission merely because an Emergency
Override exists.

### Identity and session remain required

Emergency Override does not repair invalid identity or session state.

Therefore:

```text
invalid or unresolved identity
+
valid Emergency Override
→ BLOCK
```

and:

```text
revoked or invalid session
+
valid Emergency Override
→ BLOCK
```

Emergency status must not become a second authentication mechanism.

### Binding remains required

Emergency Override does not repair a subject, action, target, or preserved
grant binding mismatch.

Therefore:

```text
binding mismatch
+
valid Emergency Override
→ BLOCK
```

The Override must apply to the same bound operation that reaches the execution
boundary.

### Gateway remains authoritative

A valid Emergency Override does not force Gateway ALLOW.

Conceptually:

```text
resolved Schedule NO_MATCH
+
valid Emergency Override
+
valid ordinary Authority
+
valid identity/session/binding
→ Schedule-derived obstacle may be exceptionally admissible
→ Gateway still evaluates
```

Therefore:

```text
valid Emergency Override
≠
Gateway ALLOW
```

and:

```text
valid Emergency Override
≠
effect executed
```

Emergency Override may relax only the explicitly authorized Schedule-derived
constraint.

It must not erase failures produced by unrelated PHAGE governance boundaries.

---

## 6. Override evaluation semantics

Emergency Override v0.1 does not introduce a second copy of the existing
Authority failure taxonomy.

Where an EmergencyOverrideGrant fails for an Authority-like reason, the
existing Authority semantics remain authoritative.

Examples include:

```text
missing or unresolvable issuer/source
→ AUTHORITY_UNRESOLVED
```

```text
subject/action/target outside supplied Override scope
→ AUTHORITY_SCOPE_VIOLATION
```

```text
Override grant revoked
→ AUTHORITY_REVOKED
```

```text
Override grant expired
→ AUTHORITY_EXPIRED
```

The Emergency Override layer adds only the question:

```text
Given a resolved SCHEDULE_NO_MATCH and otherwise valid governance state,
may this explicit Override cover the specific Schedule mismatch?
```

For design v0.1, the conceptual Override disposition is:

```text
OVERRIDE_APPLICABLE
OVERRIDE_NOT_APPLICABLE
OVERRIDE_UNRESOLVED
```

These dispositions do not replace the underlying Authority or Schedule result.

### OVERRIDE_APPLICABLE

`OVERRIDE_APPLICABLE` requires:

```text
Schedule result = SCHEDULE_NO_MATCH
+
mismatch dimension explicitly resolved
+
EmergencyOverrideGrant explicitly sourced
+
subject matches
+
action matches
+
target matches
+
schedule_id/version binding resolves
+
mismatch dimension is inside override_dimensions
+
Override Authority not revoked
+
Override Authority not expired
```

It means only that the specific resolved Schedule mismatch may be admitted
into the next governance stage.

It does not mean:

```text
Gateway ALLOW
effect authorized
effect executed
legal emergency established
institutional legitimacy established
```

### OVERRIDE_NOT_APPLICABLE

`OVERRIDE_NOT_APPLICABLE` applies when the Override is structurally valid but
does not cover the resolved Schedule mismatch being evaluated.

For example:

```text
Schedule mismatch = SPACE
override_dimensions = {TIME}
```

results in:

```text
OVERRIDE_NOT_APPLICABLE
```

Likewise:

```text
override bound to schedule-OR-7 / v17
current governing schedule = schedule-OR-7 / v18
```

must not silently inherit applicability.

A different Schedule version requires explicit resolution against the current
governing boundary.

### OVERRIDE_UNRESOLVED

`OVERRIDE_UNRESOLVED` means PHAGE cannot reliably determine whether the
supplied Override can be applied to the resolved operation.

Examples may include:

```text
required override record missing
required schedule reference unresolved
required override dimension unresolved
required emergency_ref unresolved
```

`OVERRIDE_UNRESOLVED` is fail-closed.

It does not mean:

```text
emergency false
actor malicious
override legally invalid
schedule definitely not overridable
```

It means only that the Override boundary cannot be resolved with the supplied
evidence.

---

## 7. Revocation, expiration, and effect-time revalidation

Emergency Override is temporary execution eligibility context.

It is not a durable execution capability.

Conceptually:

```text
T1  Schedule evaluation → SCHEDULE_NO_MATCH
T2  EmergencyOverrideGrant valid and applicable
T3  OVERRIDE_APPLICABLE
T4  Gateway ALLOW
T5  Override state changes
T6  downstream effect attempt
T7  pre-effect Override revalidation
```

If between T4 and T7 the Override:

```text
is revoked
expires
becomes unresolved
no longer covers the current Schedule mismatch
no longer matches subject/action/target
no longer binds to the applicable Schedule version
```

the earlier Override result must not preserve execution eligibility.

Therefore:

```text
earlier OVERRIDE_APPLICABLE
≠
effect-time OVERRIDE_APPLICABLE
```

and:

```text
earlier Gateway ALLOW
≠
permanent Override-derived execution right
```

At the effect boundary PHAGE must re-establish:

```text
current identity/session validity
+
current binding validity
+
current ordinary Authority validity
+
current Schedule state
+
current Emergency Override validity where still required
```

If the current Schedule result is:

```text
SCHEDULE_MATCH
```

the operation may proceed through the ordinary governance path without relying
on the earlier Override.

If the current Schedule result remains:

```text
SCHEDULE_NO_MATCH
```

the current mismatch must still be explicitly covered by a currently valid
Emergency Override.

If the current Schedule result is:

```text
SCHEDULE_UNRESOLVED
```

the effect path must fail closed.

### Existing pre-effect pattern reuse

Emergency Override v0.1 does not introduce a new execution mechanism.

It reuses the existing PHAGE fail-closed temporal pattern:

```text
earlier valid state
↓
earlier ALLOW
↓
state changes before effect
↓
pre-effect revalidation
↓
invalid current state blocks effect
```

This is the same structural control already used for session, Authority, and
Schedule revalidation.

The design therefore defines:

```text
NO_STALE_OVERRIDE_AT_EXECUTION
```

as an invariant.

It is not a new failure taxonomy member.

The observed failure must remain the actual current reason, such as:

```text
AUTHORITY_REVOKED
AUTHORITY_EXPIRED
AUTHORITY_SCOPE_VIOLATION
AUTHORITY_UNRESOLVED
OVERRIDE_NOT_APPLICABLE
OVERRIDE_UNRESOLVED
SCHEDULE_UNRESOLVED
```

No generic:

```text
STALE_OVERRIDE
```

status is introduced in v0.1.

This design does not freeze callback ordering among the existing validators.

It freezes only the fail-closed requirement that all required governance
dimensions remain valid at the effect boundary.
---

## 8. Proposed regression fixtures A-F

The first Emergency Override regression must preserve the following frozen
semantic fixtures.

These fixtures define expected outcomes.

They do not freeze a Python API, storage representation, production emergency
declaration system, institutional policy engine, or production execution path.

No fixture outcome may be changed merely to obtain a green regression.

### Fixture A — resolved TIME mismatch with valid narrow Override

Given:

```text
Schedule result = SCHEDULE_NO_MATCH
resolved mismatch dimension = TIME
```

and:

```text
ordinary Authority = valid
identity/session/binding = valid
```

and an EmergencyOverrideGrant with:

```text
subject = matching subject
action = matching action
target = matching target
schedule_ref = current schedule_id + version
override_dimensions = {TIME}
issuer/source = explicit and resolvable
revoked = false
not expired
```

expected Override result:

```text
OVERRIDE_APPLICABLE
```

The underlying Schedule result remains:

```text
SCHEDULE_NO_MATCH
```

This fixture must not report:

```text
SCHEDULE_MATCH
```

merely because the Override is applicable.

It also does not establish:

```text
Gateway ALLOW
effect executed
```

---

### Fixture B — resolved mismatch outside Override dimensions

Given:

```text
Schedule result = SCHEDULE_NO_MATCH
resolved mismatch dimension = SPACE
```

but:

```text
override_dimensions = {TIME}
```

while the Override is otherwise structurally valid,

expected Override result:

```text
OVERRIDE_NOT_APPLICABLE
```

The TIME exception must not silently expand into SPACE exception authority.

Therefore:

```text
some Override authority
≠
all Schedule exception authority
```

The operation must not gain Schedule-derived eligibility from this Override.

---

### Fixture C — unresolved Schedule cannot be overridden

Given:

```text
Schedule result = SCHEDULE_UNRESOLVED
```

because the required current context is missing, incomplete, stale, or
freshness-unresolved,

even if a supplied EmergencyOverrideGrant otherwise appears structurally
valid,

expected Override result:

```text
OVERRIDE_UNRESOLVED
```

Not:

```text
OVERRIDE_APPLICABLE
```

and not:

```text
OVERRIDE_NOT_APPLICABLE
```

merely to force a deterministic binary result.

This fixture freezes:

```text
unknown
≠
false
```

and:

```text
absence of reliable Schedule/context evidence
≠
resolved Schedule mismatch
```

Emergency Override must not become a mechanism for converting epistemic
uncertainty into permission.

---

### Fixture D — missing Override source remains Authority-unresolved

Given:

```text
Schedule result = SCHEDULE_NO_MATCH
resolved mismatch dimension = TIME
```

and an otherwise matching EmergencyOverrideGrant,

but the Override Authority record lacks a resolvable:

```text
issuer_id
or
source_ref
```

the existing Authority semantics must remain authoritative.

Expected result:

```text
AUTHORITY_UNRESOLVED
```

Not:

```text
OVERRIDE_APPLICABLE
```

The Emergency Override layer must not create a parallel source-resolution
taxonomy merely to make the fixture pass.

This fixture freezes:

```text
emergency_ref
≠
Authority source
```

and:

```text
emergency declaration
≠
Override Authority
```

---

### Fixture E — valid Override does not repair revoked ordinary Authority

Given:

```text
Schedule result = SCHEDULE_NO_MATCH
```

and a currently valid EmergencyOverrideGrant that would otherwise produce:

```text
OVERRIDE_APPLICABLE
```

but the ordinary operational Authority required for the action is:

```text
AUTHORITY_REVOKED
```

expected governance result:

```text
AUTHORITY_REVOKED
```

and:

```text
effect path = BLOCKED / NOT ELIGIBLE
```

Emergency Override must not repair or supersede the revoked ordinary
Authority.

This fixture freezes:

```text
Emergency Override Authority
≠
ordinary operational Authority
```

---

### Fixture F — earlier Override applicability does not survive loss of validity

Given:

```text
T1  Schedule result = SCHEDULE_NO_MATCH
T2  EmergencyOverrideGrant valid
T3  OVERRIDE_APPLICABLE
T4  Gateway ALLOW
```

then before the downstream effect boundary the Override ceases to be valid.

The regression must exercise effect-time revalidation.

#### F1 — Override revoked before effect

At effect time:

```text
Override grant = revoked
```

expected current reason:

```text
AUTHORITY_REVOKED
```

and:

```text
effect path = BLOCKED / NOT ELIGIBLE
```

#### F2 — Override expired before effect

At effect time:

```text
Override grant = expired
```

expected current reason:

```text
AUTHORITY_EXPIRED
```

and:

```text
effect path = BLOCKED / NOT ELIGIBLE
```

The earlier result:

```text
OVERRIDE_APPLICABLE
```

must not be reused as permanent execution capability.

Fixture F deliberately reuses the existing PHAGE pre-effect temporal-control
pattern.

It does not introduce a new Emergency-Override-specific execution mechanism.

It also does not introduce:

```text
STALE_OVERRIDE
```

as a failure status.

The current failure reason must remain the actual current Authority or Override
condition.

---

## 9. Genesis Authority and Meta-Governance boundary

Emergency Override creates a particularly sensitive Authority path.

However, Emergency Override v0.1 does not solve the root-of-trust bootstrap
problem.

The design can require:

```text
explicit issuer
+
explicit source
+
explicit scope
+
explicit schedule binding
+
explicit temporal validity
```

for a supplied EmergencyOverrideGrant.

It cannot, by itself, prove:

```text
who ultimately had legitimate power to create the first Override Authority
whether that institutional delegation is lawful
whether the issuer is constitutionally or organizationally legitimate
whether the emergency declaration process is substantively correct
```

Those questions belong to a later Meta-Governance boundary.

For design v0.1:

```text
OVERRIDE_ISSUER_SOURCE_REQUIRED = YES

EXISTING_AUTHORITY_SOURCE_ASSUMPTION = REUSED

NEW_OVERRIDE_ROOT_OF_TRUST = NOT_CREATED

ULTIMATE_OVERRIDE_ISSUER_LEGITIMACY = NOT_ESTABLISHED

ROOT_AUTHORITY_BOOTSTRAP = OUT_OF_SCOPE

META_GOVERNANCE = OUT_OF_SCOPE
```

Emergency Override must not hide this bootstrap problem by treating:

```text
emergency_ref
```

as self-authorizing.

Therefore:

```text
emergency declared
≠
authority to issue EmergencyOverrideGrant
```

and:

```text
EmergencyOverrideGrant accepted by frozen PHAGE invariants
≠
ultimate institutional legitimacy established
```

Emergency Override v0.1 governs the supplied authorization boundary.

It does not establish who has ultimate sovereign authority to create that
boundary.
---

## 10. Explicit non-claims

PHAGE Emergency Override design v0.1 does NOT establish:

```text
that an emergency objectively exists
that an emergency declaration is truthful
that an emergency declaration is legally valid
that an emergency declaration is institutionally approved
that an Override issuer has ultimate legitimate authority
that the supplied emergency_ref is authentic
that production identity is authentic
that production session state is trustworthy
that production clock state is trustworthy
that production Schedule context is trustworthy
that an action is lawful
that an action is ethical
that an action is clinically appropriate
that an action is operationally desirable
that Gateway must ALLOW
that a Tool Adapter must execute
that an external real-world effect occurred
that production execution is safe
that production deployment is ready
```

A result of:

```text
OVERRIDE_APPLICABLE
```

means only that, under the supplied and sufficiently resolved inputs, the
explicit EmergencyOverrideGrant satisfies the frozen v0.1 exception boundary
for the specific resolved Schedule mismatch.

It does not mean:

```text
EMERGENCY_PROVEN
LEGAL_AUTHORITY_PROVEN
INSTITUTIONAL_LEGITIMACY_PROVEN
EXECUTION_AUTHORIZED_BY_PHAGE_AS_A_WHOLE
EFFECT_OCCURRED
```

Likewise:

```text
OVERRIDE_NOT_APPLICABLE
```

does not establish misconduct, malicious intent, absence of emergency, or
legal prohibition.

And:

```text
OVERRIDE_UNRESOLVED
```

does not establish that no valid Override exists.

It establishes only that PHAGE lacks sufficient resolved information to apply
the frozen Override boundary.

---

## 11. Design freeze

For Emergency Override v0.1:

DO NOT infer Emergency Override Authority from urgency.

DO NOT infer Emergency Override Authority from an emergency declaration.

DO NOT infer Emergency Override Authority from `emergency_ref` alone.

DO NOT infer Emergency Override Authority from ordinary Authority.

DO NOT treat `SCHEDULE_UNRESOLVED` as an overridable Schedule mismatch.

DO NOT convert missing, stale, incomplete, or freshness-unresolved Schedule
context into `SCHEDULE_NO_MATCH` merely to enable Override processing.

DO NOT rewrite an underlying `SCHEDULE_NO_MATCH` into `SCHEDULE_MATCH` because
an Override is applicable.

DO NOT allow a TIME Override to silently cover SPACE or CONTEXT mismatch.

DO NOT allow a SPACE Override to silently cover TIME or CONTEXT mismatch.

DO NOT allow a CONTEXT Override to silently cover TIME or SPACE mismatch.

DO NOT detach an Override from the `schedule_id` and `version` against which it
was evaluated.

DO NOT allow a valid Emergency Override to repair invalid or unresolved
identity.

DO NOT allow a valid Emergency Override to repair revoked or invalid session
state.

DO NOT allow a valid Emergency Override to repair Binding mismatch.

DO NOT allow a valid Emergency Override to repair missing, revoked, expired,
or out-of-scope ordinary Authority.

DO NOT treat `OVERRIDE_APPLICABLE` as Gateway ALLOW.

DO NOT treat `OVERRIDE_APPLICABLE` as effect execution.

DO NOT treat an earlier `OVERRIDE_APPLICABLE` result as permanent execution
capability.

DO NOT introduce a generic `STALE_OVERRIDE` failure taxonomy.

DO NOT introduce a separate Emergency-Override-specific execution mechanism
where the existing PHAGE pre-effect fail-closed pattern already expresses the
required temporal control.

DO NOT create a parallel Override-specific Authority taxonomy where existing
Authority semantics already express the actual failure reason.

DO NOT treat the first EmergencyOverrideGrant as naturally authoritative,
ownerless, or self-legitimating.

DO NOT claim that a supplied Override Authority proves root legitimacy.

DO NOT modify existing Schedule, Authority, session, Gateway, Binding,
ActionEnvelope, Lineage, Digital Custody, or Tool Adapter semantics merely to
make future Emergency Override fixtures pass.

DO NOT change frozen A-F fixture outcomes merely to obtain a green regression.

If implementation pressure reveals that the frozen Emergency Override
semantics cannot be represented cleanly using existing PHAGE boundaries, that
pressure must be recorded before specification expansion or implementation
broadening.

---

## 12. v0.1 disposition

```text
PHAGE_PRINCIPLE0_EMERGENCY_OVERRIDE_DESIGN = DRAFT_V0_1

EMERGENCY_OVERRIDE_ROLE =
NARROW_EXCEPTION_TO_RESOLVED_SCHEDULE_NO_MATCH

EMERGENCY_CONDITION =
SEPARATE_FROM_OVERRIDE_AUTHORITY

EMERGENCY_DECLARATION =
SEPARATE_FROM_OVERRIDE_AUTHORITY

EMERGENCY_OVERRIDE_GRANT =
DEFINED_CONCEPTUALLY

OVERRIDE_SUBJECT_BINDING = DEFINED
OVERRIDE_ACTION_BINDING = DEFINED
OVERRIDE_TARGET_BINDING = DEFINED
OVERRIDE_SCHEDULE_VERSION_BINDING = DEFINED
OVERRIDE_DIMENSION_SCOPE = DEFINED
OVERRIDE_EMERGENCY_REFERENCE = DEFINED
OVERRIDE_EXPLICIT_SOURCE = REQUIRED
OVERRIDE_TEMPORAL_BOUNDING = REQUIRED
OVERRIDE_REVOCATION = REQUIRED

INITIAL_OVERRIDE_DISPOSITIONS = 3

OVERRIDE_APPLICABLE = DEFINED
OVERRIDE_NOT_APPLICABLE = DEFINED
OVERRIDE_UNRESOLVED = DEFINED

SCHEDULE_UNRESOLVED_OVERRIDE =
FAIL_CLOSED

ORDINARY_AUTHORITY_REMAINS_REQUIRED = YES
IDENTITY_SESSION_REMAIN_REQUIRED = YES
BINDING_REMAINS_REQUIRED = YES
GATEWAY_REMAINS_AUTHORITATIVE = YES

NO_STALE_OVERRIDE_AT_EXECUTION =
DEFINED_AS_INVARIANT

EXISTING_PRE_EFFECT_PATTERN_REUSE = REQUIRED

NEW_OVERRIDE_EXECUTION_MECHANISM = NOT_PROPOSED
NEW_STALE_OVERRIDE_TAXONOMY = NOT_PROPOSED
NEW_OVERRIDE_AUTHORITY_FAILURE_TAXONOMY = NOT_PROPOSED

REGRESSION_FIXTURES =
PROPOSED_A_THROUGH_F

FIXTURE_F_REVOCATION_SUBCASE = PROPOSED
FIXTURE_F_EXPIRATION_SUBCASE = PROPOSED

EXISTING_AUTHORITY_SEMANTICS = PRESERVED
EXISTING_SCHEDULE_SEMANTICS = PRESERVED
EXISTING_SESSION_SEMANTICS = PRESERVED
EXISTING_GATEWAY_SEMANTICS = PRESERVED
EXISTING_BINDING_SEMANTICS = PRESERVED
EXISTING_ACTION_ENVELOPE_SCHEMA = PRESERVED
EXISTING_LINEAGE_SEMANTICS = PRESERVED
EXISTING_DIGITAL_CUSTODY_SEMANTICS = PRESERVED
EXISTING_TOOL_ADAPTER_SEMANTICS = PRESERVED

EXISTING_AUTHORITY_SOURCE_ASSUMPTION = REUSED
NEW_OVERRIDE_ROOT_OF_TRUST = NOT_CREATED

ULTIMATE_OVERRIDE_ISSUER_LEGITIMACY = NOT_ESTABLISHED
ROOT_AUTHORITY_BOOTSTRAP = OUT_OF_SCOPE
META_GOVERNANCE = OUT_OF_SCOPE

EMERGENCY_OVERRIDE_IMPLEMENTATION = NOT_STARTED
EMERGENCY_OVERRIDE_REGRESSION = NOT_STARTED
EFFECT_TIME_OVERRIDE_INTEGRATION = NOT_STARTED

PRODUCTION_EMERGENCY_DECLARATION_TRUST = NOT_ESTABLISHED
PRODUCTION_IDENTITY_TRUST = NOT_ESTABLISHED
PRODUCTION_CLOCK_TRUST = NOT_ESTABLISHED
PRODUCTION_CONTEXT_TRUST = NOT_ESTABLISHED
LEGAL_AUTHORITY = NOT_ESTABLISHED
INSTITUTIONAL_POLICY_INTEGRATION = NOT_ESTABLISHED
PRODUCTION_EXECUTION = NOT_ESTABLISHED
PRODUCTION_READINESS = NOT_ESTABLISHED
```

This document freezes the initial PHAGE Principle 0 Emergency Override design
boundary.

For v0.1, Emergency Override is a narrow, explicitly governed exception to a
resolved Schedule mismatch.

It is not a mechanism for converting uncertainty, invalid Authority, invalid
identity/session state, Binding failure, or unrelated governance failure into
permission.

Later regression must validate the frozen A-F fixtures without silently
broadening existing PHAGE governance or execution semantics.
