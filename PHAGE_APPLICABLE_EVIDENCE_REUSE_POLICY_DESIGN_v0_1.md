# PHAGE Applicable Evidence Reuse Policy — Design v0.1

STATUS: DESIGN FROZEN
## Standing State

TRUSTED_CURRENT_TIME_BOUNDARY_FROZEN
≠
G6_READY

APPLICABLE_EVIDENCE_REUSE_POLICY
→ DESIGN FROZEN

G6
→ NOT CREATED

No Python changes.
No G6 fixture yet.

---

## 1. WHAT MAY BE REUSED?

Only the exact, previously verified evidence bundle bound to a
verified evaluation record that produced a resolved APPLICABLE
evaluation may be considered for reuse.

The APPLICABLE status belongs to that prior evaluation result,
not to the evidence artifact itself, and reuse eligibility does
not transfer to another evidence bundle.

Evidence that contributed to an UNRESOLVED, CAPTURED, or
since-superseded-policy/schedule-version evaluation is not eligible
to enter reuse evaluation at all — it must be re-evaluated from
scratch, not reused.

### APPLICABLE_EVIDENCE_REUSE_INVARIANT

A prior APPLICABLE evaluation does not itself authorize reuse of
the evidence that contributed to it.

Evidence may be reused only when the system can establish that
every decision-relevant binding, dependency, origin, integrity,
and freshness condition required by the reuse policy still holds.

Missing, stale, unverifiable, changed, incomplete, or ambiguous
reuse conditions MUST NOT be interpreted as continued applicability.

### REUSE_EVIDENCE_BUNDLE_BINDING_INVARIANT

The evidence bundle presented for reuse MUST be the exact evidence
bundle bound to the original verified evaluation record whose
resolved APPLICABLE result makes reuse eligible for consideration.

A different evidence bundle MUST NOT inherit reuse eligibility merely
because it is independently verified, semantically equivalent, newer,
or bound to the same subject/action/target/scope.

"Exact evidence bundle" means the same verifiable artifact identity
bound to the original evaluation record, such as a verified artifact
reference or digest. It does NOT mean merely the same in-memory object
instance or semantically equivalent contents.

If the originally bound evidence bundle cannot be recovered and
verified, reuse is REUSE_UNRESOLVED.

This invariant MUST be satisfied before origin/integrity reverification.
Successful origin verification of a substitute bundle does not establish
that it is the bundle bound to the original evaluation.

### REUSE_ORIGIN_REVERIFICATION_INVARIANT

A candidate evidence artifact MUST have its origin and integrity
verified again at the point of reuse.

Prior successful verification does not substitute for verification
at the current enforcement-relevant consumption point.

Origin/integrity reverification occurs only after the exact original
evidence bundle identity has been established.

---

## 2. WHAT MUST REMAIN BOUND?

Equality of a resulting value or status is not, by itself, proof
that the underlying binding is unchanged.

The following must hold between the original evaluation and the
proposed reuse context, or reuse is not applicable:

- subject — same canonical resolved subject
- action — same canonical resolved action
- target — same canonical resolved target
- scope — same canonical resolved scope
- policy dependency set that participated in the original
  applicability derivation — unchanged and bound to the original
  verified evaluation record
- schedule dependency set that participated in the original
  applicability derivation — unchanged and subject to the same
  binding requirement
- authority derivation — unchanged
- evidence bundle — exact original artifact, reverified
- original observation time(s) — unchanged and bound to the original
  evidence artifact(s)

Subject/action/target/scope equality MUST be evaluated using the
canonical resolved bindings recorded by the original evaluation,
not caller-supplied labels, aliases, display names, literal values,
or reconstructed identifiers.

### REUSE_CONTEXT_BINDING_INVARIANT

Evidence established for one subject/action/target/scope context
MUST NOT be reused for a different context merely because its
semantic value is also APPLICABLE.

Context equality for this invariant MUST be evaluated using the
canonical resolved bindings recorded by the original verified
evaluation, not caller-supplied literal values, labels, aliases,
display names, or reconstructed identifiers.

If the original canonical bindings cannot be recovered and verified,
reuse is REUSE_UNRESOLVED.

If trusted resolution positively establishes that the current
canonical subject/action/target/scope differs from the original
bound context, reuse is REUSE_INVALIDATED.

Examples:

- APPLICABLE for READ record-A ≠ APPLICABLE for READ record-B
- APPLICABLE for actor-A ≠ APPLICABLE for actor-B

