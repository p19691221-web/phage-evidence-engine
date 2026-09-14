# PHAGE Trust Evidence Freshness Policy Representation Design v0.1

## Artifact status

Specification maturity: DESIGN FROZEN  
Executable validation: NOT STARTED  
Implementation maturity: NOT STARTED  
Production assurance: NOT ESTABLISHED  
Independent external review: NOT PERFORMED

Design status as of: 2026-09-14 / commit ref: ae667bd

Re-issue required upon: first executable freshness fixture named,
first trusted-time boundary implemented, or freshness-policy
representation materially changed.

This document freezes the conceptual representation of governed
Trust Evidence freshness policy.

It does not implement freshness evaluation, trusted time,
policy storage, WRITE_POLICY enforcement, or a G6 fixture.

---

## Parent design

This document refines the frozen temporal-semantics requirement:

`EVIDENCE_FRESHNESS_POLICY_IS_GOVERNED_STATE`

from:

`PHAGE_TRUST_EVIDENCE_TEMPORAL_SEMANTICS_DESIGN_v0_1.md`

The parent design already establishes:

`ORIGIN ≠ FRESHNESS`

`FRESHNESS ≠ REPLAY_POLICY`

`OBSERVED_AT ≠ TRUSTED_NOW`

`TEMPORAL_VALIDATION ≠ PRODUCER_AUTHORITY_VALIDATION`

Those distinctions remain unchanged.

---

## Existing open assumption

The Trust Evidence prototype still retains:

`ASSUMED_GENESIS_PRODUCER_AUTHORITY`

This freshness-policy representation does not authenticate or authorize
the producer.

Therefore:

`FRESHNESS_POLICY_VALIDATION ≠ PRODUCER_AUTHORITY_VALIDATION`

and:

`COMPLETE_PROVENANCE_CHAIN ≠ LEGITIMATE_GENESIS_AUTHORITY`

---

## Design objective

The freshness threshold MUST NOT be represented as an unmanaged constant
such as:

`MAX_EVIDENCE_AGE = 30 days`

without governed policy identity, version, and scope.

The representation must allow the system to answer:

1. which freshness policy applies
2. which policy version applies
3. what evidence scope the policy governs
4. what freshness window that policy defines
5. whether the policy is currently eligible for use
6. which governed source established that policy

Therefore:

`FRESHNESS_THRESHOLD ≠ UNGOVERNED_CONSTANT`

---

## EVIDENCE_FRESHNESS_POLICY_IS_GOVERNED_STATE

Freshness policy is governed state.

Creating, changing, revoking, replacing, or widening a freshness policy
is a policy mutation.

Such mutation is conceptually subject to applicable:

`WRITE_POLICY`

and self-authorization controls.

This document does not implement those controls.

Therefore:

`POLICY_REPRESENTATION ≠ WRITE_POLICY_ENFORCEMENT`

---

## Conceptual FreshnessPolicy representation

The minimal conceptual representation is:

`FreshnessPolicy`

with:

- `policy_id`
- `version`
- `scope`
- `max_age_seconds`
- `effective_from`
- `effective_until`
- `revoked`
- `revoked_at`
- `source_ref`

These fields define the policy object.

They do not themselves establish that the policy was legitimately
created or authorized.

---

## policy_id

`policy_id` identifies the logical freshness policy.

Example:

`evidence-freshness-clinical-lab`

The identifier MUST NOT silently encode the version.

Therefore:

`policy_id ≠ version`

---

## version

`version` identifies the governed policy version used for evaluation.

Example:

`v17`

A freshness result MUST be attributable to a specific policy version.

Therefore:

`FRESHNESS_RESULT_REQUIRES_POLICY_VERSION`

A result evaluated under:

`v17`

MUST NOT silently be treated as equivalent to:

`v18`

after policy mutation.

---

## scope

`scope` defines the evidence or decision context to which the freshness
policy applies.

The representation MUST make scope explicit.

The initial conceptual scope may identify dimensions such as:

- evidence kind or class
- producer class or producer reference, if governed
- decision context
- action class
- target class
- other explicitly governed context dimensions

