# PHAGE Trust Evidence Temporal Semantics Design v0.1

## Artifact status

Specification maturity: DESIGN FROZEN  
Executable validation: NOT STARTED  
Implementation maturity: NOT STARTED  
Production assurance: NOT ESTABLISHED  
Independent external review: NOT PERFORMED

Design status as of: 2026-09-13 / commit ref: b435cd9
Re-issue required upon: first freshness-policy representation frozen,
first trusted-time boundary implemented, or first executable fixture named.

This document defines conceptual temporal semantics for PHAGE Trust Evidence.

It does not introduce a G6 fixture, freshness implementation,
replay-enforcement mechanism, trusted-clock implementation,
or single-use consumption mechanism.

---

## Existing open assumption

The existing Trust Evidence Origin prototype retains:

`ASSUMED_GENESIS_PRODUCER_AUTHORITY`

Producer identity and producer caller authorization remain outside
the validated Trust Evidence Origin boundary.

Temporal semantics defined here do not resolve, replace, or supersede
that open assumption.

Therefore:

`TEMPORAL_VALIDATION ≠ PRODUCER_AUTHORITY_VALIDATION`

and:

`COMPLETE_PROVENANCE_CHAIN ≠ LEGITIMATE_GENESIS_AUTHORITY`

A complete evidence chain cannot by itself establish that the entity
at the beginning of that chain had legitimate authority to act as
the producer.

---

## Core dimensional separation

Evidence origin, freshness, and replay or consumption policy are
independent dimensions.

Therefore:

`EVIDENCE_ORIGIN_VERIFIED ≠ EVIDENCE_FRESH`

`EVIDENCE_FRESH ≠ EVIDENCE_SINGLE_USE`

`REPEATED_PRESENTATION ≠ REPLAY_VIOLATION`

An evidence artifact may have historically verified origin while no
longer being fresh for a particular governed use.

Expiration or staleness MUST NOT rewrite historical origin as:

`EVIDENCE_ORIGIN_UNVERIFIED`

Origin answers:

`Who produced this evidence, within the validated origin boundary?`

Freshness answers:

`Is this evidence temporally acceptable under the applicable governed policy?`

Replay or consumption policy answers:

`Is this presentation or use permitted under the applicable governed use policy?`

These questions MUST NOT collapse into one Boolean result.

---

## Initial freshness dispositions

The initial conceptual freshness dispositions are:

`EVIDENCE_FRESH`

`EVIDENCE_STALE`

`EVIDENCE_FRESHNESS_UNRESOLVED`

### EVIDENCE_FRESH

The evidence age is resolvable under the applicable governed freshness
policy and remains within its permitted freshness window.

### EVIDENCE_STALE

The evidence age is resolvable under the applicable governed freshness
policy and exceeds its permitted freshness window.

### EVIDENCE_FRESHNESS_UNRESOLVED

Freshness cannot be safely determined.

Examples include:

- missing `observed_at`
- malformed `observed_at`
- unavailable trusted current time
- missing freshness policy
- unresolved freshness-policy version
- missing policy-required temporal context
- inability to determine which governed freshness policy applies

Unknown freshness MUST NOT silently become:

`EVIDENCE_FRESH`

Likewise, unresolved freshness MUST NOT be rewritten as a known stale
result merely to force a binary answer.

---

## EVIDENCE_FRESHNESS_POLICY_IS_GOVERNED_STATE

The threshold or thresholds determining:

`EVIDENCE_FRESH`

versus:

`EVIDENCE_STALE`

are governed policy state.

They are subject to the same applicable `WRITE_POLICY` and
self-authorization controls as other governed policy.

Freshness thresholds MUST NOT be treated merely as:

- hardcoded constants
- caller-selected parameters
- unmanaged deployment configuration
- locally editable convenience values outside governed policy

Changing a freshness threshold is a policy mutation.

Therefore:

`FRESHNESS_THRESHOLD_CHANGE = POLICY_MUTATION`

not:

`FRESHNESS_THRESHOLD_CHANGE = LOCAL_CONFIGURATION_ONLY`

The prototype MUST NOT silently allow the party benefiting from an
older or newer evidence interpretation to select its own freshness
window.

---

## Freshness-policy identity and version

A freshness evaluation MUST identify the governed policy state under
which it was evaluated.

Conceptually, freshness evaluation depends on at least:

- evidence `observed_at`
- trusted current time
- freshness-policy identity
- freshness-policy version
- policy-defined freshness threshold
- policy-required temporal or contextual scope

A result derived under:

`freshness_policy = P_n`

MUST NOT silently be treated as equivalent to a result under:

`freshness_policy = P_n+1`

if the governed policy changed.

This design does not yet define the execution-time revalidation
mechanism for freshness-policy changes.

---

## TRUSTED_TIME_SOURCE_REQUIRED

Freshness evaluation MUST use current time obtained from a trusted
verifier-side time source.

The caller MUST NOT be permitted to supply the authoritative value of
"now" used to determine evidence freshness.

Therefore:

`CALLER_REPORTED_NOW ≠ TRUSTED_CURRENT_TIME`

A caller-provided timestamp may itself be evidence.

It cannot become the authoritative clock merely because it was supplied
to the verifier.

If trusted current time cannot be resolved, the result MUST be:

`EVIDENCE_FRESHNESS_UNRESOLVED`

not:

`EVIDENCE_FRESH`

and not an invented deterministic stale result.

The current Trust Evidence Origin prototype does not yet implement a
production trusted-current-time source.

---

## observed_at semantics

The current Trust Evidence Origin prototype content-binds:

`observed_at`

as part of the evidence snapshot.

That content binding establishes only that the bound `observed_at`
value has not been changed without invalidating the tested origin
binding.

It does NOT establish that:

- `observed_at` was originally truthful
- `observed_at` came from a trusted clock
- the producer was authorized to assert that time
- the evidence remains fresh now

Therefore:

`OBSERVED_AT_CONTENT_BINDING ≠ TRUSTED_TIME_ATTESTATION`

and:

`OBSERVED_AT ≠ TRUSTED_NOW`

---

## Origin status must survive staleness

A historically verified-origin artifact may later become stale.

Conceptually:

`EVIDENCE_ORIGIN_VERIFIED + EVIDENCE_FRESH`

may later become:

`EVIDENCE_ORIGIN_VERIFIED + EVIDENCE_STALE`

without becoming:

`EVIDENCE_ORIGIN_UNVERIFIED`

Freshness is a current-use property.

Origin is a provenance property within the tested origin boundary.

The two MUST remain independently representable.

---

## Replay semantics

Repeated presentation alone does not establish replay violation.

A repeated evidence artifact may be legitimate if its governed use
policy allows reuse.

Therefore:

`SECOND_PRESENTATION ≠ REPLAY_ATTACK`

and:

`REPEATED_PRESENTATION ≠ REPLAY_VIOLATION`

unless the applicable governed use policy makes that presentation
invalid.

Replay semantics require an explicit use model before a violation can
be defined.

---

## Evidence reuse policy

Potential governed evidence-use models include:

- reusable within a validity window
- single-use
- version-bound
- context-bound
- session-bound
- other governed policy-defined reuse semantics

No default single-use assumption is introduced in v0.1.

The evidence artifact MUST NOT self-declare that it is reusable or
single-use in a manner that bypasses governed policy.

Likewise, a caller MUST NOT choose the reuse policy merely because a
particular choice permits the desired action.

---

## EVIDENCE_USE_POLICY_IS_GOVERNED_STATE

The rules determining whether an evidence artifact is:

- reusable
- single-use
- context-bound
- session-bound
- otherwise consumption-limited

are governed policy state.

They are subject to applicable `WRITE_POLICY` and self-authorization
controls.

Therefore:

`EVIDENCE_REUSE_RULE ≠ CALLER_PREFERENCE`

and:

`EVIDENCE_REUSE_RULE ≠ UNGOVERNED_DEPLOYMENT_CONFIG`

A change from reusable to single-use, or from single-use to reusable,
is a policy mutation.

---

## Single-use semantics

Single-use behavior, if introduced later, is a governed evidence-use
policy.

It is not an intrinsic property of all Trust Evidence.

The current design does not make all evidence single-use.

A single-use policy would require the system to distinguish at least:

`UNUSED`

from:

`CONSUMED`

without allowing concurrent consumers to both succeed.

Implementation is NOT STARTED.

---

## EVIDENCE_CONSUMPTION_MUST_BE_ATOMIC

If a future governed policy marks an evidence instance as single-use,
consumption MUST be an atomic check-and-set operation.

Conceptually:

`CHECK_UNUSED + MARK_CONSUMED`

must behave as one indivisible state transition.

Two concurrent Decisions MUST NOT both successfully consume the same
single-use evidence instance.

This is structurally analogous to:

`RESOURCE_BINDING_MUST_BE_ATOMIC`

Allocation atomicity and evidence-consumption atomicity are distinct
mechanisms but share the same concurrency problem shape.

Therefore:

`CHECK_UNUSED`
followed later by
`MARK_CONSUMED`

without atomicity is insufficient.

Atomic evidence consumption implementation is NOT STARTED.

---

## Consumption state is not origin state

If a future evidence instance becomes consumed, that consumption state
MUST NOT rewrite its historical origin.

Conceptually:

`EVIDENCE_ORIGIN_VERIFIED + CONSUMED`

is distinct from:

`EVIDENCE_ORIGIN_UNVERIFIED`

Consumption answers whether another governed use is permitted.

It does not answer who originally produced the artifact.

---

## Freshness is not consumption

A fresh artifact may already be consumed.

A stale artifact may never have been consumed.

Therefore:

`FRESH ≠ UNUSED`

`STALE ≠ CONSUMED`

and:

`FRESHNESS ≠ CONSUMPTION`

These dimensions MUST remain independently representable.

---

## Unresolved temporal state

Temporal evaluation must fail closed when required temporal information
cannot be resolved.

Examples include:

- trusted current time unavailable
- freshness policy unavailable
- applicable policy version unresolved
- evidence timestamp malformed
- required temporal context missing
- required reuse policy unresolved

The exact downstream fail-closed effect is NOT frozen by this document.

This design freezes only that unresolved temporal state MUST NOT be
silently promoted to a positive temporal determination.

Therefore:

`UNRESOLVED ≠ FRESH`

and:

`UNRESOLVED ≠ REUSE_ALLOWED`

unless a later governed specification explicitly establishes otherwise.

---

## Temporal validation and execution

A positive freshness result does not itself authorize execution.

Likewise, a non-violating repeated presentation does not itself
authorize execution.

Therefore:

`EVIDENCE_FRESH ≠ EXECUTION_AUTHORIZED`

`REUSE_ALLOWED ≠ EXECUTION_AUTHORIZED`

Temporal evaluation is one input to downstream governance.

It does not replace:

- Authority
- Gateway decision
- execution-time revalidation
- Tool Adapter effect boundary

Existing PHAGE distinctions remain:

`Assessment ≠ Authorization ≠ Execution`

---

## Existing producer-authority open item

This temporal design retains the previously documented:

`ASSUMED_GENESIS_PRODUCER_AUTHORITY`

The current Trust Evidence Origin prototype does not establish:

- producer caller authentication
- producer caller authorization
- cross-process producer identity
- legitimate genesis producer authority

Temporal validation does not repair that gap.

A fresh, non-replayed artifact from an unauthorized or illegitimate
producer does not become trustworthy merely because its temporal
properties are valid.

Therefore:

`TEMPORAL_VALIDATION ≠ PRODUCER_AUTHORITY_VALIDATION`

and:

`FRESH + REUSE_ALLOWED ≠ LEGITIMATE_PRODUCER_AUTHORITY`

---

## Preserved distinctions

`ORIGIN ≠ FRESHNESS`

`FRESHNESS ≠ REPLAY_POLICY`

`FRESHNESS ≠ CONSUMPTION`

`OBSERVED_AT ≠ TRUSTED_NOW`

`OBSERVED_AT_CONTENT_BINDING ≠ TRUSTED_TIME_ATTESTATION`

`POLICY_THRESHOLD ≠ DEPLOYMENT_CONFIG`

`REPEATED_PRESENTATION ≠ REPLAY_VIOLATION`

`SECOND_PRESENTATION ≠ REPLAY_ATTACK`

`SINGLE_USE_POLICY ≠ ATOMIC_CONSUMPTION_IMPLEMENTATION`

`TEMPORAL_VALIDATION ≠ PRODUCER_AUTHORITY_VALIDATION`

`COMPLETE_PROVENANCE_CHAIN ≠ LEGITIMATE_GENESIS_AUTHORITY`

`EVIDENCE_FRESH ≠ EXECUTION_AUTHORIZED`

`REUSE_ALLOWED ≠ EXECUTION_AUTHORIZED`

---

## OUT_OF_SCOPE_v0.1

This design does not establish:

- production trusted-clock infrastructure
- clock synchronization guarantees
- cryptographic timestamping
- production freshness-policy storage
- production `WRITE_POLICY` enforcement for freshness state
- production evidence-use-policy storage
- replay-cache implementation
- single-use evidence implementation
- atomic consumption implementation
- cross-process consumption coordination
- persistent consumed-state storage
- production evidence revocation
- production evidence supersession
- clinical or domain-specific applicability semantics
- producer identity
- producer caller authorization
- legitimate genesis producer authority
- resistance to compromised-process execution
- production deployment readiness

---

## Explicit non-claims

This design does NOT prove that:

- any existing evidence artifact is currently fresh
- any existing evidence artifact is stale
- repeated presentation is malicious replay
- any evidence artifact is single-use
- any evidence artifact has already been consumed
- a trusted clock exists in the current prototype
- freshness policy is presently enforced
- reuse policy is presently enforced
- consumption is presently atomic
- producer authority has been validated

No executable G6 or G7 evidence exists yet.

---

## Design disposition

The next executable fixture MUST NOT be defined until the following are
frozen:

1. the freshness-policy representation
2. the trusted-current-time acquisition boundary
3. the applicable reuse policy
4. whether the candidate fixture concerns freshness or replay
5. the expected fail-closed behavior for unresolved temporal state

The dependency order is intentional.

The applicable reuse policy must be known before a repeated presentation
can be classified as legitimate reuse or replay violation.

Only after these semantics are frozen should a new executable regression
be named.

---

## Assurance statement

This document is a conceptual temporal-semantics design.

It establishes terminology, separations, governed-state requirements,
and future regression preconditions.

It does NOT establish executable temporal enforcement.

Current temporal assurance is therefore:

`DESIGN ONLY`

not:

`EXECUTABLY VALIDATED`

and not:

`PRODUCTION ENFORCED`

Re-issue of this design is required when the first freshness-policy
representation is frozen, the first trusted-time boundary is implemented,
or the first executable temporal fixture is named.
