# PHAGE Authority-to-Tool-Adapter Operational Interface Inspection v0.1

Status: INTERFACE INSPECTION RECORD — NO IMPLEMENTATION CLAIM

This document records inspection of the existing PHAGE Tool Adapter and
adjacent execution interfaces before operational-effect regression or
implementation work begins.

The purpose is to determine what the existing interfaces actually express,
rather than inventing a new adapter API to satisfy later fixtures.

This record does not modify Python code.

It does not establish a new Authority-to-ActionEnvelope bridge.

It does not establish production execution or an external real-world effect.

---

## 1. Inspected surfaces

The inspection covered the following existing repository surfaces:

```text
phage_tool_adapter.py
phage_gateway.py
test_phage_tool_adapter.py
phage_executor.py
test_phage_v6_revocation_enforcement.py
phage_authority_execution_integration_v0_1.py
phage_authority_execution_binding_v0_1.py
```

Repo-wide code searches were also used to look for an existing operational
bridge between AuthorityExecutionIntegrator and ActionEnvelope.

Search absence is recorded only as:

```text
NOT FOUND IN INSPECTED REPOSITORY SEARCHES
```

and must not be promoted into proof that no semantically equivalent mapping
could exist under another representation.

---

## 2. Existing Tool Adapter interface

The existing Tool Adapter implementation is:

```text
phage_tool_adapter.py
```

The inspected adapter class is:

```text
SandboxToolAdapter
```

Its operational entry point is:

```text
invoke(envelope: ActionEnvelope) -> str
```

The adapter accepts an optional pre-effect guard:

```text
PreEffectGuard =
Callable[[ActionEnvelope], tuple[bool, str]]
```

The adapter maintains an observable sandbox effect:

```text
SandboxEffect

invoked: bool
action: str | None
target: str | None
```

If the pre-effect guard rejects the operation, `invoke(...)` returns a BLOCKED
result before the sandbox effect is marked as invoked.

If the guard permits the operation, the existing adapter records:

```text
effect.invoked = True
effect.action = envelope.action
effect.target = envelope.target
```

Therefore the currently inspected effect is a bounded sandbox observation.

It does not establish modification of an external real-world system.

---

## 3. ActionEnvelope interface

The existing `ActionEnvelope` inspected in `phage_gateway.py` contains:

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

The inspected schema directly carries:

```text
action
target
```

It does not expose fields named:

```text
subject_id
grant_id
```

Therefore:

```text
ExecutionBinding.subject_id
≠ automatically ActionEnvelope.agent
≠ automatically ActionEnvelope.principal
```

unless that mapping is separately established.

Likewise:

```text
ExecutionBinding.grant_id
```

must not be assumed to be transported inside `ActionEnvelope`.

No modification to `ActionEnvelope` is implied by this inspection.

---

## 4. Existing governed execution boundary

The existing governed execution layer inspected in `phage_executor.py` exposes:

```text
execute_governed(
    envelope: ActionEnvelope,
    tool: Callable[[ActionEnvelope], Any],
)
```

Its observed control flow is:

```text
ActionEnvelope
        ↓
evaluate_action(envelope)
        ↓
ExecutionReceipt
        ↓
Decision != ALLOW
        → tool_invoked = False
        → tool_result = None
```

and:

```text
Decision == ALLOW
        ↓
tool(envelope)
        ↓
tool_invoked = True
        ↓
tool_result = returned result
```

Therefore:

```text
GovernedExecutionResult.tool_invoked = True
```

establishes only that the executor called the supplied tool callable.

It does not by itself establish that the Tool Adapter produced an observable
effect.

In particular:

```text
executor tool invocation
≠
adapter effect observation
```

The two states must remain distinguishable.

---

## 5. Existing SandboxToolAdapter operational regression

The existing regression in `test_phage_tool_adapter.py` already exercises the
real `SandboxToolAdapter` code path through `execute_governed(...)`.

The inspected clean path is structurally:

```text
ActionEnvelope
        ↓
execute_governed(envelope, adapter.invoke)
        ↓
Gateway ALLOW
        ↓
SandboxToolAdapter.invoke(...)
        ↓
SandboxEffect observed
```

The clean fixture asserts:

```text
receipt.decision = ALLOW
tool_invoked = True

adapter.effect.invoked = True
adapter.effect.action = expected action
adapter.effect.target = expected target
```

The same regression also preserves fail-closed cases in which Gateway
evaluation blocks the request and the adapter effect remains uninvoked.

Therefore this inspection establishes:

```text
EXISTING_SANDBOX_TOOL_ADAPTER_OPERATIONAL_REGRESSION = PRESENT
```

This means the next Authority-to-Tool-Adapter work does not need to prove from
zero that `SandboxToolAdapter.invoke(...)` can be operationally exercised.

The unresolved seam is narrower:

```text
Authority / Binding context
        ↓
existing governed Tool Adapter execution path
```

has not yet been found as an implemented operational bridge.

This does not establish production execution.

---

## 6. Existing pre-effect guard boundary

The existing `SandboxToolAdapter` supports:

```text
pre_effect_guard(ActionEnvelope)
→ tuple[bool, str]
```

The inspected session-revocation regression
`test_phage_v6_revocation_enforcement.py` uses this boundary operationally.

The observed sequence is:

```text
session valid
        ↓
evaluate_action(envelope)
        ↓
Gateway ALLOW
        ↓
session revoked
        ↓
SandboxToolAdapter(
    pre_effect_guard = effect-time session validation
)
        ↓
adapter.invoke(envelope)
        ↓
session revalidated
        ↓
revoked session
        ↓
effect not invoked
```

The regression asserts:

```text
adapter.effect.invoked = False
```

after revocation occurs between the earlier ALLOW decision and the downstream
effect attempt.

Therefore:

```text
GATEWAY_ALLOW
≠
PERMANENT_EXECUTION_CAPABILITY
```

and:

```text
EFFECT_TIME_SESSION_REVALIDATION
= EXISTING_PRE_EFFECT_GUARD_USE
```

This existing session-revocation behavior must be preserved.

Future Authority effect-time validation must not silently replace or erase the
existing session guard semantics.

---

## 7. Authority-to-Execution Integration interface

The inspected `AuthorityExecutionIntegrator.evaluate(...)` requires:

```text
gateway_decision
binding
grant
subject_id
action
target
grant_id
at
```

Its observed fail-closed sequence is:

```text
Gateway not ALLOW
→ NOT_EXECUTED

Gateway ALLOW
→ Binding validation
    ↓
Binding not CLEAN
→ NOT_EXECUTED

Binding CLEAN
→ Authority validation
    ↓
Authority not CLEAN
→ NOT_EXECUTED

Binding CLEAN
+
Authority CLEAN
→ tool_adapter_permitted = True
→ EFFECT_PATH_ELIGIBLE
```

Therefore:

```text
Binding CLEAN
≠
Authority CLEAN
```

and:

```text
Authority CLEAN
≠
effect executed
```

and:

```text
EFFECT_PATH_ELIGIBLE
≠
effect occurred
```

The integrator has enough information to validate:

```text
subject_id
action
target
grant_id
```

but the existing `pre_effect_guard` receives only:

```text
ActionEnvelope
```

Any future reuse of the pre-effect boundary for Authority validation would
therefore require an explicitly defined bridge or preserved context.

This inspection does not choose that bridge.

It does not require `grant_id` to be added to `ActionEnvelope`.

It does not choose whether:

```text
subject_id = ActionEnvelope.agent
```

or:

```text
subject_id = ActionEnvelope.principal
```

Those mappings remain unresolved.
---

## 8. Repository-wide bridge search

Repo-wide code search was used to inspect whether an operational bridge from
`AuthorityExecutionIntegrator` to the existing `ActionEnvelope` / Tool Adapter
path already exists.

The search for:

```text
AuthorityExecutionIntegrator(
```

returned operational construction only in:

```text
test_phage_authority_execution_integration_v0_1.py
```

No separate bridge or production-path implementation was found in the
inspected search results.

Therefore:

```text
AUTHORITY_EXECUTION_INTEGRATOR_IMPLEMENTATION = PRESENT

AUTHORITY_EXECUTION_INTEGRATOR_REGRESSION_USE = PRESENT

AUTHORITY_TO_ACTION_ENVELOPE_OPERATIONAL_BRIDGE =
NOT_FOUND_IN_INSPECTED_REPOSITORY_SEARCHES
```