### REUSE_DEPENDENCY_BINDING_INVARIANT

The dependency set used for reuse evaluation MUST be the dependency
set bound to the original verified evaluation record.

A caller MUST NOT supply, remove, narrow, rewrite, or reconstruct
the dependency set for purposes of reuse.

If the original dependency set cannot be recovered and verified,
reuse is REUSE_UNRESOLVED.

A verified binding to a dependency set does not, by itself, prove
that the set is complete. Completeness is governed separately by
REUSE_DEPENDENCY_COMPLETENESS_INVARIANT.

### REUSE_AUTHORITY_DERIVATION_BINDING_INVARIANT

Reuse MUST NOT treat equality of an authority status value as proof
that the underlying authority derivation is unchanged.

The authority proof/derivation bound to the original evaluation
MUST be recovered and verified, including all relevant grant,
source, version, and lineage dependencies.

If the original authority derivation cannot be recovered and
verified, reuse is REUSE_UNRESOLVED.

If that derivation has been revoked, replaced, superseded, or
otherwise invalidated, reuse is REUSE_INVALIDATED.

A newly established authority path that happens to produce the
same authority status does not preserve eligibility to reuse the
old evidence bundle; it requires a fresh evaluation.

Example:

old authority path → CLEAN
new authority path → CLEAN

CLEAN == CLEAN
≠
same authority derivation

All reuse-time facts used to verify the current authority derivation
remain subject to REUSE_CURRENT_STATE_ACQUISITION_INVARIANT.

---

## 3. WHAT INVALIDATES REUSE?

A candidate reuse is REUSE_INVALIDATED when authoritative,
verified current-state resolution positively establishes any of
the following:

- any policy/version/dependency in the original complete and
  verified dependency closure has changed, been replaced, or
  been superseded;
- any schedule/version/dependency in that closure has changed,
  been replaced, or been superseded;
- any node or dependency in the original bound authority
  derivation has been revoked, expired, replaced, deleted,
  superseded, or otherwise invalidated;
- a bound grant has been revoked or expired;
- trusted current time has passed the effective reuse deadline;
- origin or integrity verification positively fails.

A candidate reuse is REUSE_UNRESOLVED, not REUSE_INVALIDATED,
when the system cannot obtain or verify enough authoritative
information to determine whether those conditions hold.

Invalidation is dependency-sensitive, not global.

An unrelated policy or schedule change does not by itself invalidate
reuse, provided that:

1. the original verified dependency closure is complete; and
2. the authoritative current state of that closure can be resolved.

The governing distinction is:

positive proof of invalidity
→ REUSE_INVALIDATED

absence of sufficient proof either way
→ REUSE_UNRESOLVED

never:
unknown → assume unchanged

### REUSE_CURRENT_STATE_ACQUISITION_INVARIANT

Every current-state fact used to determine reuse validity MUST be
resolved at reuse time through the authoritative trusted source for
that state.

Caller-supplied, reconstructed, or unverified cached representations
of current policy, schedule, authority, grant, revocation, or related
state MUST NOT satisfy a reuse check.

If authoritative current state cannot be obtained or verified,
reuse is REUSE_UNRESOLVED.

If authoritative current state positively establishes that a bound
dependency has changed, expired, been revoked, deleted, replaced, or
superseded, reuse is REUSE_INVALIDATED.

This is symmetric to the Trusted Current Time Boundary:

the reuse gate cannot ask the caller "what changed?"
any more than it can ask the caller "what time is it?"

### REUSE_DEPENDENCY_COMPLETENESS_INVARIANT

The dependency set bound to the original evaluation MUST represent
the complete decision-relevant dependency closure required to
establish that evaluation result.

Binding integrity alone is insufficient.

An intact but incomplete dependency set MUST NOT be treated as
sufficient for reuse.

If completeness of the original dependency closure cannot be
established according to the trusted evaluation mechanism, reuse
is REUSE_UNRESOLVED.

This is distinct from REUSE_DEPENDENCY_BINDING_INVARIANT:

- binding prevents substitution or narrowing after the fact;
- completeness requires the original trusted evaluation mechanism
  to have recorded the full decision-relevant dependency closure.

### REUSE MUST NOT EXTEND VALIDITY

Reusing evidence MUST NOT create a validity interval longer than
the original evidence or governed policy permits.

Reuse cannot refresh, renew, or reset an original observation time
merely by being reused.

This is the governing temporal principle.

