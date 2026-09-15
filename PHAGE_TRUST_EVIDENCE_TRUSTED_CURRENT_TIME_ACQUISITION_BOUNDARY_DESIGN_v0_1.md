# PHAGE Trust Evidence Trusted Current Time Acquisition Boundary Design v0.1

## Artifact status

Specification maturity: DESIGN FROZEN  
Executable validation: NOT STARTED  
Implementation maturity: NOT STARTED  
Production assurance: NOT ESTABLISHED  
Independent external review: NOT PERFORMED

Design status as of: 2026-09-15 / commit ref: `eaa72cd`
Re-issue required upon: first trusted-time provider implementation,
first executable freshness fixture named, or material change to the
trusted-current-time acquisition boundary.

This document defines the conceptual boundary by which PHAGE Trust
Evidence freshness evaluation obtains authoritative current time.

It does not implement a production clock, time synchronization,
freshness evaluation, replay enforcement, or a G6 fixture.

---

## Parent designs

This document refines the frozen temporal requirement:

`TRUSTED_TIME_SOURCE_REQUIRED`

from:

`PHAGE_TRUST_EVIDENCE_TEMPORAL_SEMANTICS_DESIGN_v0_1.md`

and follows the frozen freshness-policy representation in:

`PHAGE_TRUST_EVIDENCE_FRESHNESS_POLICY_REPRESENTATION_DESIGN_v0_1.md`

Those parent designs already establish:

`ORIGIN ≠ FRESHNESS`

`OBSERVED_AT ≠ TRUSTED_NOW`

`VALID_FRESHNESS_POLICY ≠ TRUSTED_TIME_AVAILABLE`

`FRESHNESS_POLICY_REPRESENTATION_FROZEN ≠ G6_READY`

Those distinctions remain unchanged.

---

## Existing open assumptions

The Trust Evidence prototype still retains:

`ASSUMED_GENESIS_PRODUCER_AUTHORITY`

This trusted-time design does not authenticate or authorize the evidence
producer.

It also does not establish the ultimate institutional or cryptographic
legitimacy of any production time authority.

Therefore:

`TRUSTED_TIME_ACQUISITION ≠ PRODUCER_AUTHORITY_VALIDATION`

and:

`TIME_SOURCE_REFERENCE ≠ ULTIMATE_TIME_AUTHORITY_VALIDATED`

---

## Design objective

Freshness evaluation needs an authoritative value for current time.

That value MUST NOT be supplied by the caller whose evidence is being
evaluated.

The acquisition boundary must allow the verifier to answer:

1. where current time came from
2. whether the verifier obtained it through the trusted-time boundary
3. whether a canonical absolute instant was resolved
4. whether source selection was governed rather than caller-selected
5. whether time acquisition failed or remained unresolved

Therefore:

`CALLER_REPORTED_NOW ≠ TRUSTED_CURRENT_TIME`

---

## TRUSTED_CURRENT_TIME_ACQUISITION_BOUNDARY

Trusted current time is acquired through a verifier-controlled boundary.

Conceptually:

`freshness verifier → trusted-time provider → current-time observation`

The caller may supply evidence and context.

The caller MUST NOT supply the authoritative current-time value used to
decide freshness.

Therefore:

`CALLER_INPUT ≠ AUTHORITATIVE_NOW`

and:

`CALLER_SELECTED_TIME_SOURCE ≠ GOVERNED_TIME_SOURCE_SELECTION`

---

## No caller-supplied now

A public freshness-evaluation entry point MUST NOT accept a caller value
whose semantics are:

`authoritative_now`

and then treat that value as trusted merely because it was provided.

Caller timestamps may themselves be evidence.

They are not the verifier's authoritative clock.

Therefore:

`CALLER_TIMESTAMP ≠ VERIFIER_TRUSTED_NOW`

---

## Verifier-side acquisition

The verifier obtains current time from a trusted-time provider under its
own control boundary.

The exact production provider is not frozen here.

Possible future implementations may include:

- a protected operating-system time service
- an authenticated service-to-service time source
- a hardware-backed trusted-time source
- another explicitly governed trusted-time provider

This design does not claim that any one of these is presently
implemented or sufficient for all production environments.

