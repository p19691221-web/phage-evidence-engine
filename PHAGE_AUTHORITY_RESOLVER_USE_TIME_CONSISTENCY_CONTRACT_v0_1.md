# Authority resolver — use-time consistency contract revision v0.1

Status: REVIEW PROPOSAL rev 3, NOT FROZEN. Prepared 2026-10-08, revised
2026-10-09 (Asia/Taipei).
Baseline inspected: main `2e8ac147163d28e9fba423c34443c7bf8577b1c6`.
Revises: H/H′/N executable interface (PR #92, frozen) and its fixture
resolver (PR #93). Semantic requirements of PR #91 are retained.
Implementation / executable validation: NOT STARTED.

Sequence: spec review → contract freeze → RED tests → implementation → re-review.

## 0. Revision log

rev 2 closes four review gaps in rev 1:

| Gap | rev 1 defect | rev 2 location |
|---|---|---|
| R1 | Commit seam had no `snapshot_at`, so TIME_REGRESSION was undefined; `committed_epoch` had no source | §3.3, §3.4 |
| R2 | "Single use follows from epoch advance" was stated without scope; read as request-level replay protection | §4 |
| R3 | Preflight traversal could call hooks on non-exact types; visit counting and limit/malformed precedence were order-dependent | §5 |
| R4 | Atomic rejection did not require zero writes; mixed seam failures had no precedence; write-then-raise untested | §3.4, §3.5, §6, §8 |

rev 3 closes three review findings on rev 2:

| Gap | rev 2 defect | rev 3 location |
|---|---|---|
| R5 | No obligation tying snapshot content to its `state_epoch` label; a label newer than its content is undetectable and was not stated | §3.6, §6, §8 O01–O04, §9 |
| R6 | Key gate was per key, so lookups or hashing on a dict could run while another key of the same dict was still ungated (hash-collision `__eq__` path) | §5.2 S-4, §5.5, §8 T04–T05 |
| R7 | P03 required TIME_REGRESSION and NOT_CURRENT together, which `snapshot_at < valid_until` makes unreachable | §3.3, §6, §8 P03 |

Q1 resolved: global epoch for v0.2 (reviewer approved).

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

Frozen artifacts are not edited. The v0.1 interface and module remain as the
provenance baseline. The revision lands as new files (§10).

## 2. Validity of an authorization result

| Result | Produced by | Consumable |
|---|---|---|
| Inspection AUTHORIZED | `resolve_policy_change` | Never |
| Use-time authorization | inside `commit_policy_change` only | By the one `commit_if_epoch` call in the same entry invocation |

Inspection AUTHORIZED keeps its #92 meaning: an inspection record bound to one
request and one snapshot. No entry accepts it as input. Neither entry has a
parameter through which a prior result, token, epoch, `snapshot_at` or
`valid_until` can be supplied; such a keyword is a TypeError raised before any
seam call. This keeps the resolver outside the Decision-origin problem (Trust
Boundary L), which this contract does not solve.

A use-time authorization is valid only while all of the following hold. They
are checked at the protected-use boundary:

1. the request is identical to the bound copy resolved (#92 §5);
2. the source epoch equals the epoch of the snapshot resolved (§3);
3. trusted source time `now` satisfies `snapshot_at <= now < valid_until`,
   where `snapshot_at` is the snapshot's `at` and
   `valid_until = min(expires_at)` over every grant visited on the chain.

`now >= snapshot_at` is what keeps every visited grant's `not_before` satisfied
at commit time (resolution established `not_before <= at`). `now < valid_until`
keeps every `expires_at` satisfied. Revocation and every other content change
are covered by condition 2.

**Protected-use boundary** = the atomic step inside the state source that
writes the new policy revision. Conditions 2 and 3 are checked inside that
step, not before it. A consumer that compares epochs and then writes is
non-conforming: the window between compare and write is the TOCTOU this
contract removes.

## 3. Change and ABA detection: monotonic epoch

### 3.1 Epoch

One monotonic `state_epoch` per authority state source.

- Scope: everything the resolver reads: policy records, all grant records,
  root anchors, and resolver-relevant configuration (`max_grants`).
- Any mutation in scope, including a revocation and including a commit made
  under this contract, increases the epoch by at least 1.
- Epochs are exact integers ≥ 0, never decrease, are never reused. A source
  restored from backup must resume above every epoch it previously issued
  (formal-source obligation; not fixture-testable, see §9).
- Coarse granularity is deliberate: an unrelated grant change invalidates an
  in-flight commit. The cost is a retry; the failure direction is closed.

Lease was evaluated and rejected for v0.2:

- A lease that does not block writers does not detect change during its term;
  ABA inside the term passes.
- A lease that blocks writers is a lock. Revocation could then not take effect
  until expiry, which contradicts the PR #14 mid-flight revocation guarantee.
- Either variant puts holder/source trusted-time agreement on the consistency
  path. The epoch puts an integer comparison there.

Time remains a freshness bound (§2 condition 3), not the consistency
mechanism. Integration with governed `MAX_DECISION_VALIDITY_WINDOW` is out of
scope.

ABA coverage: a digest may return to a prior value; the epoch cannot.

### 3.2 Detection points

| Point | Check | Result on failure |
|---|---|---|
| D1 snapshot preflight | `state_epoch` present, exact int, `0 <= e`, bit length ≤ 64 | missing → AUTHORITY_UNRESOLVED; non-int or negative → INVALID_AUTHORITY_INPUT; bit length > 64 → SNAPSHOT_LIMIT_EXCEEDED |
| D2 after traversal authorizes, before AUTHORIZED is returned | `current_epoch()` once; must equal snapshot epoch | greater → AUTHORITY_STATE_CHANGED; less → AUTHORITY_VERIFICATION_ERROR; exception / not exact int → AUTHORITY_VERIFICATION_ERROR |
| D3 protected-use step | atomic `commit_if_epoch` (§3.3) | see §3.4 |

D2 runs only on the path where traversal would authorize. A denial is not
re-checked against current state: `current_epoch` is called zero times on
denial. A denial from a stale snapshot is fail-closed and is not claimed to
describe current state.

D2 reports what was detected (state moved), not what the new state contains:
a visited grant revoked mid-traversal yields AUTHORITY_STATE_CHANGED, not
AUTHORITY_REVOKED. D2 narrows the window; it does not replace D3.

### 3.3 Commit seam

```
commit_if_epoch(*, expected_epoch, snapshot_at, valid_until, binding)
    -> {"outcome": str, "committed_epoch": int | None}
```

Arguments are supplied by the entry, never by the caller:
`expected_epoch` = snapshot `state_epoch`; `snapshot_at` = snapshot `at`;
`valid_until` = §2 minimum; `binding` = the eight-field request tuple.

Atomic step, normative for the reference fixture source and an obligation on
any formal source:

```
1  now := trusted source time
2  if now < snapshot_at          -> TIME_REGRESSION   (no write)
3  if epoch != expected_epoch    -> EPOCH_MISMATCH    (no write)
4  if now >= valid_until         -> NOT_CURRENT       (no write)
5  set policy[binding.policy_id] revision/digest := binding.proposed_*
   epoch := new value > expected_epoch
   -> COMMITTED, committed_epoch := new epoch
```

Steps 1–4 perform no write. Steps 1–5 are one atomic section with respect to
every other mutator of the source.

**Zero-write rejection.** For TIME_REGRESSION, EPOCH_MISMATCH and NOT_CURRENT,
the source after the call equals the source before it: policy, all grants, root
anchors, configuration, and epoch. No partial write, no epoch advance, no
mutation log entry counted as a write.

**Precedence inside the seam** is the step order above. Only two pairs can
co-occur:

- TIME_REGRESSION with EPOCH_MISMATCH → TIME_REGRESSION. A trusted-time fault
  is a verification error and is reported before any state or freshness
  result.
- EPOCH_MISMATCH with NOT_CURRENT → EPOCH_MISMATCH. A moved epoch removes the
  authorization basis regardless of time.

TIME_REGRESSION and NOT_CURRENT are mutually exclusive. Resolution requires
`at < expires_at` for every visited grant, so every AUTHORIZED result has
`snapshot_at < valid_until`. Then `now < snapshot_at` implies
`now < valid_until`. The entry checks `snapshot_at < valid_until` before
calling the seam; if it fails (an internal fault, unreachable under a correct
resolver), the seam is not called and the result is COMMIT_ERROR /
AUTHORITY_VERIFICATION_ERROR / BLOCKED. That guard is an implementation
assertion, not an acceptance case.

### 3.4 Use-time entry

```
commit_policy_change(*, request, authenticate, snapshot_provider,
                     current_epoch, verify_grant, commit_if_epoch)
  1. r := v0.2 resolution (§6), including D1 and D2
  2. if r is not AUTHORIZED: return per §6 table; commit_if_epoch never called
  3. raw := commit_if_epoch(expected_epoch=r.state_epoch,
                            snapshot_at=r.snapshot_at,
                            valid_until=r.valid_until,
                            binding=r.request_binding)
  4. validate raw and map (below)
  5. return; no further seam call, no retry, no read-back
```

Return validation. `raw` is well-formed only if all hold:
`type(raw) is dict`; `len(raw) == 2`; the whole-dict key gate (§5.2 S-4)
passes; its key set is then exactly `{outcome, committed_epoch}`; `type(outcome) is str` and
in the vocabulary; for COMMITTED, `committed_epoch` is an exact int (not bool)
with `committed_epoch > expected_epoch`; for every other outcome,
`committed_epoch is None`.

| Seam result | commit_status | reason | effect_path |
|---|---|---|---|
| well-formed COMMITTED | COMMITTED | POLICY_CHANGE_COMMITTED | EFFECT_APPLIED |
| well-formed EPOCH_MISMATCH | NOT_COMMITTED | AUTHORITY_STATE_CHANGED | BLOCKED |
| well-formed NOT_CURRENT | NOT_COMMITTED | AUTHORITY_NOT_CURRENT | BLOCKED |
| well-formed TIME_REGRESSION | COMMIT_ERROR | AUTHORITY_VERIFICATION_ERROR | BLOCKED |
| exception, or any malformed return | COMMIT_OUTCOME_UNKNOWN | COMMIT_OUTCOME_UNKNOWN | NOT_DETERMINED |

A seam exception or malformed return gives no evidence about whether step 5
ran. The entry therefore reports neither BLOCKED nor COMMITTED, does not
retry, and does not read state back to find out. Recovery is a separate read
by the caller, not a repeat of the change.

Use-time result fields, exactly: `commit_status`, `reason`, `effect_path`,
`request_binding`, `committed_epoch`. `request_binding` and `committed_epoch`
are set only for COMMITTED; `committed_epoch` is the seam's validated value.

### 3.5 Seam call counts per `commit_policy_change`

| Seam | Calls |
|---|---|
| authenticate | 0 if request rejected, else 1 |
| snapshot_provider | 0 unless authentication ESTABLISHED, else 1 |
| verify_grant | one per visited grant, 0 if preflight fails |
| current_epoch | 1 only if traversal authorizes, else 0 |
| commit_if_epoch | 1 only if resolution AUTHORIZED, else 0 |

No seam is called after `commit_if_epoch` returns or raises.

### 3.6 Snapshot / epoch consistency obligations

The epoch checks compare labels. They are sound only if each label describes
the content it is attached to. These are obligations on the state source. The
resolver cannot verify them; it can only show which violations fail closed.

- **O1 Atomic snapshot.** `snapshot_provider()` returns content and
  `state_epoch` from one read that is atomic with respect to every mutator in
  epoch scope. The content equals source state at exactly that epoch. No torn
  reads: no record from before a mutation together with a record from after
  it.
- **O2 One counter.** `snapshot_provider`, `current_epoch` and
  `commit_if_epoch` read and advance the same epoch counter of the same
  source. A replica, cache or second source behind any one of them violates
  O2.
- **O3 Snapshot time.** `at` is trusted source time taken within the O1 read.
  `commit_if_epoch` reads `now` from the same trusted time source.
- **O4 Epoch scope coverage.** Every write to anything the resolver reads
  advances the epoch in the same atomic section as the write (restates §3.1 as
  a source obligation).

Effect of an O1 violation, by direction:

| Violation | Example | Detected | Outcome |
|---|---|---|---|
| Label older than content | content at E+1, label E, current E+1 | Yes, D2 | AUTHORITY_STATE_CHANGED (spurious, fail-closed) |
| Label newer than content | content at E−1, label E, current E | No | Commit may succeed on stale content |
| Mixed content | half at E−1, half at E, label E | No | Commit may succeed on content that never existed |

The second and third rows are why O1 is load-bearing. No check inside the
resolver or the entry can close them, because the resolver has no view of
source state other than the snapshot itself. §8 O02–O03 record this as a
positive non-claim test, in the same way U03 records the absence of replay
protection.

## 4. Single-use scope and replay

What the epoch guarantees:

- **Per attempt.** One `commit_policy_change` invocation calls
  `commit_if_epoch` at most once.
- **Per snapshot epoch.** Among all attempts resolved against snapshot epoch
  E, at most one receives COMMITTED, because the first commit moves the
  epoch past E and every other attempt bound to E then gets EPOCH_MISMATCH.
  This depends on the source's atomicity (§3.3), which the fixture source
  models and a formal source must provide.

What it does not guarantee:

- **No request-level replay protection.** An identical request submitted
  again starts a new resolution against the current snapshot and current
  epoch. If current state again satisfies the request, it is authorized and
  committed again. That is a fresh authorization decision under current
  state, not a reuse of the earlier one.
- In normal use a resubmission after commit fails with POLICY_STATE_MISMATCH,
  but only because `expected_revision` / `expected_digest` no longer match
  the committed policy. That is the precondition doing its job, not replay
  detection. If the policy returns to the expected revision and digest
  (independent revert, or a request whose proposed value equals its expected
  value), the identical request can commit again.
- The request has no nonce, request ID, or idempotency key. Neither the
  resolver nor the source records which requests have been committed.

Request deduplication, idempotency keys and replay windows belong to the
caller or to a future contract. Adding them would require governed storage of
consumed request IDs inside epoch scope; this contract does not specify it.

## 5. Resource budgets and safe traversal

### 5.1 Budgets

Three budgets, three distinct results. None is supplied by the request.

| Budget | Owner | Exceeded result |
|---|---|---|
| Request | resolver constants | REQUEST_LIMIT_EXCEEDED |
| Snapshot structure | resolver constants | SNAPSHOT_LIMIT_EXCEEDED |
| Traversal (`max_grants`) | trusted snapshot (unchanged from #92) | AUTHORITY_LIMIT_EXCEEDED |

Structural limits are module constants, not provider-supplied and not
overridable per call: the provider's data size is the quantity being bounded.
Values are review defaults (Q3):

```
REQUEST_MAX_KEYS           = 16
REQUEST_MAX_STRING_CHARS   = 256     # keys and values
SNAPSHOT_MAX_GRANTS        = 1024
SNAPSHOT_MAX_ROOTS         = 64
SNAPSHOT_MAX_RECORD_KEYS   = 32      # any dict except roots
SNAPSHOT_MAX_SCOPE_ITEMS   = 64      # per operations / targets list
SNAPSHOT_MAX_STRING_CHARS  = 256     # keys and values
SNAPSHOT_MAX_INT_BITS      = 64      # at, max_grants, state_epoch, not_before, expires_at
SNAPSHOT_MAX_VISITS        = 65536
```

All results in §5 have `authorization_status` UNVERIFIED, `effect_path`
BLOCKED.

### 5.2 Safe-traversal rules

These apply to the request scan and the snapshot preflight. Goal: no
caller- or provider-defined code runs during measurement.

- S-1 **Exact-type gate first.** Every object is classified by
  `type(x) is dict | list | str | int | bool | NoneType`. No `isinstance`.
  Subclasses fail the gate.
- S-2 **Measure only gated objects.** `len()` is called only on exact `dict`,
  `list`, `str`; `int.bit_length()` only on exact `int`. An object that fails
  the gate is malformed and is never measured, iterated, hashed, compared or
  copied.
- S-3 **Iterate only gated containers**, via `dict.items(d)` / plain list
  iteration on the exact type, after the size check passes.
- S-4 **Whole-dict key gate before any keyed access.** Lookups on a dict can
  run `__eq__` of any stored key whose hash collides with the probe, so
  gating keys one at a time is not enough. For every exact dict `d`
  (request, snapshot, policy, grant, roots, anchor, seam return):

  1. Before the gate, the only permitted operations are `type(d)`, `len(d)`,
     and one iteration of `dict.keys(d)` or `dict.items(d)`. Iteration does
     not hash or compare keys.
  2. Size check: `len(d)` against the applicable cap (`REQUEST_MAX_KEYS`,
     `SNAPSHOT_MAX_RECORD_KEYS`, `SNAPSHOT_MAX_ROOTS`, or exactly 2 for a seam
     return).
  3. Gate pass: iterate *all* keys of `d` once. Each key must satisfy
     `type(k) is str`; each exact-`str` key is length-checked. The pass does
     not stop at the first non-`str` key, so a later over-length key still
     yields LIMIT (§5.4).
  4. Only if every key of `d` is an exact `str` may any keyed operation
     follow: `d[k]`, `d.get(k)`, `k in d`, `set(d)`, `dict(d)`, `==` on `d`
     or its key set. Comparing an exact-`str` key against the module's field
     name tuple is permitted after step 3, since both operands are exact `str`.
  5. If any key fails the gate, `d` is malformed. From then on `d` is accessed
     only by `dict.items(d)` iteration: no keyed operation, no hashing, no
     copy. Its scalar values are still size-checked (an over-length `str`
     value is LIMIT); its container values are not entered.
- S-5 **Fixed schema walk, no generic recursion.** The scan descends only at
  schema container positions:

  ```
  snapshot (dict)
  ├─ policy (dict)
  ├─ grants (list) ─ grant (dict) ─┬─ operations (list of str)
  │                                └─ targets (list of str)
  └─ roots (dict) ─ anchor (dict)
  ```

  Every other position is scalar. A container found at a scalar position
  (including a list that contains itself, or a dict inside `targets`) is
  malformed and is not entered. Maximum depth is 4 by construction.
- S-6 **No seam calls between first preflight and completed copy.** The copy
  is therefore bounded by what the preflight counted.
- S-7 The private copy is built from exact-typed values only; it contains no
  aliasing and no subclass instances.

This is resolver-local. It does not close the Principle 0 non-`str` /
`str`-subclass gap, which remains a separate fix line.

### 5.3 Visit counting (normative)

For an exact container entered at a schema container position:

```
visits(dict d) = 1 + Σ_{(k,v) in d} (1 + inner(v))
visits(list l) = 1 + Σ_{e in l}      (1 + inner(e))
inner(x)       = visits(x)  if x is an exact container at a schema container position
               = 0          otherwise (scalars, malformed objects, containers at scalar
                            positions, and every value of a dict that failed its key gate)
```

The key gate pass (S-4 step 3) does not add visits: each pair is charged once
under `1 + inner(v)` whether it is reached by the gate pass or the value pass.

Snapshot cost = `visits(snapshot)`. The counter is incremented before each
unit; the unit that would make the total exceed `SNAPSHOT_MAX_VISITS` is not
performed, and the scan stops with SNAPSHOT_LIMIT_EXCEEDED.

Request cost = `1 + len(request)`, ≤ 17 after the key cap; no separate visit
constant.

Aliasing is charged per expansion (per reference path), not per distinct
object. The resolver does not memoize by object identity, because the copy
materializes every expansion and the budget must bound that work. Aliasing
within schema is legal input, not malformation.

### 5.4 Limit vs malformed vs missing

Each scan has two phases.

Phase 1, size: walk per §5.2–5.3. On an exact object, check size caps before
iterating. Record, but do not stop for, malformation and missing fields. Stop
at the first size exceedance.

Phase 2, classify: if any size exceedance → LIMIT; else if any malformation →
INVALID_AUTHORITY_INPUT; else if any missing required field →
AUTHORITY_UNRESOLVED (snapshot only; a missing request field is
INVALID_AUTHORITY_INPUT per #92).

Consequences:

- **LIMIT > malformed > missing**, globally, independent of where in the
  structure each condition sits. Whether a structure exceeds a cap is a
  property of the structure; the stopping point does not change the result.
- Once a size exceedance stops the scan, later malformations are unknown.
  LIMIT is the only claim the resolver can support.
- LIMIT is reported only for sizes measured on exact-typed objects. An object
  whose size cannot be measured safely (S-2) is malformed. A list subclass
  with 10⁶ elements at `grants` yields INVALID_AUTHORITY_INPUT, with zero
  calls to its `__len__` / `__iter__`.
- Snapshot size limits are checked before any `verify_grant` call and before
  traversal, so SNAPSHOT_LIMIT_EXCEEDED preempts AUTHORITY_LIMIT_EXCEEDED.
  `max_grants` above the record count is harmless: cycle detection bounds
  traversal by distinct identifiers.

### 5.5 Request scan order

Before authentication; any failure means zero seam calls.

```
1  type(request) is not dict                 -> TypeError (#92)
2  len(request) > REQUEST_MAX_KEYS           -> REQUEST_LIMIT_EXCEEDED  (no key iterated)
3  phase 1: one dict.items(request) pass over ≤16 pairs, no keyed access:
     key: type(k) is str, else mark malformed; if str, len(k) > 256 -> size
     value: type(v) is str, else mark malformed; if str, len(v) > 256 -> size
4  phase 2: size -> REQUEST_LIMIT_EXCEEDED
            any non-str key or value  -> INVALID_AUTHORITY_INPUT (no keyed access)
5  keyed checks, only after all keys passed: set(request) == the eight fields,
   every value nonempty                      -> else INVALID_AUTHORITY_INPUT
6  bound copy built from the gated pairs
```

A 9–16-key request with an extra field remains INVALID_AUTHORITY_INPUT, as in
#92.

## 6. Resolution order and consolidated precedence

```
0  API types / callables / unexpected keyword     → TypeError, no seam call
1  request scan (§5.5)                            → REQUEST_LIMIT_EXCEEDED > INVALID_AUTHORITY_INPUT
2  authenticate                                   (#92)
3  snapshot_provider(); None                      → AUTHORITY_UNRESOLVED
4  snapshot preflight (§5.4), incl. D1            → SNAPSHOT_LIMIT_EXCEEDED > INVALID > UNRESOLVED
5  private copy; preflight of copy
6  traversal (#92 order, traversal budget)        → first decisive failure (#92)
7  D2 current_epoch()                             → AUTHORITY_STATE_CHANGED / AUTHORITY_VERIFICATION_ERROR
8  inspection AUTHORIZED, or commit_if_epoch (use-time entry only)
9  seam result validation and mapping (§3.4)
```

Earlier stage wins. Mixed failures across stages:

| Simultaneous conditions | Result | Why |
|---|---|---|
| request over limit + snapshot over limit | REQUEST_LIMIT_EXCEEDED | snapshot never acquired |
| request malformed + authentication fails | INVALID_AUTHORITY_INPUT | authenticate never called |
| snapshot over limit + malformed + missing | SNAPSHOT_LIMIT_EXCEEDED | §5.4 |
| snapshot malformed (subclass) + "large" | INVALID_AUTHORITY_INPUT | size not measurable |
| traversal denial + state changed | traversal reason | D2 not run on denial |
| traversal authorizes + state changed | AUTHORITY_STATE_CHANGED | D2 |
| epoch mismatch + now ≥ valid_until | AUTHORITY_STATE_CHANGED | seam step 3 before 4 |
| now < snapshot_at + epoch mismatch | AUTHORITY_VERIFICATION_ERROR | seam step 2 first |
| now < snapshot_at + now ≥ valid_until | not reachable | `snapshot_at < valid_until` (§3.3) |
| seam raises after writing | COMMIT_OUTCOME_UNKNOWN | §3.4 |
| dict with non-str key + over-length key or value | LIMIT | whole-dict gate pass completes (§5.2 S-4) |
| snapshot label older than content | AUTHORITY_STATE_CHANGED | D2; fail-closed (§3.6) |
| snapshot label newer than content, or torn content | not detected | O1 obligation (§3.6) |

Inspection result fields, exactly: `authorization_status`, `reason`,
`effect_path`, `request_binding`, `snapshot_id`, `state_epoch`,
`snapshot_at`, `valid_until`. The last five are None except on AUTHORIZED.
Snapshot schema adds exactly one required field, `state_epoch`.

Use-time entry when resolution does not authorize: UNVERIFIED reasons map to
NOT_COMMITTED with the same reason; AUTHORITY_VERIFICATION_ERROR maps to
COMMIT_ERROR. effect_path BLOCKED in both cases, since no commit seam was
called.

## 7. New reason codes

| Reason | Status | Distinct from |
|---|---|---|
| AUTHORITY_STATE_CHANGED | UNVERIFIED / NOT_COMMITTED | POLICY_STATE_MISMATCH: requester's expectation is wrong. This: state moved under a correct expectation |
| REQUEST_LIMIT_EXCEEDED | UNVERIFIED | INVALID_AUTHORITY_INPUT: shape. This: size |
| SNAPSHOT_LIMIT_EXCEEDED | UNVERIFIED | AUTHORITY_LIMIT_EXCEEDED: delegation depth |
| POLICY_CHANGE_COMMITTED | COMMITTED | — |
| COMMIT_OUTCOME_UNKNOWN | COMMIT_OUTCOME_UNKNOWN | AUTHORITY_VERIFICATION_ERROR: known no-write |

## 8. Acceptance cases (RED targets)

Fixture state source: in-memory reference source implementing §3.3 exactly,
with an epoch counter, a write counter, a controllable trusted clock, and a
hook that runs between resolution and the commit step. Tests that exercise
seam precedence validate this reference model and the entry's mapping, not
any production source.

Mid-change
- C01 Mutation of an unrelated grant fired from inside `verify_grant` →
  AUTHORITY_STATE_CHANGED; source unchanged by the resolver.
- C02 Visited leaf revoked from inside `verify_grant` →
  AUTHORITY_STATE_CHANGED, not AUTHORITY_REVOKED.
- C03 Leaf revoked in the pre-commit hook → NOT_COMMITTED /
  AUTHORITY_STATE_CHANGED; policy unchanged.
- C04 Positive control → COMMITTED; `committed_epoch` = seam value =
  snapshot epoch + 1; exactly one seam call; seam received
  `snapshot_at = at` and `valid_until` = chain minimum.
- C05 Traversal denial (revoked leaf in snapshot) while epoch moves during
  `verify_grant` → AUTHORITY_REVOKED; `current_epoch` calls = 0.

ABA
- A01 Policy p1→p2→p1 with identical digest in the pre-commit hook →
  NOT_COMMITTED / AUTHORITY_STATE_CHANGED.
- A02 Leaf revoked then restored in the pre-commit hook → same.
- A03 `current_epoch` returns less than snapshot epoch →
  AUTHORITY_VERIFICATION_ERROR.
- A04 `state_epoch` missing → AUTHORITY_UNRESOLVED; `True`, `-1`, `'3'`,
  `3.0` → INVALID_AUTHORITY_INPUT; `2**64` → SNAPSHOT_LIMIT_EXCEEDED.

Single use and replay (§4)
- U01 Attempts A and B resolve at epoch E; A's pre-commit hook runs B to
  completion. B → COMMITTED; A → NOT_COMMITTED / AUTHORITY_STATE_CHANGED.
  Exactly one COMMITTED for E.
- U02 Identical request after C04 → POLICY_STATE_MISMATCH; commit calls 0.
- U03 After C04, an independently authorized revert returns policy to the
  original revision/digest; identical original request → COMMITTED again.
  Positive non-claim test: documents absent replay protection.
- U04 Passing `prior_result`, `state_epoch`, `snapshot_at` or `valid_until`
  to either entry → TypeError, zero seam calls.

Seam rejection: zero writes and precedence
- Z01 Each of TIME_REGRESSION (`now = at - 1`), EPOCH_MISMATCH, NOT_CURRENT
  (`now = valid_until`): deep-equal source before/after, epoch unchanged,
  write counter 0, mapped per §3.4.
- Z02 Boundary: `now = at` and `now = valid_until - 1` → COMMITTED.
- Z03 `valid_until` uses chain minimum: intermediate expires before leaf and
  root; `now` between the two → NOT_CURRENT.
- P01 Epoch mismatch + expired → AUTHORITY_STATE_CHANGED.
- P02 Time regression + epoch mismatch → AUTHORITY_VERIFICATION_ERROR.
- P03 Tightest window, showing TIME_REGRESSION and NOT_CURRENT never
  co-occur: chain minimum `expires_at = at + 1`, so `valid_until = at + 1`.
  `now = at - 1` → TIME_REGRESSION; `now = at` → COMMITTED (separate fresh
  source); `now = at + 1` → NOT_CURRENT. Each with epoch mismatch added:
  `at - 1` → AUTHORITY_VERIFICATION_ERROR, `at + 1` →
  AUTHORITY_STATE_CHANGED. No `now` value produces both time conditions.
- P01–P03 each assert zero writes on every rejection.

Exception and malformed seam result
- X01 Seam performs step 5, then raises → COMMIT_OUTCOME_UNKNOWN,
  NOT_DETERMINED. Test asserts the source *did* change and epoch advanced,
  showing why BLOCKED would be false.
- X02 Seam raises before any write → identical entry result to X01. Test
  asserts the source did not change. The entry cannot distinguish X01 from
  X02 and must not try.
- X03 Malformed returns, each → COMMIT_OUTCOME_UNKNOWN: non-dict; dict
  subclass; extra or missing key; unknown outcome string; COMMITTED with
  `committed_epoch` ∈ {None, expected, expected − 1, True, '6'};
  EPOCH_MISMATCH with an int `committed_epoch`.
- X04 For X01–X03: commit seam calls = 1; no `current_epoch`,
  `snapshot_provider` or `commit_if_epoch` call after it.

Budget, both sides
- B01 `len(request) = 17` → REQUEST_LIMIT_EXCEEDED, zero seam calls. One key
  is a non-str object whose `__hash__` / `__eq__` record; recorder is reset
  after dict construction and must stay 0 (no key iterated). A 9-key request
  with an extra field → INVALID_AUTHORITY_INPUT (regression).
- B02 Request value of 256 chars passes the scan; 257 →
  REQUEST_LIMIT_EXCEEDED. Same for a 257-char extra key.
- B03 1025 grants → SNAPSHOT_LIMIT_EXCEEDED, zero `verify_grant` calls, with a
  malformed grant placed before and, separately, after the overflow point,
  and a missing field elsewhere.
- B04 Snapshot with `visits` exactly 65536 passes preflight; 65537 →
  SNAPSHOT_LIMIT_EXCEEDED. Helper computes the count from §5.3.
- B05 Each cap individually: 257-char string, 65-item scope list, 33-key
  grant dict, 65 roots, int of 65 bits → SNAPSHOT_LIMIT_EXCEEDED.
- B06 Request and snapshot both over limit → REQUEST_LIMIT_EXCEEDED;
  `authenticate` and `snapshot_provider` never called.
- B07 #92 N03/N04 unchanged: AUTHORITY_LIMIT_EXCEEDED, never
  SNAPSHOT_LIMIT_EXCEEDED.
- B08 Snapshot over limit and `max_grants` too small for the chain →
  SNAPSHOT_LIMIT_EXCEEDED.

Safe traversal
- T01 Subclass of `str`, `list`, `dict`, `int` at every schema position, each
  overriding `__len__`, `__iter__`, `__eq__`, `__hash__`, `__getitem__`,
  `keys`, `items`, `bit_length` with a recorder → INVALID_AUTHORITY_INPUT;
  recorder calls = 0.
- T02 List subclass with 10⁶ elements at `grants` → INVALID_AUTHORITY_INPUT,
  not SNAPSHOT_LIMIT_EXCEEDED; zero hook calls.
- T03 Dict with a non-str key whose `__hash__` / `__eq__` records →
  INVALID_AUTHORITY_INPUT; recorder calls = 0.
- T04 Hash-collision probe, whole-dict gate: a grant dict holds every valid
  field plus one non-str key whose `__hash__` returns `hash('id')` (computed
  at runtime, so hash randomization does not matter) and whose `__eq__`
  records. Recorder reset after construction. The non-str key is placed
  last in insertion order, so a per-key gate would already have looked up
  `'id'`. Expect INVALID_AUTHORITY_INPUT and recorder calls = 0. Repeat for
  the request dict (collision with `'requester_id'`), the snapshot dict, the
  policy dict, an anchor dict and a seam return dict (collision with
  `'outcome'`; result COMMIT_OUTCOME_UNKNOWN).
- T05 Same dict also holds a 257-char str key, placed after the non-str key →
  SNAPSHOT_LIMIT_EXCEEDED (request variant: REQUEST_LIMIT_EXCEEDED); recorder
  calls = 0.

Snapshot / epoch consistency (§3.6)
- O01 Reference source: `snapshot_provider`, `current_epoch` and
  `commit_if_epoch` share one counter; a mutation through any source mutator
  is visible to all three at the same epoch (O2, O4 for the reference model).
- O02 Lagging-content provider (content from E−1 with leaf unrevoked, label
  E, current E with leaf revoked) → COMMITTED. Positive non-claim test: an O1
  violation in this direction is undetectable by the resolver.
- O03 Torn provider (policy from E, grants from E−1, label E) → same as O02,
  same non-claim.
- O04 Leading-content provider (content from E+1, label E, current E+1) →
  AUTHORITY_STATE_CHANGED at D2; `commit_if_epoch` calls = 0.

Shared references within schema depth
- S01 One `targets` list object shared by K grants, expanded count under
  budget → same result as the unaliased fixture.
- S02 `verify_grant` mutates its record's `targets`; the next visited record
  that shared that list in the source sees the original value; source object
  unchanged.
- S03 Shared list whose distinct-object size is under budget but whose
  expanded count exceeds it → SNAPSHOT_LIMIT_EXCEEDED.
- S04 One anchor dict shared by two root IDs → legal; charged twice per §5.3.
- S05 `targets` list containing itself → INVALID_AUTHORITY_INPUT (container at
  scalar position, S-5). Runs in a disposable subprocess with a 5 s wall-clock
  timeout (N-test pattern) as a guard, though termination follows from S-5.

All v0.1 tests carry forward with `state_epoch` added to fixtures and a
fixture `current_epoch`; their expected results do not change.

## 9. Non-claims

- No production state backend, database CAS, distributed consensus, or
  replication semantics. The reference fixture source models atomicity.
- Epoch non-reuse across restart/restore is a formal-source obligation, not
  validated here.
- Snapshot/epoch consistency O1–O4 (§3.6) are source obligations. The
  resolver does not and cannot verify them; O02–O03 show that an O1
  violation with a label newer than its content passes undetected. Fixture
  validation covers only the reference source model.
- No request-level replay protection or idempotency (§4).
- Trusted time remains a modeling assumption (see
  PHAGE_TRUST_EVIDENCE_TRUSTED_CURRENT_TIME_ACQUISITION_BOUNDARY_DESIGN_v0_1).
- COMMITTED means the reference source applied a policy revision. It is not
  runtime enforcement closure, Gateway integration, or tool-effect binding.
- No DF-016 machinery is reused; the #95 record stands unchanged.
- §5.2 is resolver-local and does not close the Principle 0 non-`str` /
  `str`-subclass gap (separate fix line).
- No CLAIMS_STATUS change and no maturity promotion through this PR. Pilot
  remains gated on external Problem Adoption.

## 10. Delivery

- This PR: this document only.
- Freeze PR: `PHAGE_AUTHORITY_LINEAGE_HHN_EXECUTABLE_INTERFACE_v0_2.md` with
  frozen constants and exact signatures.
- RED PR: `test_phage_authority_lineage_hhn_v0_2.py`,
  `test_phage_authority_protected_use_v0_1.py`, reference fixture source;
  surface RED and semantic RED recorded separately.
- Implementation PR: `phage_authority_lineage_hhn_v0_2.py`,
  `phage_authority_protected_use_v0_1.py`. v0.1 module untouched.

## 11. Open review questions

- Q2 AUTHORITY_STATE_CHANGED as a new code vs reusing POLICY_STATE_MISMATCH.
  Proposed: new.
- Q3 Numeric budget values in §5.1.
- Q4 Keep inspection AUTHORIZED although never consumable. Proposed: keep,
  for #92 continuity.
- Q5 A request with `proposed_* == expected_*` (no-op) commits and advances
  the epoch under the current rules, and is the simplest U03-style replay.
  Options: allow (current); reject as INVALID_AUTHORITY_INPUT. Proposed:
  reject, as a narrow change; it does not add replay protection.