The exact domain vocabulary is not frozen by this document.

However:

`MISSING_SCOPE ≠ GLOBAL_SCOPE`

and:

`UNKNOWN_SCOPE ≠ MATCH`

A policy MUST NOT silently widen merely because a scope dimension is
missing or unresolved.

---

## NO_SILENT_SCOPE_WIDENING

A freshness policy applies only where its governed scope is resolved.

Missing or ambiguous scope information MUST NOT be interpreted as:

`policy applies everywhere`

Therefore:

`NO_SILENT_SCOPE_WIDENING`

is a frozen invariant.

---

## max_age_seconds

`max_age_seconds` represents the maximum permitted evidence age under
the governed policy.

It is represented conceptually as a non-negative duration.

Example:

`2592000`

for a 30-day window.

The example does NOT establish a default freshness window.

There is no universal default in v0.1.

Therefore:

`NO_DEFAULT_FRESHNESS_WINDOW`

and:

`MAX_AGE_VALUE = GOVERNED_POLICY_STATE`

The caller MUST NOT choose this value for a particular evaluation.

---

## effective_from

`effective_from` defines when this policy version becomes eligible to
govern freshness evaluation.

It is policy state.

It is not evidence `observed_at`.

Therefore:

`POLICY_EFFECTIVE_FROM ≠ EVIDENCE_OBSERVED_AT`

---

## effective_until

`effective_until` optionally defines when this policy version ceases to
be eligible for new freshness evaluation.

A missing `effective_until` does NOT imply that all other policy
requirements are satisfied.

It only means that this representation does not define a fixed
end timestamp.

Policy revocation or supersession may still make the version
ineligible.

---

## revoked

`revoked` explicitly represents whether the governed policy version has
been revoked.

A revoked freshness policy MUST NOT produce a new positive freshness
determination.

This design does not yet define a separate policy-evaluation status
taxonomy.

---

## revoked_at

`revoked_at` records the governed revocation time when available.

It does not by itself establish trusted current time.

Therefore:

`POLICY_REVOKED_AT ≠ TRUSTED_NOW`

---

## source_ref

`source_ref` identifies the governed source or record from which this
policy representation derives.

Example forms may include:

- policy record reference
- governance decision reference
- institutional policy identifier

`source_ref` is lineage metadata.

It does NOT by itself establish authority.

Therefore:

`POLICY_SOURCE_REF ≠ POLICY_AUTHORITY_VALIDATED`

---

## Minimal conceptual object

Conceptually:

```text
FreshnessPolicy {
    policy_id
    version

    scope

    max_age_seconds

    effective_from
    effective_until

    revoked
    revoked_at

    source_ref
}
```

This is a conceptual representation.

It is not yet a production API or storage schema.

---

## Required representation fields

For a freshness policy to be usable for a deterministic freshness
evaluation, the initial design requires resolvable:

- `policy_id`
- `version`
- `scope`
- `max_age_seconds`
- `effective_from`
- `revoked`
- `source_ref`

`effective_until` and `revoked_at` may be absent only where their
semantics do not require a value.

Missing required policy representation MUST NOT silently yield:

`EVIDENCE_FRESH`

---

## Policy selection

Freshness evaluation requires selection of an applicable governed
policy.

Policy selection MUST NOT be caller preference.

Therefore:

`CALLER_SELECTED_FRESHNESS_POLICY ≠ GOVERNED_POLICY_SELECTION`

The caller may present context.

The caller may not make its preferred policy authoritative merely by
naming it.

---

## NO_AMBIGUOUS_POLICY_SELECTION

If the system cannot resolve which freshness policy applies, freshness
must remain unresolved.

Examples include:

- no applicable policy found
- multiple applicable policies with no frozen precedence rule
- policy scope cannot be resolved
- requested policy version does not exist
- applicable version cannot be determined

Therefore:

`AMBIGUOUS_POLICY_SELECTION → EVIDENCE_FRESHNESS_UNRESOLVED`

not:

`AMBIGUOUS_POLICY_SELECTION → EVIDENCE_FRESH`