---

## Conceptual TrustedCurrentTimeObservation

The minimal conceptual observation is:

`TrustedCurrentTimeObservation`

with:

- `time_value`
- `source_ref`
- `acquisition_ref`

These fields describe an acquired current-time observation.

They do not by themselves prove that the underlying time authority is
legitimate or uncompromised.

---

## time_value

`time_value` represents the resolved current instant used for freshness
evaluation.

It MUST be an absolute, timezone-aware instant.

The conceptual canonical form is UTC-equivalent time.

Therefore:

`LOCAL_CLOCK_LABEL ≠ TRUSTED_ABSOLUTE_INSTANT`

and:

`TIMEZONE_AMBIGUITY → TRUSTED_TIME_UNRESOLVED`

This document does not freeze a production serialization format.

---

## source_ref

`source_ref` identifies the trusted-time source or provider from which
the observation derives.

It is lineage metadata.

It does NOT by itself establish source legitimacy.

Therefore:

`TIME_SOURCE_REF ≠ TIME_SOURCE_AUTHORITY_VALIDATED`

---

## acquisition_ref

`acquisition_ref` identifies the specific acquisition event or provider
response used by the verifier.

Its purpose is auditability and binding of a freshness decision to the
time observation actually used.

It does not imply cryptographic attestation.

Therefore:

`ACQUISITION_REF ≠ CRYPTOGRAPHIC_TIME_ATTESTATION`

---

## Governed time-source selection

The source or provider eligible to supply authoritative current time is
governed state.

The caller MUST NOT select a weaker source merely because it makes
evidence appear fresh.

Therefore:

`TRUSTED_TIME_SOURCE_SELECTION_IS_GOVERNED_STATE`

and:

`TIME_SOURCE_SELECTION ≠ CALLER_PREFERENCE`

Changing the trusted-time source, source class, or source-selection rule
is a governance mutation.

Actual `WRITE_POLICY` enforcement for that mutation is NOT implemented
by this document.

---

## No silent fallback

If the governed trusted-time source is unavailable, the verifier MUST
NOT silently fall back to:

- caller-reported time
- evidence `observed_at`
- an unmanaged local clock
- an arbitrary secondary source
- a cached value with undefined validity

Therefore:

`TRUSTED_TIME_SOURCE_UNAVAILABLE → TRUSTED_TIME_UNRESOLVED`

and the frozen invariant is:

`NO_SILENT_TIME_SOURCE_FALLBACK`

A later governed specification may explicitly authorize a fallback
source and its selection semantics; absent such a specification,
no fallback is allowed.
---

## Trusted-time dispositions

The initial conceptual acquisition dispositions are:

`TRUSTED_TIME_RESOLVED`

`TRUSTED_TIME_UNRESOLVED`

### TRUSTED_TIME_RESOLVED

A verifier-controlled acquisition produced a canonical current-time
instant through the applicable governed trusted-time source.

### TRUSTED_TIME_UNRESOLVED

The verifier cannot safely resolve authoritative current time.

Examples include:

- trusted-time provider unavailable
- malformed provider response
- timezone or instant ambiguity
- governed source cannot be determined
- multiple eligible sources disagree with no governed reconciliation rule
- source response cannot be associated with an acquisition event

`TRUSTED_TIME_UNRESOLVED` MUST NOT silently become a current-time value.

---

## Unresolved time fails closed for freshness

If trusted current time is unresolved, freshness must remain unresolved.

Therefore:

`TRUSTED_TIME_UNRESOLVED → EVIDENCE_FRESHNESS_UNRESOLVED`

not:

`TRUSTED_TIME_UNRESOLVED → EVIDENCE_FRESH`

and not:

`TRUSTED_TIME_UNRESOLVED → EVIDENCE_STALE`

merely to force a binary answer.

---

## observed_at remains evidence time

The current Trust Evidence Origin prototype content-binds:

`observed_at`

That field remains evidence temporal information.

It is not authoritative current time.

Therefore:

`OBSERVED_AT ≠ TRUSTED_NOW`

and:

`OBSERVED_AT_CONTENT_BINDING ≠ TRUSTED_TIME_ATTESTATION`