REUSE_FRESHNESS_WINDOW_INVARIANT operationalizes this principle and
does not establish an independent or additional validity interval.

### REUSE_FRESHNESS_WINDOW_INVARIANT

Evidence reuse freshness is governed by its own bound:

MAX_EVIDENCE_REUSE_WINDOW

This value is governed policy state under WRITE_POLICY.

It is NOT implicitly identical to MAX_DECISION_VALIDITY_WINDOW or
any other decision-freshness bound unless a future design explicitly
and deliberately unifies them.

For a single freshness-bearing evidence artifact:

effective_reuse_deadline =
    min(
        original_evidence_valid_until,
        original_observed_at + MAX_EVIDENCE_REUSE_WINDOW
    )

If the original evidence validity bound required for reuse cannot
be recovered and verified, reuse is REUSE_UNRESOLVED.

Reuse becomes REUSE_INVALIDATED once newly acquired trusted current
time exceeds the effective reuse deadline.

For an evidence bundle containing multiple decision-relevant,
freshness-bearing evidence members:

- each member retains its own immutable original observation time;
- freshness MUST be evaluated for every decision-relevant member;
- a bundle-level timestamp MUST NOT refresh or mask an older member;
- the bundle reuse deadline MUST NOT exceed the earliest applicable
  member deadline.

Conceptually:

bundle_effective_reuse_deadline =
    earliest(
        effective deadline of every required freshness-bearing member
    )

This prevents two failure directions:

1. repeatedly reusing old evidence to create effectively permanent
   validity;
2. using a generous evidence reuse window to extend the validity of
   a decision or another independently governed artifact.

---

## 4. WHAT HAPPENS WHEN REUSE CANNOT BE PROVEN SAFE?

Reuse is never assumed by default.

REUSE_UNRESOLVED means the system lacks sufficient verified
information to determine whether reuse is safe.

REUSE_INVALIDATED means an authoritative condition positively
establishes that the prior evidence bundle is not eligible for reuse.

Neither status authorizes an effect.

A fresh evaluation may be attempted only when trusted workflow/policy
state permits it.

That fresh evaluation MUST be independent of the failed reuse path
and MUST satisfy the ordinary trusted acquisition, origin, integrity,
binding, completeness, and freshness requirements for a new evaluation.

The prior APPLICABLE result and the failed reuse candidate MUST NOT
be inherited as authorization or laundered into fresh evidence.

If a permitted fresh evaluation completes, its own deterministic
result — not the prior APPLICABLE result and not the reuse outcome —
controls the workflow.

If fresh evaluation is not permitted, cannot complete, or becomes
UNRESOLVED, the workflow fails closed and no effect may proceed.

REUSE_INVALIDATED ≠ final authorization denial.

It means only:

the old evidence cannot be reused.

A fresh evaluation may still establish applicability if trusted
workflow/policy permits it.

### REUSE_ALLOWED_IS_NOT_AUTHORIZATION

REUSE_ALLOWED means only that the previously verified evidence
bundle is eligible to be consumed by the current deterministic
evaluation.

REUSE_ALLOWED does NOT mean:

- the requested action is authorized;
- the prior APPLICABLE result remains current;
- a new APPLICABLE result has been established.

The current deterministic evaluation MUST still produce its own
decision.

### REUSE_FALLBACK_ISOLATION_INVARIANT

A fresh evaluation triggered after REUSE_UNRESOLVED or
REUSE_INVALIDATED MUST NOT inherit, re-admit, or reinterpret the
failed reuse candidate as fresh evidence merely by entering a new
evaluation path.

Any evidence used by the fresh evaluation MUST independently satisfy
the ordinary trusted acquisition, origin, integrity, freshness,
completeness, and binding requirements applicable to a new evaluation.

The prior APPLICABLE result, reuse eligibility, and reuse outcome
MUST NOT be treated as evidence for the fresh evaluation.

Fresh evaluation
≠
retry reuse under a different function name.

### REUSE_FALLBACK_GOVERNANCE_INVARIANT

Whether a fresh evaluation is permitted after a failed reuse attempt
MUST be determined by trusted workflow/policy state, not by the caller
or by the failed reuse candidate.

If fresh evaluation is not permitted, unavailable, or cannot be
completed, no effect may proceed on the basis of the prior
APPLICABLE evaluation.

The workflow MUST fail closed.

### REUSE_FALLBACK_TERMINATION_INVARIANT