---

## No implicit precedence rule

This design does NOT invent a precedence rule such as:

- newest version always wins
- shortest freshness window always wins
- longest freshness window always wins
- most specific policy always wins

A precedence rule, if later required, is itself governed semantics and
must be explicitly designed.

Therefore:

`POLICY_PRECEDENCE ≠ IMPLEMENTATION_GUESS`

---

## Policy version pinning

A freshness determination MUST identify the policy version under which
it was derived.

Conceptually a future freshness result should be able to carry at least:

- `policy_id`
- `policy_version`

This document does not freeze the full freshness-result schema.

It freezes only:

`FRESHNESS_POLICY_VERSION_MUST_BE_PINNED`

---

## Policy mutation after evaluation

An earlier freshness result derived under policy:

`P_n`

does not automatically remain valid after the governed policy state
changes to:

`P_n+1`

This document does not yet implement execution-time revalidation.

However:

`EARLIER_FRESHNESS_RESULT ≠ PERMANENT_FRESHNESS_AUTHORITY`

The temporal parent design's revalidation requirement remains open.

---

## Trusted time remains separate

This document freezes freshness-policy representation only.

It does not define the trusted-current-time acquisition mechanism.

Freshness evaluation still requires:

`TRUSTED_TIME_SOURCE_REQUIRED`

from the parent temporal design.

Therefore:

`VALID_FRESHNESS_POLICY ≠ TRUSTED_TIME_AVAILABLE`

and:

`POLICY_MAX_AGE ≠ CURRENT_TIME`

---

## observed_at remains separate

The current Trust Evidence Origin prototype content-binds:

`observed_at`

That does NOT make it trusted current time.

Nor does it prove that the original timestamp was truthful.

Therefore:

`OBSERVED_AT_CONTENT_BINDING ≠ TRUSTED_TIME_ATTESTATION`

Freshness evaluation requires both:

- evidence temporal information
- governed freshness policy
- trusted current time

No one element substitutes for the others.

---

## Initial freshness decision relation

Conceptually, later freshness evaluation may depend on:

```text
evidence.observed_at
+
trusted_current_time
+
FreshnessPolicy(policy_id, version, scope, max_age_seconds, ...)
```

to derive one of:

`EVIDENCE_FRESH`

`EVIDENCE_STALE`

`EVIDENCE_FRESHNESS_UNRESOLVED`

This document does NOT implement that evaluation.

---

## No stale-to-unverified collapse

Freshness policy MUST NOT rewrite historical origin status.

Therefore a future result may legitimately contain:

`EVIDENCE_ORIGIN_VERIFIED`

together with:

`EVIDENCE_STALE`

The following inference remains invalid:

`EVIDENCE_STALE → EVIDENCE_ORIGIN_UNVERIFIED`

---

## Freshness policy is not replay policy

`FreshnessPolicy`

does not determine whether evidence is:

- single-use
- reusable
- context-bound
- session-bound

Those belong to governed evidence-use policy.

Therefore:

`FRESHNESS_POLICY ≠ REUSE_POLICY`

This document does not satisfy the parent design's separate requirement
to freeze the applicable reuse policy before a replay fixture can be
defined.

---

## Policy mutation categories

The following are policy mutations:

- change `max_age_seconds`
- change scope
- widen scope
- narrow scope
- change effective period
- revoke policy
- restore or replace policy
- introduce a new version
- change any future precedence semantics

Such changes MUST NOT be treated merely as local configuration edits.

---

## Self-authorization warning

A party benefiting from an older or newer evidence interpretation MUST
NOT be able to change freshness policy merely to make its desired
evidence pass.

Therefore:

`EVIDENCE_CONSUMER ≠ AUTOMATIC_POLICY_AUTHORITY`

and:

`POLICY_BENEFICIARY ≠ SELF_AUTHORIZED_POLICY_WRITER`

Actual `WRITE_POLICY` enforcement remains outside this representation
design.

---

## Representation does not establish policy legitimacy

A perfectly formed `FreshnessPolicy` object does not prove:

