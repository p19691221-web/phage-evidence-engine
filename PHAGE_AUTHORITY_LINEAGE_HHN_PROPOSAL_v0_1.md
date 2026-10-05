# PHAGE Authority Lineage H/H′ and N — proposal v0.1

Status: REVIEW PROPOSAL, NOT FROZEN.
Prepared: 2026-10-05 (Asia/Taipei).
Baseline inspected: main `6882afe459bf17802b4cd9d2537b88c950bedce0`.
Implementation / executable validation: NOT STARTED for this proposed contract.

## 1. Provenance and approval boundary

This is a new proposal. The original PHAGE_TRUST_BOUNDARY_INVARIANTS_v0_1
text remains unavailable. The L/M reconstructed specification retains only
historical descriptions of H/H′ and N; those descriptions do not supply frozen
acceptance criteria. This proposal does not restore or inherit that approval.

H concerns policy self-authorization; H′ is its independently authorized
positive control. N concerns cyclic authority lineage and fail-closed resolution.
Explicit review approval and merge may freeze the requirements below. Concrete
Python signatures and fixture representations must be specified in a subsequent
RED-test PR before implementation. No maturity promotion occurs through this PR.

Related inputs:

- PHAGE_TRUST_BOUNDARY_LM_RECONSTRUCTED_SPEC_v0_1.md
- PHAGE_PRODUCER_VERIFIER_CONTRACT_v0_2.md
- PHAGE_TRUST_BOUNDARY_PRODUCER_AUTHORITY_CONTRACT_v0_1.md
- REPO_GOVERNANCE.md and CLAIMS_STATUS.md

## 2. Scope and distinctions

The proposed resolver decides whether a verified requester has existing
fixture authority for one precisely bound policy-change request. It does not
apply that change or execute a tool. It does not establish institutional
legitimacy, cryptographic identity, or production authority.

Independent authorization means that the change's authority is derived from
pre-existing trusted state and an external root anchor, never from the proposed
policy or a grant supplied as a new fact by the requester. It does not require
a different human or subject to initiate every change: an already delegated
subject may request a change within its existing scope.

Evidence lineage (`lineage.py`) traverses supplied evidence dependencies; it
explicitly does not resolve authority. G6 fallback cycle detection is also a
separate contract. Neither substitutes for this resolver's N fixtures.
Producer contract v0.2 and L/M remain unchanged. This resolver is initially a
separate fixture entry, not a replacement producer verifier or runtime gate.

## 3. Trusted input boundary

Resolution receives one internally consistent, read-only fixture snapshot from
a replaceable trusted-state provider. It contains:

- authenticated requester context, or an explicit authentication outcome;
- target policy identifier and current revision/content digest;
- current authority grant records indexed by stable unique grant identifiers;
- externally configured root anchors binding root grant identifiers to exact
  revision/content digests;
- an explicit trusted evaluation time and positive traversal budget.

The snapshot and trusted time are modeling assumptions, not validated acquisition
mechanisms. A requester cannot provide or overwrite this trusted snapshot,
authentication outcome, root list, time, or traversal budget through the mutation
request. A plain dictionary bearing an `authenticated` or `trusted_root` flag
cannot establish those facts.

The request binds requester identity, exact target policy identifier, expected
current revision/digest, proposed revision/content digest, operation
`POLICY_CHANGE`, and the leaf grant identifier to be resolved. Payload integrity
and the binding of any approval result to this exact request must be preserved.
The proposed content carries no authority; it is not interpreted as an authority
source. No wildcard scope or alternate mutation operation is introduced in v0.1.

Root-anchor changes, grant creation/replacement, trusted-time configuration,
and changes to the resolver or its authorization rules are outside this entry's
allowed targets. Requests for them fail scope checks. They require a separate
future governance contract, not self-approval through POLICY_CHANGE.

## 4. Grant and delegation requirements

Each grant record has an identifier, revision/content digest, subject, issuer,
parent grant identifier (or no parent for an anchored root), allowed operation
set, exact target policy set, validity interval, and explicit revocation state.
Malformed, duplicate, ambiguous, or contradictory records do not confer authority.

Every resolved grant must:

- be supplied by the trusted snapshot, not accepted from request content;
- be valid at the trusted evaluation time: `not_before <= time < expires_at`;
- have an established current revocation state and be unrevoked;
- cover POLICY_CHANGE and the exact target policy;
- preserve the snapshot identity/revision of the record used in resolution.

The leaf subject must equal the authenticated requester. For each non-root
child, the child's issuer must equal its parent's subject. The parent must
explicitly permit delegation. Child operations and targets must be subsets of
its parent's scope; child validity must fit within the parent's validity interval.
No child may grant itself wider or longer authority than its parent.

A no-parent record terminates successfully only when its identifier and exact
revision/digest match an externally configured root anchor. A caller label,
issuer field, source_ref string, or a structurally complete chain alone cannot
establish an anchored root. Root legitimacy remains an external assumption.

## 5. Resolution and observable results

The entry returns three separate fields: `authorization_status`, `reason`, and
`effect_path`. Effect path is always BLOCKED for denial/error and NOT_DETERMINED
for successful fixture authorization. No result is an operational ALLOW.