A fresh evaluation entered as fallback from a failed reuse attempt
MUST NOT recursively re-enter reuse evaluation for the same prior
evaluation/evidence candidate.

Fallback processing MUST have a terminating, monotonic control path.

Detected fallback cycles or inability to establish termination
MUST fail closed.

---

## Core Invariants — Index

All invariants below are normative.

Their full text and rationale are defined at their single authoritative
location in Sections 1–4.

This index is not a second source of truth.

### Governing Principle

- APPLICABLE_EVIDENCE_REUSE_INVARIANT (§1)
  - a prior APPLICABLE result never grants reuse by itself

### Identity & Substitution Binding

- REUSE_EVIDENCE_BUNDLE_BINDING_INVARIANT (§1)
  - exact verified artifact identity must remain bound
- REUSE_CONTEXT_BINDING_INVARIANT (§2)
  - canonical resolved context, not caller literals
- REUSE_DEPENDENCY_BINDING_INVARIANT (§2)
  - caller cannot replace, narrow, rewrite, or reconstruct dependencies

### Derivation & Completeness

- REUSE_AUTHORITY_DERIVATION_BINDING_INVARIANT (§2)
  - same authority status is insufficient without the same valid derivation
- REUSE_DEPENDENCY_COMPLETENESS_INVARIANT (§3)
  - an intact dependency set must also be complete

### Trusted Acquisition & Verification

- REUSE_ORIGIN_REVERIFICATION_INVARIANT (§1)
  - applies only after exact bundle identity is established
- REUSE_CURRENT_STATE_ACQUISITION_INVARIANT (§3)
  - governs all reuse-time current-state facts, including authority,
    policy, schedule, grant, and revocation checks

### Temporal Bound

- REUSE MUST NOT EXTEND VALIDITY (§3)
  - governing temporal principle
- REUSE_FRESHNESS_WINDOW_INVARIANT (§3)
  - operationalizes the governing principle through the effective
    reuse deadline

### Output Semantics

- REUSE_ALLOWED_IS_NOT_AUTHORIZATION (§4)
  - reuse admission is not an authorization decision

### Fallback Control Flow

- REUSE_FALLBACK_ISOLATION_INVARIANT (§4)
- REUSE_FALLBACK_GOVERNANCE_INVARIANT (§4)
- REUSE_FALLBACK_TERMINATION_INVARIANT (§4)

---

## Reuse Evaluation Flow

```text
prior resolved APPLICABLE evaluation
        ↓
recover + verify the exact evidence bundle bound to that evaluation
(caller-supplied substitute rejected)
        ↓
recover + verify the original dependency set bound to that evaluation
(caller-supplied substitute/narrowed set rejected)
        ↓
establish dependency closure completeness
        ↓
verify evidence origin/integrity again
        ↓
acquire trusted current time
        ↓
resolve authoritative current state for all relevant dependencies
        ↓
verify canonical subject/action/target/scope bindings unchanged
        ↓
verify original authority derivation remains valid and unchanged
        ↓
verify policy/schedule/grant/dependency state remains valid
        ↓
verify trusted current time has not passed the effective reuse deadline
        ↓
REUSE_ALLOWED
        ↓
evidence admitted to current deterministic evaluation
        ↓
current deterministic evaluation
        ↓
current result controls
```

If any required fact cannot be affirmatively established:

```text
REUSE_UNRESOLVED
        ↓
fresh evaluation only if trusted workflow/policy permits
        ↓
otherwise fail closed
```

If an authoritative check positively proves invalidity:

```text
REUSE_INVALIDATED
        ↓
old evidence blocked from reuse
        ↓
fresh evaluation only if trusted workflow/policy permits
        ↓
otherwise fail closed
```

A fallback fresh evaluation MUST NOT recursively retry reuse of the
same failed candidate.

---

## Freeze Status

§1 — WHAT MAY BE REUSED?
→ FROZEN

§2 — WHAT MUST REMAIN BOUND?
→ FROZEN

§3 — WHAT INVALIDATES REUSE?
→ FROZEN

§4 — WHAT HAPPENS WHEN REUSE CANNOT BE PROVEN SAFE?
→ FROZEN

Core Invariants Index
→ FROZEN

APPLICABLE_EVIDENCE_REUSE_POLICY
→ DESIGN FROZEN

G6
→ NOT CREATED

Python
→ UNCHANGED

TRUSTED_CURRENT_TIME_BOUNDARY_FROZEN
≠
G6_READY