A truthful or well-formed `observed_at` cannot replace verifier-side
current-time acquisition.

---

## No self-referential freshness

The freshness of evidence MUST NOT be decided by a current-time value
derived solely from that same evidence artifact.

Therefore:

`EVIDENCE_SUPPLIED_TIME ≠ AUTHORITATIVE_FRESHNESS_CLOCK`

This prevents the evidence under evaluation from self-declaring the
temporal reference used to judge itself.

---

## Canonical time comparison boundary

A later freshness evaluator may conceptually depend on:

```text
evidence.observed_at
+
TrustedCurrentTimeObservation.time_value
+
FreshnessPolicy.max_age_seconds
```

This design freezes only the acquisition boundary for the current-time
term.

It does NOT implement the freshness calculation.

---

## Future-dated evidence

If later freshness evaluation finds:

`evidence.observed_at > trusted_current_time`

that condition MUST NOT silently yield:

`EVIDENCE_FRESH`

The exact later disposition is not frozen here.

At minimum:

`FUTURE_OBSERVED_AT ≠ AUTOMATICALLY_FRESH`

A later freshness specification may classify this as unresolved or
otherwise fail closed.

---

## Multiple trusted-time sources

This design does not define a default precedence or reconciliation rule
for multiple eligible trusted-time sources.

It does NOT assume:

- newest source wins
- lowest timestamp wins
- highest timestamp wins
- local source wins
- remote source wins

Therefore:

`TIME_SOURCE_PRECEDENCE ≠ IMPLEMENTATION_GUESS`

If multiple sources disagree and no governed reconciliation policy
exists:

`TRUSTED_TIME_UNRESOLVED`

---

## No default clock-skew tolerance

This design does not invent a default acceptable clock-skew threshold.

If a future implementation permits disagreement within a tolerance, that
tolerance is governed policy state.

Therefore:

`NO_DEFAULT_CLOCK_SKEW_TOLERANCE`

and:

`CLOCK_SKEW_TOLERANCE ≠ UNGOVERNED_CONSTANT`

---

## Cached time observations

This design does not define cached trusted-time reuse.

A previously resolved time observation MUST NOT silently become
authoritative for an unlimited later period.

Therefore:

`EARLIER_TRUSTED_TIME ≠ PERMANENT_TRUSTED_NOW`

If caching is later introduced, cache-validity semantics must be
explicitly governed.

---

## Clock rollback and discontinuity

This design does not claim resistance to operating-system clock rollback,
synchronization jumps, leap-second handling, or compromised time
infrastructure.

A production implementation must define how material time discontinuity
is detected and handled.

Until such semantics exist:

`CLOCK_DISCONTINUITY ≠ SAFE_TO_IGNORE`

This document does not freeze a production discontinuity taxonomy.

---

## Source integrity and source authority remain separate

A verifier-controlled acquisition boundary is intended to prevent
the caller from choosing the authoritative value of `now`.
It does not by itself prove that the underlying time source is honest,
secure, or institutionally legitimate.

Therefore:

`VERIFIER_CONTROLLED_ACQUISITION ≠ TRUSTED_TIME_SOURCE_LEGITIMACY`

and:

`TIME_SOURCE_IDENTITY ≠ TIME_SOURCE_AUTHORITY`

Production source authentication and source-authority governance remain
outside this design.

---

## Temporal validation remains separate from authority

Even with:

`TRUSTED_TIME_RESOLVED`

and later:

`EVIDENCE_FRESH`

the system has not established authorization to act.

Therefore:

`TRUSTED_TIME_RESOLVED ≠ EXECUTION_AUTHORIZED`

`EVIDENCE_FRESH ≠ EXECUTION_AUTHORIZED`

Existing PHAGE distinctions remain:

`Assessment ≠ Authorization ≠ Execution`

---

## Execution-time revalidation remains open

An earlier trusted-time observation or freshness result does not
automatically survive until effect time.

Therefore:

`EARLIER_TRUSTED_TIME ≠ EFFECT_TIME_TRUSTED_TIME`

and:

`EARLIER_FRESHNESS_RESULT ≠ PERMANENT_FRESHNESS_AUTHORITY`