- the issuer had authority
- the policy was institutionally approved
- the policy is legally valid
- the source is authentic
- the policy should be operationally preferred

Therefore:

`VALID_POLICY_SHAPE ≠ LEGITIMATE_POLICY_AUTHORITY`

This mirrors the existing producer-authority distinction:

`TRUSTED_PRODUCER_OUTPUT ≠ TRUSTED_PRODUCER_IDENTITY`

---

## Preserved distinctions

`FRESHNESS_POLICY ≠ FRESHNESS_RESULT`

`FRESHNESS_POLICY ≠ TRUSTED_TIME`

`FRESHNESS_POLICY ≠ REUSE_POLICY`

`POLICY_ID ≠ POLICY_VERSION`

`POLICY_SOURCE_REF ≠ POLICY_AUTHORITY_VALIDATED`

`VALID_POLICY_SHAPE ≠ LEGITIMATE_POLICY_AUTHORITY`

`CALLER_SELECTED_POLICY ≠ GOVERNED_POLICY_SELECTION`

`MISSING_SCOPE ≠ GLOBAL_SCOPE`

`UNKNOWN_SCOPE ≠ MATCH`

`POLICY_THRESHOLD ≠ DEPLOYMENT_CONFIG`

`POLICY_REPRESENTATION ≠ WRITE_POLICY_ENFORCEMENT`

`FRESHNESS_POLICY_VALIDATION ≠ PRODUCER_AUTHORITY_VALIDATION`

`TEMPORAL_VALIDATION ≠ PRODUCER_AUTHORITY_VALIDATION`

---

## Frozen invariants

This design freezes:

`EVIDENCE_FRESHNESS_POLICY_IS_GOVERNED_STATE`

`NO_DEFAULT_FRESHNESS_WINDOW`

`NO_SILENT_SCOPE_WIDENING`

`NO_AMBIGUOUS_POLICY_SELECTION`

`FRESHNESS_POLICY_VERSION_MUST_BE_PINNED`

`TRUSTED_TIME_SOURCE_REQUIRED`

These are design invariants.

They are not yet executable enforcement claims.

---

## OUT_OF_SCOPE_v0.1

This design does not establish:

- production freshness-policy storage
- production policy database schema
- production `WRITE_POLICY` enforcement
- production identity for policy writers
- institutional policy legitimacy
- policy-signature verification
- trusted-current-time implementation
- clock synchronization
- executable freshness evaluation
- execution-time freshness revalidation
- replay policy
- evidence consumption
- atomic evidence consumption
- production policy precedence
- production deployment readiness

---

## Explicit non-claims

This design does NOT prove that:

- any existing evidence is fresh
- any existing evidence is stale
- any particular freshness window is correct
- any particular policy currently applies
- any existing policy source is legitimate
- policy-writing authority has been validated
- a trusted clock currently exists
- freshness evaluation is implemented
- a G6 freshness fixture exists

No executable freshness-policy regression exists yet.

---

## Relationship to next temporal work

The parent temporal design requires the following before an executable
fixture is named:

1. freshness-policy representation
2. trusted-current-time acquisition boundary
3. applicable reuse policy
4. fixture classification: freshness or replay
5. unresolved-state fail-closed behavior

This document freezes item 1 only.

Items 2 through 5 remain open.

Therefore:

`FRESHNESS_POLICY_REPRESENTATION_FROZEN ≠ G6_READY`

---

## Design disposition

After this representation is frozen, the next temporal design task is:

`TRUSTED_CURRENT_TIME_ACQUISITION_BOUNDARY`

No executable G6 fixture should be named merely because the policy
representation now exists.

The trusted-time boundary must be designed next.

---

## Assurance statement

This document establishes only the conceptual representation and
governance requirements for Trust Evidence freshness policy.

Current assurance is:

`DESIGN ONLY`

not:

`EXECUTABLY VALIDATED`

and not:

`PRODUCTION ENFORCED`

Re-issue is required when:

- the first executable freshness fixture is named
- the trusted-time boundary is implemented
- the freshness-policy representation materially changes
