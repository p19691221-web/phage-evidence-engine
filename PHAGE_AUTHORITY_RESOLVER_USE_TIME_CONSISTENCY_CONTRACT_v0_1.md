# Authority resolver — use-time consistency contract revision v0.1

Status: REVIEW PROPOSAL, NOT FROZEN. Prepared 2026-10-08 (Asia/Taipei).
Baseline inspected: main `2e8ac147163d28e9fba423c34443c7bf8577b1c6`.
Revises: H/H′/N executable interface (PR #92, frozen) and its fixture
resolver (PR #93). Semantic requirements of PR #91 are retained.
Implementation / executable validation: NOT STARTED.

Sequence: spec review → contract freeze → RED tests → implementation → re-review.

## 1. Why a revision

PR #91 §5 left one item open by design: "a future applying consumer must bind
and revalidate request and snapshot at its protected-use boundary under a
separately reviewed contract." The DF-016 gate record (#95, §5) lists the same
item. This document is that contract. It also closes two bounded-work gaps in
the #93 resolver that a formal state source would expose:

- G-A: `expected_revision` / `expected_digest` equality is the only state
  check. Revision strings are opaque and digests are content-addressed, so an
  A→B→A change (policy, or a grant revoked then restored) is invisible.
- G-B: the structural preflight "does not consume traversal budget" and has no
  budget of its own. Request key sets and snapshot containers are scanned and
  copied without bound; a container shared by many records is expanded once
  per reference.

Frozen artifacts are not edited. v0.1 interface and module remain as the
provenance baseline. The revision lands as new files (§9).

## 2. Validity of an authorization result

Two results are distinguished:

| Result | Produced by | Consumable |
|---|---|---|
| Inspection AUTHORIZED | `resolve_policy_change` | Never |
| Use-time authorization | inside `commit_policy_change` only | Once, within that call |

Inspection AUTHORIZED keeps its #92 meaning: an inspection record bound to
one request and one snapshot. No entry accepts it as input. There is no
parameter through which a prior result, token, epoch or `valid_until` can be
supplied; such a keyword is a TypeError. This keeps the resolver outside the
Decision-origin problem (Trust Boundary L), which this contract does not solve.

A use-time authorization is valid only while all of the following hold, and
they are checked at the protected-use boundary defined below:

1. the request is byte-identical to the one resolved (bound copy, §5 of #92);
2. the authority state epoch equals the epoch of the snapshot resolved (§3);
3. trusted source time `now` satisfies `at <= now < valid_until`, where
   `valid_until = min(expires_at)` over every grant visited on the chain;
4. the commit has not already happened (single use; follows from 2, because a
   commit advances the epoch).

**Protected-use boundary** = the atomic step inside the state source that
writes the new policy revision. Checks 2 and 3 run inside that step, not
before it. A consumer that compares epochs and then writes is non-conforming:
the window between compare and write is the TOCTOU this contract removes.

## 3. Change and ABA detection: monotonic epoch, not lease

Decision: one monotonic `state_epoch` per authority state source.

- Scope: everything the resolver reads — policy records, all grant records,
  root anchors, and resolver-relevant configuration (`max_grants`).
- Any mutation in scope, including a revocation and including the commit
  performed by this contract, increases the epoch by at least 1.
- Epochs are exact integers ≥ 0, never decrease, never reused. A source
  restored from backup must resume above every epoch it previously issued
  (formal-source obligation; not fixture-testable, see §8).
- Coarse granularity is deliberate: an unrelated grant change invalidates an
  in-flight commit. Cost is a retry; the failure direction is closed.

Lease was evaluated and rejected for v0.2:

- A lease that does not block writers does not detect change during its term;
  ABA inside the term passes.
- A lease that does block writers is a lock. Revocation then cannot take
  effect until the lease expires, which contradicts the PR #14 mid-flight
  revocation guarantee.
- Either variant puts trusted-time agreement between holder and source on the
  critical path. The epoch puts only an integer comparison there.

Time still matters, as a freshness bound (`valid_until`, §2.3), not as the
consistency mechanism. Integration with governed
`MAX_DECISION_VALIDITY_WINDOW` is out of scope here; with re-resolution inside
the commit call, the window between read and write is the call's duration.

ABA coverage follows directly: digest equality may return to a prior value;
the epoch cannot.

### Detection points

| Point | Check | Result on failure |
|---|---|---|
| D1 snapshot read | `state_epoch` present, exact int ≥ 0 | missing → AUTHORITY_UNRESOLVED; malformed → INVALID_AUTHORITY_INPUT |
| D2 after traversal, before any AUTHORIZED | `current_epoch()` once; equal to snapshot epoch | greater → AUTHORITY_STATE_CHANGED; less → AUTHORITY_VERIFICATION_ERROR |
| D3 protected-use step | atomic `commit_if_epoch` | EPOCH_MISMATCH → AUTHORITY_STATE_CHANGED; NOT_CURRENT → AUTHORITY_NOT_CURRENT |

D2 means a resolution that observed a change never reports AUTHORIZED, even
though it ran on a private copy whose content was internally valid. The reason
reports what was detected (state moved), not what the new state contains: a
visited grant revoked mid-traversal yields AUTHORITY_STATE_CHANGED, not
AUTHORITY_REVOKED. D2 does not replace D3.

### Consumer enforcement

The use-time entry re-resolves itself; it never trusts a caller-held result:

```
commit_policy_change(*, request, authenticate, snapshot_provider,
                     current_epoch, verify_grant, commit_if_epoch)
  1. r = resolve(...)                      # full v0.2 resolution incl. D1, D2
  2. if r is not AUTHORIZED: return NOT_COMMITTED with r.reason, 0 commits
  3. outcome = commit_if_epoch(r.state_epoch, r.valid_until, r.request_binding)
  4. map outcome (below); commit_if_epoch called at most once, never retried
```

`commit_if_epoch(expected_epoch, valid_until, binding)` is a trusted source
seam. Atomically it compares epoch, compares trusted `now` against
`valid_until`, writes `proposed_revision` / `proposed_digest` to the bound
policy, and advances the epoch. Return values are exact strings:

| Seam outcome | commit_status | reason | effect_path |
|---|---|---|---|
| COMMITTED | COMMITTED | POLICY_CHANGE_COMMITTED | EFFECT_APPLIED |
| EPOCH_MISMATCH | NOT_COMMITTED | AUTHORITY_STATE_CHANGED | BLOCKED |
| NOT_CURRENT | NOT_COMMITTED | AUTHORITY_NOT_CURRENT | BLOCKED |
| TIME_REGRESSION | COMMIT_ERROR | AUTHORITY_VERIFICATION_ERROR | BLOCKED |
| exception / other value | COMMIT_OUTCOME_UNKNOWN | COMMIT_OUTCOME_UNKNOWN | NOT_DETERMINED |

An exception from the commit seam may follow a completed write. The entry
therefore does not retry, does not report BLOCKED, and does not report
COMMITTED. Recovery is a separate read of state, not a repeat of the change.
`TIME_REGRESSION` = source `now` earlier than the snapshot `at`.

Use-time result fields, exactly: `commit_status`, `reason`, `effect_path`,
`request_binding`, `committed_epoch`. `request_binding` and `committed_epoch`
are set only for COMMITTED.

## 4. Resource budgets

Three budgets, three distinct results. None is supplied by the request.

| Budget | Owner | Exceeded result |
|---|---|---|
| Request | resolver constants | REQUEST_LIMIT_EXCEEDED |
| Snapshot structure | resolver constants | SNAPSHOT_LIMIT_EXCEEDED |
| Traversal (`max_grants`) | trusted snapshot (unchanged) | AUTHORITY_LIMIT_EXCEEDED |

Snapshot structural limits are resolver constants, not provider-supplied: the
provider's data size is the quantity being bounded. Constants are module-level
and not overridable per call. Proposed values are review defaults:

```
REQUEST_MAX_KEYS          = 16
REQUEST_MAX_STRING_CHARS  = 256
SNAPSHOT_MAX_GRANTS       = 1024
SNAPSHOT_MAX_ROOTS        = 64
SNAPSHOT_MAX_SCOPE_ITEMS  = 64     # per operations / targets list
SNAPSHOT_MAX_STRING_CHARS = 256
SNAPSHOT_MAX_VISITS       = 65536
```

All results in this section have `authorization_status` UNVERIFIED,
`effect_path` BLOCKED.

### Request side

Checked before authentication; zero seam calls on exceedance.

1. `len(request) > REQUEST_MAX_KEYS` → REQUEST_LIMIT_EXCEEDED before any key
   is iterated.
2. Iterate keys (≤ 16): any non-`str` key → INVALID_AUTHORITY_INPUT
   (unchanged; no hashing of untrusted keys).
3. Any value with `type(v) is str and len(v) > REQUEST_MAX_STRING_CHARS` →
   REQUEST_LIMIT_EXCEEDED.
4. Remaining #92 shape rules (exact field set, nonempty strings).

Request visit count = keys examined + values examined; maximum 32. A 9–16 key
request with extra fields remains INVALID_AUTHORITY_INPUT, as in #92.

### Snapshot side

Checked in the first preflight, before copy and before any `verify_grant`.

Visit counting (normative): one visit for entering each container (snapshot
dict, policy dict, grants list, each grant dict, roots dict, each anchor dict,
each operations list, each targets list) and one visit for each key/value
pair or list element examined. The counter is checked before each visit;
the visit that would exceed `SNAPSHOT_MAX_VISITS` is not performed.

Cheap length checks run before iterating a container: `len(grants)`,
`len(roots)`, each scope list length, each string length.

Precedence: SNAPSHOT_LIMIT_EXCEEDED preempts INVALID_AUTHORITY_INPUT and
AUTHORITY_UNRESOLVED. Once a limit is hit the scan stops, so a later
malformation cannot be known; reporting limit exceedance is the only claim
the resolver can support.

The second preflight over the private copy and the copy itself are bounded by
the first preflight and do not draw on a second budget. Traversal budget is
unchanged and independent: N03/N04 semantics remain as frozen.
`max_grants` larger than the number of records is harmless, since cycle
detection bounds traversal by distinct identifiers.

### Shared references within schema depth

The snapshot schema has fixed depth (snapshot → grants → grant → scope list)
and no recursive definitions, so the only amplification is aliasing: one list
or dict object referenced from several places.

- Aliasing within schema is legal input, not malformation.
- Budget is charged per expansion (per reference path), not per distinct
  object. The resolver does not memoize by object identity, because the copy
  materializes each expansion and the budget must bound that work.
- The private copy contains no aliasing: a `verify_grant` mutation of one
  copied record's list cannot appear in another record.
- A container that contains itself fails the element predicate (its element is
  not a `str`) and is INVALID_AUTHORITY_INPUT; the scan never recurses into it.

## 5. Revised resolution order

```
0  API types / callables                         → TypeError, no seam call
1  request budget                                → REQUEST_LIMIT_EXCEEDED
2  request shape (#92)                           → INVALID_AUTHORITY_INPUT
3  authenticate (#92)
4  snapshot_provider(); None                     → AUTHORITY_UNRESOLVED
5  preflight with snapshot budget                → SNAPSHOT_LIMIT_EXCEEDED
                                                   > malformed > missing
6  private copy; preflight of copy
7  traversal (#92 order, traversal budget)
8  D2 current_epoch() check (only if 7 authorized)
9  AUTHORIZED with state_epoch, valid_until
```

Inspection result fields, exactly: `authorization_status`, `reason`,
`effect_path`, `request_binding`, `snapshot_id`, `state_epoch`,
`valid_until`. The last four are None except on AUTHORIZED. Snapshot schema
adds exactly one required field, `state_epoch`. `current_epoch` is called
once per resolution, only at step 8; exceptions or non-int returns →
AUTHORITY_VERIFICATION_ERROR.

## 6. New reason codes

| Reason | authorization_status | Distinct from |
|---|---|---|
| AUTHORITY_STATE_CHANGED | UNVERIFIED | POLICY_STATE_MISMATCH = requester's expectation is wrong; this = state moved under a correct expectation |
| REQUEST_LIMIT_EXCEEDED | UNVERIFIED | INVALID_AUTHORITY_INPUT = shape; this = size |
| SNAPSHOT_LIMIT_EXCEEDED | UNVERIFIED | AUTHORITY_LIMIT_EXCEEDED = delegation depth |

Use-time-only codes: POLICY_CHANGE_COMMITTED, COMMIT_OUTCOME_UNKNOWN.

## 7. Acceptance cases (RED targets)

Fixture state source: in-memory store with an epoch counter; every mutator
advances it; exposes `snapshot_provider`, `current_epoch`, `commit_if_epoch`,
and a test hook that runs between resolution and the commit step.

Mid-change
- C01 Mutation of an unrelated grant fired from inside `verify_grant` →
  AUTHORITY_STATE_CHANGED, BLOCKED; source unchanged by the resolver.
- C02 Visited leaf revoked from inside `verify_grant` → AUTHORITY_STATE_CHANGED
  (not AUTHORITY_REVOKED).
- C03 Leaf revoked by the pre-commit hook → NOT_COMMITTED /
  AUTHORITY_STATE_CHANGED; policy unchanged; failed commit does not advance
  the epoch.
- C04 Positive control: no change → COMMITTED; epoch +1; exactly one
  `commit_if_epoch` call; `committed_epoch` = new epoch.

ABA
- C05 Policy p1→p2→p1 with identical digest in the pre-commit hook; request's
  expected revision/digest match current → NOT_COMMITTED /
  AUTHORITY_STATE_CHANGED.
- C06 Leaf revoked then restored (False→True→False) in the pre-commit hook →
  NOT_COMMITTED / AUTHORITY_STATE_CHANGED.
- C07 Resubmitting the identical request after C04 → POLICY_STATE_MISMATCH;
  zero commit calls (single use).
- C08 `current_epoch` returns less than snapshot epoch →
  AUTHORITY_VERIFICATION_ERROR.
- C09 `state_epoch` missing → AUTHORITY_UNRESOLVED; `True`, `-1`, `'3'`, `3.0`
  → INVALID_AUTHORITY_INPUT.

Use-time freshness and outcome
- C10 Source `now >= valid_until` at commit → NOT_COMMITTED /
  AUTHORITY_NOT_CURRENT; `valid_until` equals the minimum chain `expires_at`
  (fixture: intermediate expires earlier than leaf and root).
- C11 Commit seam raises → COMMIT_OUTCOME_UNKNOWN, NOT_DETERMINED, one call,
  no retry.
- C12 Passing any prior result / epoch / valid_until keyword to either entry
  → TypeError before any seam call.

Budget, both sides
- B01 `len(request) = 17` → REQUEST_LIMIT_EXCEEDED, zero seam calls.
  `len = 9` with an extra field → INVALID_AUTHORITY_INPUT (regression).
- B02 Field of 256 chars passes; 257 → REQUEST_LIMIT_EXCEEDED, zero seam
  calls.
- B03 1025 grants → SNAPSHOT_LIMIT_EXCEEDED, zero `verify_grant` calls, even
  when grant 1 is malformed and another is missing a field.
- B04 Snapshot whose normative visit count is exactly 65536 passes preflight;
  65537 → SNAPSHOT_LIMIT_EXCEEDED. Test helper computes the count from §4.
- B05 Snapshot string of 257 chars, and scope list of 65 items →
  SNAPSHOT_LIMIT_EXCEEDED.
- B06 Request and snapshot both over limit → REQUEST_LIMIT_EXCEEDED;
  `snapshot_provider` and `authenticate` never called.
- B07 Traversal limit unchanged: N03/N04 still return
  AUTHORITY_LIMIT_EXCEEDED, never SNAPSHOT_LIMIT_EXCEEDED.

Shared references within schema depth
- S01 One `targets` list object shared by K grants, expanded count under
  budget → result identical to the unaliased fixture.
- S02 `verify_grant` mutates its record's `targets`; the next visited record
  sharing that list in the source sees the original value; source object
  unchanged.
- S03 Shared list whose distinct-object size is under budget but whose
  expanded count exceeds it → SNAPSHOT_LIMIT_EXCEEDED.
- S04 One anchor dict shared by two root IDs → legal; charged twice.
- S05 `targets` list containing itself → INVALID_AUTHORITY_INPUT; runs in a
  disposable subprocess with a 5 s wall-clock timeout (N-test pattern).

All v0.1 tests are carried forward with `state_epoch` added to fixtures and a
fixture `current_epoch`; their expected results do not change.

## 8. Non-claims

- No production state backend, database CAS, distributed consensus, or
  replication semantics. The fixture source models them.
- Epoch non-reuse across restart/restore is a formal-source obligation, not
  validated here.
- Trusted time remains a modeling assumption (see
  PHAGE_TRUST_EVIDENCE_TRUSTED_CURRENT_TIME_ACQUISITION_BOUNDARY_DESIGN_v0_1).
- COMMITTED means the fixture source applied a policy revision. It is not
  runtime enforcement closure, Gateway integration, or tool-effect binding.
- No DF-016 machinery is reused; the #95 record stands unchanged.
- No CLAIMS_STATUS change and no maturity promotion through this PR.
- Principle 0 non-`str` / `str`-subclass hook gap is a separate small fix
  line. Pilot remains gated on external Problem Adoption.

## 9. Delivery

- This PR: this document only.
- Freeze PR: `PHAGE_AUTHORITY_LINEAGE_HHN_EXECUTABLE_INTERFACE_v0_2.md` with the
  frozen constants and exact signatures.
- RED PR: `test_phage_authority_lineage_hhn_v0_2.py`,
  `test_phage_authority_protected_use_v0_1.py`; surface RED vs semantic RED
  recorded separately.
- Implementation PR: `phage_authority_lineage_hhn_v0_2.py`,
  `phage_authority_protected_use_v0_1.py`. v0.1 module untouched.

## 10. Review questions

- Q1 Global epoch vs per-record read set (precise, larger surface). Proposed:
  global for v0.2.
- Q2 AUTHORITY_STATE_CHANGED as a new code vs reusing POLICY_STATE_MISMATCH.
  Proposed: new, to keep "requester wrong" and "state moved" separable.
- Q3 Numeric budget values.
- Q4 Whether the inspection entry should keep reporting AUTHORIZED, given it is
  never consumable. Proposed: keep, for #92 continuity.