The execution-time temporal revalidation mechanism is NOT implemented by
this document.

---

## Preserved distinctions

`CALLER_REPORTED_NOW ≠ TRUSTED_CURRENT_TIME`

`CALLER_TIMESTAMP ≠ VERIFIER_TRUSTED_NOW`

`OBSERVED_AT ≠ TRUSTED_NOW`

`OBSERVED_AT_CONTENT_BINDING ≠ TRUSTED_TIME_ATTESTATION`

`TIME_SOURCE_REF ≠ TIME_SOURCE_AUTHORITY_VALIDATED`

`ACQUISITION_REF ≠ CRYPTOGRAPHIC_TIME_ATTESTATION`

`TIME_SOURCE_SELECTION ≠ CALLER_PREFERENCE`

`EARLIER_TRUSTED_TIME ≠ PERMANENT_TRUSTED_NOW`

`VALID_FRESHNESS_POLICY ≠ TRUSTED_TIME_AVAILABLE`

`TRUSTED_TIME_RESOLVED ≠ EXECUTION_AUTHORIZED`

`EVIDENCE_FRESH ≠ EXECUTION_AUTHORIZED`

`TRUSTED_TIME_ACQUISITION ≠ PRODUCER_AUTHORITY_VALIDATION`

`TIME_SOURCE_REFERENCE ≠ ULTIMATE_TIME_AUTHORITY_VALIDATED`

---

## Frozen invariants

This design freezes:

`TRUSTED_CURRENT_TIME_ACQUISITION_BOUNDARY`

`TRUSTED_TIME_SOURCE_REQUIRED`

`TRUSTED_TIME_SOURCE_SELECTION_IS_GOVERNED_STATE`

`NO_SILENT_TIME_SOURCE_FALLBACK`

`NO_DEFAULT_CLOCK_SKEW_TOLERANCE`

`CALLER_REPORTED_NOW ≠ TRUSTED_CURRENT_TIME`

These are design invariants.

They are not yet executable enforcement claims.

---

## OUT_OF_SCOPE_v0.1

This design does not establish:

- production trusted-time infrastructure
- authenticated network time
- hardware-backed trusted time
- operating-system clock integrity
- clock synchronization guarantees
- clock rollback resistance
- leap-second semantics
- production clock-skew reconciliation
- production time-source precedence
- production cache-validity semantics
- cryptographic time attestation
- production identity for time sources
- ultimate institutional time-source authority
- freshness evaluation implementation
- execution-time freshness revalidation
- replay policy
- evidence consumption
- production deployment readiness

---

## Explicit non-claims

This design does NOT prove that:

- a production trusted clock exists
- the current host clock is trustworthy
- any external time service is legitimate
- any current evidence is fresh
- any current evidence is stale
- freshness evaluation is implemented
- caller-controlled time is technically impossible in all code paths
- clock rollback is currently detected
- time-source compromise is currently resisted
- a G6 freshness fixture exists

No executable trusted-time regression exists yet.

---

## Relationship to next temporal work

The parent temporal design requires the following before an executable
fixture is named:

1. freshness-policy representation
2. trusted-current-time acquisition boundary
3. applicable reuse policy
4. fixture classification: freshness or replay
5. unresolved-state fail-closed behavior

The freshness-policy representation is already frozen.

This document freezes item 2 only.

Items 3 through 5 remain open.

Therefore:

`TRUSTED_CURRENT_TIME_BOUNDARY_FROZEN ≠ G6_READY`

---

## Design disposition

After this boundary is frozen, the next temporal design task is:

`APPLICABLE_EVIDENCE_REUSE_POLICY`

No executable G6 fixture should be named merely because trusted-current-
time acquisition semantics now exist.

The applicable reuse policy must be designed next.

---

## Assurance statement

This document establishes only the conceptual acquisition boundary and
governance requirements for trusted current time.

Current assurance is:

`DESIGN ONLY`

not:

`EXECUTABLY VALIDATED`

and not:

`PRODUCTION ENFORCED`

Re-issue is required when:

- the first trusted-time provider implementation is introduced
- the first executable freshness fixture is named
- the trusted-current-time acquisition boundary materially changes
