# H/H′ and N executable interface — review proposal v0.1

Status: REVIEW PROPOSAL, NOT FROZEN. Prepared 2026-10-05 (Asia/Taipei).
Semantic requirements: PR #91, effective merge
`1c67c47026ac5575e48b7d34f4c92be347e0b6ad`.
This draft fixes fixture representation; it does not modify that semantic contract.

## Entry and trusted seams

Module: `phage_authority_lineage_hhn_v0_1`.
Entry: `resolve_policy_change(*, request, authenticate, snapshot_provider, verify_grant)`.
No application callback, producer change, or runtime integration.

All seams must be callable. Authenticate is called once with requester_id and
returns exactly ESTABLISHED, NOT_ESTABLISHED, or VERIFICATION_ERROR.
Only ESTABLISHED permits snapshot_provider(), called once per resolution.
None means unavailable state. Exceptions/unexpected authentication outcomes
produce VERIFICATION_ERROR / AUTHORITY_VERIFICATION_ERROR / BLOCKED.
Trusted provider output is an explicit modeling assumption; caller flags do not
substitute for any seam. The provider owns trusted time and budget.

Request is a plain dict with exactly these nonempty string fields:
requester_id, policy_id, expected_revision, expected_digest, proposed_revision,
proposed_digest, operation, leaf_grant_id. Operation is POLICY_CHANGE.
Unsupported operations are scope violations. Extra fields are invalid authority
input. Proposed digest is an opaque fixture reference, not cryptographic evidence.

Snapshot is a plain dict with exactly snapshot_id, policy, grants, roots, at,
max_grants. snapshot_id is a nonempty string; at is an exact integer fixture time;
max_grants is an exact positive integer, excluding bool.
Policy contains policy_id, revision, digest, and mutable_by_policy_change (bool).
A false value protects roots, grant stores, and resolver configuration from this
entry. This protection is trusted state, not a requester classification.
Grants is a list of plain records; duplicate identifiers are invalid.
Roots maps root IDs to exact {revision, digest} trusted anchors.

Each grant contains id, revision, digest, subject, issuer, parent_id,
operations, targets, not_before, expires_at, revoked, can_delegate.
Identifiers/revisions/digests/subject/issuer are nonempty strings; parent_id is
None or a nonempty string. operations and targets are nonempty lists of unique
nonempty strings. not_before/expires_at are exact integer fixture times with
not_before < expires_at. revoked is bool or None (unknown); can_delegate is bool.
All current grants, including roots, undergo local checks. Unknown revocation
is unresolved. Missing required state fields are unresolved; present malformed
fields, extra fields and invalid vocabulary are invalid authority input.

verify_grant(record, at) is called once for each visited, structurally valid grant
before using its authority. Exactly VERIFIED proceeds, UNVERIFIED is unresolved,
and VERIFICATION_ERROR/unexpected results/exceptions are verification errors.
This seam validates trusted record acceptance only; issuer matching, delegation,
attenuation, root matching and cycles remain the resolver's own responsibility.
Do not pass live provider records: resolve against private copies; changes to
seam arguments must not change snapshot semantics or provider stores.

## Traversal, precedence and binding

Validate API argument types/callables first (TypeError, no seam calls). Plain
request shape errors return INVALID_AUTHORITY_INPUT before authentication.
Authenticate, acquire/validate snapshot, check exact policy identity/revision/
digest, then policy-change eligibility and operation, then traverse the leaf.
Within traversal: detect repeated ID, check budget, lookup/validate record,
verify_grant, check subject/issuer edges, local scope/revocation/time, then root
or parent delegation/attenuation. First decisive failure wins; fixtures isolate
conditions unless explicitly testing this order. No lookups after denial.

Budget counts distinct grant lookups, including root or missing-record lookup.
Cycle detection precedes budget: a repeated ID does not consume another lookup.
A chain of n grants succeeds with budget n, fails with n-1; exhausted budget
returns AUTHORITY_LIMIT_EXCEEDED before another lookup/verification.
Root mismatch is unresolved. Child scope/time expansion and absent parent
permission are scope violations. Child issuer equals parent's subject.

Result has exactly authorization_status, reason, effect_path, request_binding,
snapshot_id. The first three fields follow PR #91. On AUTHORIZED only,
request_binding is a tuple of the eight request fields in the order listed above,
and snapshot_id is the trusted snapshot ID; both are None for denial/error.
This is an inspection record, never a reusable approval token. A changed request
requires new resolution, even when proposed content is different but in scope.
Every call reacquires state; result bindings contain no mutable object references.
This does not establish atomic application or consumer-side enforcement.

## Validation scope

Tests are proposed RED acceptance tests. Absent module failures are surface RED,
not behavioral enforcement evidence. A subsequent stub/implementation sequence
must preserve semantic RED logs. No new workflow is introduced in this draft,
so merging it does not intentionally turn main CI red. Do not alter frozen
producer, L/M, G6, or CLAIMS_STATUS to make these tests pass.