This is a repository-search observation.

It is not a proof that no semantically equivalent bridge could exist under a
different representation or name.

---

## 9. Subject mapping search

The inspection also searched for direct and broader mappings between
`ExecutionBinding.subject_id` and existing `ActionEnvelope` identity fields.

Inspected searches included forms equivalent to:

```text
subject_id=envelope.
subject_id = envelope.
subject_id envelope.agent
subject_id envelope.principal
```

No matching implementation was found in the inspected repository searches.

Therefore:

```text
SUBJECT_ID_TO_ACTION_ENVELOPE_AGENT_MAPPING =
NOT_ESTABLISHED

SUBJECT_ID_TO_ACTION_ENVELOPE_PRINCIPAL_MAPPING =
NOT_ESTABLISHED
```

This does not mean either mapping is impossible or incorrect.

It means the repository evidence inspected here does not establish which
mapping is intended.

The inspection must not resolve this ambiguity by inference alone.

---

## 10. Interface pressure identified

The frozen Operational Effect design requires preservation of:

```text
subject
action
target
grant
```

The inspected existing Tool Adapter boundary directly carries:

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

Therefore:

```text
action preservation = directly representable

target preservation = directly representable

subject preservation = mapping unresolved

grant preservation = not directly represented in ActionEnvelope
```

This is recorded as interface pressure.

It does not authorize modification of:

```text
ActionEnvelope
ExecutionBinding
AuthorityGrant
SandboxToolAdapter
phage_executor
```

merely to make future regression fixtures easier to implement.

It also does not introduce a new failure taxonomy.

Before regression implementation, the bridge semantics for subject identity
and preserved grant context must be made explicit.

---

## 11. Inspection disposition

```text
AUTHORITY_TOOL_ADAPTER_OPERATIONAL_INTERFACE_INSPECTION = COMPLETE_V0_1

SANDBOX_TOOL_ADAPTER_ENTRY_POINT = CONFIRMED

ACTION_ENVELOPE_SCHEMA = CONFIRMED

GOVERNED_EXECUTION_BOUNDARY = CONFIRMED

EXISTING_SANDBOX_TOOL_ADAPTER_OPERATIONAL_REGRESSION = CONFIRMED

PRE_EFFECT_GUARD_BOUNDARY = CONFIRMED

EFFECT_TIME_SESSION_REVALIDATION_USE = CONFIRMED

AUTHORITY_EXECUTION_INTEGRATOR_INTERFACE = CONFIRMED

AUTHORITY_EXECUTION_INTEGRATOR_REGRESSION_USE = CONFIRMED

AUTHORITY_TO_ACTION_ENVELOPE_OPERATIONAL_BRIDGE =
NOT_FOUND_IN_INSPECTED_REPOSITORY_SEARCHES

SUBJECT_ID_TO_AGENT_MAPPING = NOT_ESTABLISHED

SUBJECT_ID_TO_PRINCIPAL_MAPPING = NOT_ESTABLISHED

GRANT_ID_IN_ACTION_ENVELOPE = NOT_PRESENT_IN_INSPECTED_SCHEMA

SUBJECT_MAPPING_SPECIFICATION = UNRESOLVED

GRANT_CONTEXT_BRIDGE = UNRESOLVED

PYTHON_MODIFICATION = NONE

NEW_FAILURE_TAXONOMY = NONE

OPERATIONAL_EFFECT_REGRESSION = NOT_STARTED

OPERATIONAL_EFFECT_IMPLEMENTATION = NOT_STARTED

PRODUCTION_TOOL_ADAPTER_INTEGRATION = NOT_ESTABLISHED

EXTERNAL_REAL_WORLD_EFFECT = NOT_ESTABLISHED

PRODUCTION_EXECUTION = NOT_ESTABLISHED
```

This inspection narrows the next implementation problem to:

```text
Authority / Binding context
        ↓
explicit bridge semantics
        ↓
existing governed execution path
        ↓
existing SandboxToolAdapter
```

The next step must not guess whether `subject_id` means `agent` or `principal`.

Likewise, the absence of `grant_id` from `ActionEnvelope` must not be repaired
silently by expanding the adapter schema.

Any specification decision required to bridge these contexts must be explicit
before regression implementation begins.