| Condition | authorization_status | reason |
|---|---|---|
| Requester authentication not established | UNVERIFIED | AUTHENTICATION_NOT_ESTABLISHED |
| Authentication/provider/verifier exception or unexpected outcome | VERIFICATION_ERROR | AUTHORITY_VERIFICATION_ERROR |
| Expected policy revision/digest differs from trusted current state | UNVERIFIED | POLICY_STATE_MISMATCH |
| Missing grant, parent, root anchor, or required current state | UNVERIFIED | AUTHORITY_UNRESOLVED |
| Malformed/ambiguous request or grant record | UNVERIFIED | INVALID_AUTHORITY_INPUT |
| Requester, issuer/delegation, operation, target, or attenuation mismatch | UNVERIFIED | AUTHORITY_SCOPE_VIOLATION |
| Any resolved grant revoked | UNVERIFIED | AUTHORITY_REVOKED |
| Any resolved grant outside validity interval | UNVERIFIED | AUTHORITY_NOT_CURRENT |
| Repeated grant identifier on active resolution path | UNVERIFIED | AUTHORITY_CYCLE_DETECTED |
| Traversal budget exhausted before a verified root | UNVERIFIED | AUTHORITY_LIMIT_EXCEEDED |
| Exact request resolves through valid delegation to anchored root | AUTHORIZED | POLICY_CHANGE_AUTHORIZED |

Missing revocation state is unresolved, not unrevoked. Unsupported record
vocabulary is invalid input, not authorization. Provider absence is unresolved;
a provider exception or internal fault is a distinct verification error.
Raw verifier exceptions are not returned as authorization results. Concrete
invalid-API-argument behavior will be fixed by the RED interface proposal.

Authentication is a hard prerequisite: on denial/error, authority traversal
calls are zero. Check the expected current policy before traversing grants.
For each visited grant, apply cycle detection before dereferencing an already
visited identifier; check local validity and binding, then resolve its parent.
A self-loop, two-node cycle, or cycle reached below a valid prefix must terminate
with no authorization. Do not treat a visited node or depth limit as a root.
An earlier decisive failure may stop traversal; cyclic fixtures used to assert
N must have otherwise valid records so they isolate cycle behavior.

Each call resolves against a fresh consistent snapshot. No cached prior
AUTHORIZED outcome can replace current verification. If coherent snapshot
acquisition cannot be established, fail closed. Resolution does not claim atomic
application: a future applying consumer must bind and revalidate request and
snapshot at its protected-use boundary under a separately reviewed contract.

## 6. Side effects and failure containment

All resolution paths leave policies, grant stores, root anchors, and trusted
configuration unchanged. There is no policy-application callback in v0.1.
A success result is bound to the exact request and snapshot inspected; it must
not be reused as a bearer authorization token for a different mutation.

Verifier faults are observable separately from unverifiable authority. Fault
injection must use replaceable seams and demonstrate failure before authorization.
A later implementation's own programmer faults must not be counted as semantic
mutant detection without an assertion witness for the intended requirement.

## 7. Required RED and positive-control matrix

These are proposed acceptance requirements, not executed results.

| ID | Fixture | Required observation |
|---|---|---|
| H01 | Proposed policy declares its own requester authorized | UNVERIFIED; proposed declaration has no authority effect |
| H02 | Request includes a new grant or new root claim | Cannot establish authority absent trusted-state record |
| H03 | Change targets root anchors/grant store/resolver authorization rules | Scope violation; all stores unchanged |
| HP01 | Pre-existing leaf and valid delegated chain to anchored root | AUTHORIZED for exact bound request; no mutation applied |
| HP02 | Delegated requester initiates own in-scope change | May authorize; requester/initiator equality alone is not denial |
| A01 | Missing authentication, then authentication verifier fault | Separate denial/error; authority traversal zero |
| A02 | Missing leaf/parent/root/current revocation state | Unresolved; never authorized |
| A03 | Requester mismatch, issuer mismatch, missing delegation, scope/validity expansion | Scope violation for each isolated subcase |
| A04 | Revoked, not-yet-valid, expired; exact expiry boundary | Distinct fail-closed reason; valid interval positive control |
| A05 | Stale expected revision/digest or substituted policy/request | Reject; successful result cannot authorize changed request |
| N01 | Self-cycle | Cycle reason; finite traversal; unchanged state |
| N02 | Two-node cycle and cycle after acyclic prefix | Cycle reason; finite traversal; unchanged state |
| N03 | Valid anchored chain within budget | Positive control; no unconditional cycle rejection |
| N04 | Acyclic chain beyond budget | Explicit limit reason; no silent truncation or authorization |
| E01 | Provider/verifier raises; unsupported verifier result | VERIFICATION_ERROR; no authorization or state mutation |
| R01 | Repeat use after grant revoked or policy revision changed | New snapshot rechecked; prior success not reused |
| V01 | Malformed, duplicate, ambiguous records and caller trust flags | Fail closed without interpreting caller claims as trusted facts |

All negative controls must have a neighboring valid control so denial is not
mistaken for a working resolver. Assert visited-call bounds and unchanged stores.
Mutation tests should independently challenge root matching, cycle checks,
attenuation, hard-stop composition, fresh snapshots, and request binding; no
target detection ratio or previous mutant set is prescribed.

## 8. Change sequence and non-claims

1. Review this documentation-only proposal and resolve semantic disagreements.
2. Freeze through explicit approval/merge, with effective revision retained in PR history.
3. Review exact API, fixtures, replaceable seams and RED acceptance tests.
4. Retain behavioral RED evidence; implement isolated resolver without modifying frozen consumers.
5. Perform independent dynamic validation and review scope before any integration.

This proposal supplies no executable H/H′/N evidence. Even a later green fixture
resolver does not establish full G–N runtime closure, trusted state acquisition,
cryptographic provenance, institutional authority, concurrency-safe application,
production readiness, or pilot validation. CLAIMS_STATUS remains unchanged.
