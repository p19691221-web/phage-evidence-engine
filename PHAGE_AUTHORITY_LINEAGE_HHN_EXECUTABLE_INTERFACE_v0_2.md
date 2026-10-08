# H/H′/N executable interface v0.2 — freeze candidate

Status: FREEZE CANDIDATE, NOT FROZEN. Prepared 2026-10-09 (Asia/Taipei).
Becomes frozen only on explicit review approval and merge.
Baseline: main `cb425810b57d73a83d714a06e0509550157f9af5`.
Supersedes for new work: PHAGE_AUTHORITY_LINEAGE_HHN_EXECUTABLE_INTERFACE_v0_1.md
(frozen, #92). v0.1 and `phage_authority_lineage_hhn_v0_1.py` stay unchanged as
provenance.
Decisions source: PHAGE_AUTHORITY_RESOLVER_USE_TIME_CONSISTENCY_CONTRACT_v0_1.md
(#96, rev 5, NOT FROZEN). Semantic requirements: #91.
Implementation / executable validation: NOT STARTED.

This document restates only what an implementer and a test author need. It
adds no rule absent from #91, #92 or #96. Rationale lives in #96 and is
referenced by section (`P§n`). Where wording here and in #96 differ, this
document governs after freeze; any such difference found in review is a defect
to fix before freeze.

## 1. Modules and entries

| Module | Entry | Role |
|---|---|---|
| `phage_authority_lineage_hhn_v0_2` | `resolve_policy_change` | Inspection. Never consumable. |
| `phage_authority_protected_use_v0_1` | `commit_policy_change` | Use-time. Only entry that can cause an effect. |

```python
resolve_policy_change(*, request, authenticate, snapshot_provider,
                      current_epoch, verify_grant) -> dict

commit_policy_change(*, request, authenticate, snapshot_provider,
                     current_epoch, verify_grant, commit_if_epoch) -> dict
```

Both are keyword-only with no defaults. `commit_policy_change` performs the
same resolution as `resolve_policy_change` (§6 stages 0–7) and must not accept
or reuse any result of a separate inspection call. Neither entry accepts any
other keyword; prior results, tokens, epochs, `snapshot_at` and `valid_until`
cannot be supplied (TypeError raised by the signature, before any seam call).

Constants are module-level in `phage_authority_lineage_hhn_v0_2`, imported by
the protected-use module, and not overridable per call.

## 2. Seams

All seams are trusted modeling assumptions. Each must be callable; otherwise
TypeError before any seam call. Arguments are supplied by the entry, never by
the caller.

| Seam | Call | Accepted return | Anything else / exception |
|---|---|---|---|
| `authenticate` | `authenticate(requester_id)` | exact `str` in {`ESTABLISHED`, `NOT_ESTABLISHED`, `VERIFICATION_ERROR`} | AUTHORITY_VERIFICATION_ERROR |
| `snapshot_provider` | `snapshot_provider()` | any value; `None` → AUTHORITY_UNRESOLVED, everything else classified by stage 4 (§7), e.g. a non-dict → INVALID_AUTHORITY_INPUT | exception → AUTHORITY_VERIFICATION_ERROR |
| `verify_grant` | `verify_grant(record, at)` | exact `str` in {`VERIFIED`, `UNVERIFIED`, `VERIFICATION_ERROR`} | AUTHORITY_VERIFICATION_ERROR |
| `current_epoch` | `current_epoch()` | exact `int`, not `bool` | AUTHORITY_VERIFICATION_ERROR |
| `commit_if_epoch` | `commit_if_epoch(expected_epoch=, snapshot_at=, valid_until=, binding=)` | §2.1 | COMMIT_OUTCOME_UNKNOWN |

Authentication outcome mapping is unchanged from #92: `NOT_ESTABLISHED` →
AUTHENTICATION_NOT_ESTABLISHED; `VERIFICATION_ERROR` →
AUTHORITY_VERIFICATION_ERROR. `verify_grant` mapping is unchanged: `UNVERIFIED`
→ AUTHORITY_UNRESOLVED.

`verify_grant` receives a fresh copy of the grant record per call and the
snapshot `at`. Mutating the argument cannot affect resolution state, the
snapshot returned by the provider, or other records.

### 2.1 `commit_if_epoch`

Arguments: `expected_epoch` = snapshot `state_epoch`; `snapshot_at` = snapshot
`at`; `valid_until` = §5.3; `binding` = the 8-tuple of §3.

Return, well-formed only if all hold (checked under §7 safe-traversal rules,
whole-dict key gate first):

- `type(raw) is dict` and `len(raw) == 2`;
- every key exact `str`; key set exactly `{"outcome", "committed_epoch"}`;
- `outcome` exact `str` in {`COMMITTED`, `EPOCH_MISMATCH`, `NOT_CURRENT`,
  `TIME_REGRESSION`};
- `COMMITTED` ⇒ `committed_epoch` exact `int`, not `bool`,
  `committed_epoch > expected_epoch`; other outcomes ⇒ `committed_epoch is None`.

Any malformed return, any exception raised by the seam, and any exception
raised while validating its return → COMMIT_OUTCOME_UNKNOWN.

Normative atomic step for the reference source; obligation on any formal
source (P§3.3):

```
1  now := trusted source time
2  now < snapshot_at          -> TIME_REGRESSION   no write
3  epoch != expected_epoch    -> EPOCH_MISMATCH    no write
4  now >= valid_until         -> NOT_CURRENT       no write
5  write binding.proposed_revision / proposed_digest to binding.policy_id;
   epoch := value > expected_epoch                 -> COMMITTED
```

Steps 1–5 are atomic with respect to every other mutator. Rejections leave
policy, grants, root anchors, configuration and epoch unchanged.

### 2.2 Source obligations (not verifiable by the resolver)

From P§3.1 and P§3.6; listed so the reference source and RED fixtures implement
them, and so no reader mistakes them for resolver guarantees.

| ID | Obligation |
|---|---|
| E1 | Epoch: exact int ≥ 0, monotonic, never reused; covers policy, all grants, root anchors, `max_grants`; every in-scope write advances it in the same atomic section |
| O1 | Snapshot content and `state_epoch` come from one atomic read; content equals state at exactly that epoch |
| O1a | Returned snapshot and every reachable container stay unmodified until the resolver's private copy is complete; provider returns a structure detached from its live store |
| O2 | `snapshot_provider`, `current_epoch`, `commit_if_epoch` share one source and one epoch counter |
| O3 | `at` is trusted source time taken within the O1 read; `commit_if_epoch` reads `now` from the same time source |

## 3. Request schema

Plain `dict` (exact type; otherwise TypeError) with exactly these eight keys,
each an exact nonempty `str` of at most `REQUEST_MAX_STRING_CHARS` characters:

```
requester_id, policy_id, expected_revision, expected_digest,
proposed_revision, proposed_digest, operation, leaf_grant_id
```

`operation` must be `POLICY_CHANGE`; any other value is
AUTHORITY_SCOPE_VIOLATION at stage 6 (#92). A request with both
`proposed_revision == expected_revision` and `proposed_digest ==
expected_digest` is INVALID_AUTHORITY_INPUT (Q5). The bound copy is taken after
the request scan; `binding` and `request_binding` are the eight values as a
tuple in the order above. `proposed_digest` is an opaque fixture reference.

## 4. Snapshot schema

Unchanged from #92 except one added required field, `state_epoch`.

```
snapshot  dict, exactly: snapshot_id  str (nonempty)
                         policy       dict
                         grants       list of grant dict
                         roots        dict  root_id(str) -> anchor dict
                         at           int
                         max_grants   int > 0, not bool
                         state_epoch  int >= 0, not bool
policy    dict, exactly: policy_id (str, no * or ?), revision (str),
                         digest (str), mutable_by_policy_change (bool)
anchor    dict, exactly: revision (str), digest (str)
grant     dict, exactly: id, revision, digest, subject, issuer   (str)
                         parent_id        None or str
                         operations       list of unique str from {POLICY_CHANGE}
                         targets          list of unique str, no * or ?
                         not_before, expires_at   int, not_before < expires_at
                         revoked          bool or None
                         can_delegate     bool
```

All `str` fields above are exact nonempty `str`. All `int` fields are exact
`int`, not `bool`. Grant `id` values are unique. Missing-versus-malformed
classification is #92's, extended by §7.4.

## 5. Results

### 5.1 Inspection result (`resolve_policy_change`)

Exactly these keys:

| Key | AUTHORIZED | Otherwise |
|---|---|---|
| `authorization_status` | `AUTHORIZED` | `UNVERIFIED` or `VERIFICATION_ERROR` |
| `reason` | `POLICY_CHANGE_AUTHORIZED` | §5.4 |
| `effect_path` | `NOT_DETERMINED` | `BLOCKED` |
| `request_binding` | 8-tuple (§3) | `None` |
| `snapshot_id` | snapshot `snapshot_id` | `None` |
| `state_epoch` | snapshot `state_epoch` | `None` |
| `snapshot_at` | snapshot `at` | `None` |
| `valid_until` | §5.3 | `None` |

An inspection AUTHORIZED is an inspection record. No entry accepts it.

### 5.2 Use-time result (`commit_policy_change`)

Exactly these keys: `commit_status`, `reason`, `effect_path`,
`request_binding`, `committed_epoch`. `request_binding` and `committed_epoch`
are non-`None` only for `COMMITTED`.

| Situation | commit_status | reason | effect_path |
|---|---|---|---|
| Resolution UNVERIFIED (any reason) | NOT_COMMITTED | resolution reason | BLOCKED |
| Resolution VERIFICATION_ERROR | COMMIT_ERROR | AUTHORITY_VERIFICATION_ERROR | BLOCKED |
| Pre-seam guard `snapshot_at < valid_until` fails (internal fault) | COMMIT_ERROR | AUTHORITY_VERIFICATION_ERROR | BLOCKED |
| Seam `COMMITTED` | COMMITTED | POLICY_CHANGE_COMMITTED | EFFECT_APPLIED |
| Seam `EPOCH_MISMATCH` | NOT_COMMITTED | AUTHORITY_STATE_CHANGED | BLOCKED |
| Seam `NOT_CURRENT` | NOT_COMMITTED | AUTHORITY_NOT_CURRENT | BLOCKED |
| Seam `TIME_REGRESSION` | COMMIT_ERROR | AUTHORITY_VERIFICATION_ERROR | BLOCKED |
| Seam exception / malformed return | COMMIT_OUTCOME_UNKNOWN | COMMIT_OUTCOME_UNKNOWN | NOT_DETERMINED |

The pre-seam guard is unreachable under a correct resolver (P§3.3) and is an
implementation assertion, not an acceptance case. After `commit_if_epoch` is
invoked the entry makes no further seam call, does not retry, and does not
read state back.

### 5.3 `valid_until`

`min(expires_at)` over every grant visited on the authorizing chain, leaf to
anchored root inclusive. Because resolution requires
`not_before <= at < expires_at` for each, `at < valid_until` on every
AUTHORIZED result.

### 5.4 Reason codes

| Reason | authorization_status | Source |
|---|---|---|
| POLICY_CHANGE_AUTHORIZED | AUTHORIZED | #92 |
| AUTHENTICATION_NOT_ESTABLISHED | UNVERIFIED | #92 |
| INVALID_AUTHORITY_INPUT | UNVERIFIED | #92; extended by §7 and Q5 |
| AUTHORITY_UNRESOLVED | UNVERIFIED | #92; adds missing `state_epoch` |
| POLICY_STATE_MISMATCH | UNVERIFIED | #92 |
| AUTHORITY_SCOPE_VIOLATION | UNVERIFIED | #92 |
| AUTHORITY_REVOKED | UNVERIFIED | #92 |
| AUTHORITY_NOT_CURRENT | UNVERIFIED | #92; also use-time NOT_CURRENT |
| AUTHORITY_CYCLE_DETECTED | UNVERIFIED | #92 |
| AUTHORITY_LIMIT_EXCEEDED | UNVERIFIED | #92 (traversal budget) |
| AUTHORITY_VERIFICATION_ERROR | VERIFICATION_ERROR | #92 |
| AUTHORITY_STATE_CHANGED | UNVERIFIED | new (Q2) |
| REQUEST_LIMIT_EXCEEDED | UNVERIFIED | new |
| SNAPSHOT_LIMIT_EXCEEDED | UNVERIFIED | new |
| POLICY_CHANGE_COMMITTED | — (use-time only) | new |
| COMMIT_OUTCOME_UNKNOWN | — (use-time only) | new |

## 6. Resolution order

Earlier stage wins. Within stage 6, #92's order applies unchanged.

```
0  signature, exact-dict request, callable seams  -> TypeError, no seam call
1  request scan (§7.5)                            -> REQUEST_LIMIT_EXCEEDED
                                                    > INVALID_AUTHORITY_INPUT
2  authenticate(requester_id)                     -> #92 mapping
3  snapshot_provider(); None                      -> AUTHORITY_UNRESOLVED
4  snapshot preflight (§7)                        -> SNAPSHOT_LIMIT_EXCEEDED
                                                    > INVALID_AUTHORITY_INPUT
                                                    > AUTHORITY_UNRESOLVED
5  private copy; preflight of the copy            (no seam call in 4–5)
6  #92 traversal: policy identity -> eligibility/operation -> leaf to root,
   cycle before budget, verify_grant per visited grant, local checks,
   attenuation, root anchor                       -> #92 reasons
7  current_epoch() once, only if 6 reached the anchored root:
     equal                                        -> continue
     greater                                      -> AUTHORITY_STATE_CHANGED
     less / exception / not exact int             -> AUTHORITY_VERIFICATION_ERROR
8  inspection: AUTHORIZED (§5.1)
   use-time:   pre-seam guard; commit_if_epoch once; §5.2 mapping
```

Any exception from a seam in stages 2–7, or any internal fault, is
AUTHORITY_VERIFICATION_ERROR (#92 containment); exception detail is not
returned.

### 6.1 Seam call counts

| Seam | Calls per entry invocation |
|---|---|
| authenticate | 0 if stage 0–1 fails, else 1 |
| snapshot_provider | 1 only if authentication `ESTABLISHED`, else 0 |
| verify_grant | one per visited grant; 0 if stage 4–5 fails |
| current_epoch | 1 only if stage 6 reached the anchored root, else 0 |
| commit_if_epoch | use-time only; 1 only if stages 0–7 authorize and the guard holds, else 0 |

### 6.2 Mixed-failure precedence (normative)

| Simultaneous conditions | Result |
|---|---|
| request over limit + snapshot over limit | REQUEST_LIMIT_EXCEEDED |
| request malformed or no-op + authentication would fail | INVALID_AUTHORITY_INPUT |
| snapshot over limit (reachable) + malformed + missing | SNAPSHOT_LIMIT_EXCEEDED |
| oversize only behind an unreachable container | INVALID_AUTHORITY_INPUT |
| non-exact object, any size | INVALID_AUTHORITY_INPUT |
| traversal denial + state changed | traversal reason (stage 7 not run) |
| traversal authorizes + state changed | AUTHORITY_STATE_CHANGED |
| seam: epoch mismatch + now ≥ valid_until | AUTHORITY_STATE_CHANGED |
| seam: now < snapshot_at + epoch mismatch | AUTHORITY_VERIFICATION_ERROR |
| seam: now < snapshot_at + now ≥ valid_until | unreachable (§5.3) |
| seam raises after writing | COMMIT_OUTCOME_UNKNOWN |

## 7. Budgets and safe traversal

### 7.1 Constants (Q3: accepted as fixture v0.2 limits)

```python
REQUEST_MAX_KEYS          = 16
REQUEST_MAX_STRING_CHARS  = 256      # keys and values
SNAPSHOT_MAX_GRANTS       = 1024
SNAPSHOT_MAX_ROOTS        = 64
SNAPSHOT_MAX_RECORD_KEYS  = 32       # every snapshot dict except roots
SNAPSHOT_MAX_SCOPE_ITEMS  = 64       # per operations / targets list
SNAPSHOT_MAX_STRING_CHARS = 256      # keys and values
SNAPSHOT_MAX_INT_BITS     = 64       # int.bit_length(); every int field
SNAPSHOT_MAX_VISITS       = 65536
```

Traversal budget remains the snapshot's `max_grants` (#92 semantics).

### 7.2 Safe-traversal rules

Applies to the request scan, snapshot preflight and seam-return validation.

- **S-1** Classify by `type(x) is T` for `dict`, `list`, `str`, `int`, `bool`,
  `NoneType`. No `isinstance`. Subclasses fail.
- **S-2** `len()` only on exact `dict`/`list`/`str`; `bit_length()` only on
  exact `int`. A failing object is malformed and is never measured, iterated,
  hashed, compared or copied.
- **S-3** Iterate only exact containers, after their size check, via
  `dict.keys(d)` / `dict.items(d)` or plain list iteration.
- **S-4** Whole-dict key gate, for every dict:
  1. before the gate: only `type(d)`, `len(d)`, one iteration of
     `dict.keys(d)` or `dict.items(d)`;
  2. size check `len(d)` against its cap (`REQUEST_MAX_KEYS`,
     `SNAPSHOT_MAX_RECORD_KEYS`, `SNAPSHOT_MAX_ROOTS`, or `== 2` for a seam
     return);
  3. gate pass over **all** keys: `type(k) is str`, and length check on each
     exact-`str` key; does not stop at the first failure;
  4. only if every key is exact `str`: keyed access (`d[k]`, `d.get`,
     `k in d`, `set(d)`, `dict(d)`) and comparison of `set(d)` with a module
     field-name set. `==` on `d` itself is never used;
  5. on gate failure: `d` is malformed; accessed only by `dict.items(d)`;
     scalar values still size-checked; container values not entered.
- **S-5** Fixed schema walk, max depth 4; descend only at:
  `snapshot.policy`, `snapshot.grants[*]`, `grant.operations`,
  `grant.targets`, `snapshot.roots[*]`. A container elsewhere is malformed
  and not entered.
- **S-6** No seam call from the start of stage 4 to the end of stage 5. With
  O1a, the copy is bounded by the stage-4 count.
- **S-7** The private copy contains only exact-typed values, no aliasing.

### 7.3 Visit counting

```
visits(dict d) = 1 + Σ_{(k,v) in d} (1 + inner(v))
visits(list l) = 1 + Σ_{e in l}      (1 + inner(e))
inner(x) = visits(x)  if x is an exact container at an S-5 position
                      in a dict that passed its key gate
         = 0          otherwise
```

Charged per expansion; no identity memoization. Counter checked before each
unit; the unit that would exceed `SNAPSHOT_MAX_VISITS` is not performed.

Reference figures (must be reproduced by the RED helper before use):
#92 base fixture plus `state_epoch` = **55**. With `n = 1024` grants, each with
one operation, 1023 grants of 47 targets and one of 28 targets, one root
anchor: **65536**; last grant at 29 targets: **65537**. General form for this
shape: `19 + Σ_i (16 + o_i + t_i)` (P§5.3).

### 7.4 Classification

Phase 1 walks reachable positions (S-4, S-5), records malformation and
missing fields, and stops at the first size exceedance. Phase 2:
size exceedance → `*_LIMIT_EXCEEDED`; else malformation →
INVALID_AUTHORITY_INPUT; else missing → AUTHORITY_UNRESOLVED (snapshot only;
missing request fields are INVALID_AUTHORITY_INPUT).

LIMIT > malformed > missing holds over positions reachable by safe traversal.
Size exceedance at an unreachable position is not observed.

`state_epoch` (D1): missing → AUTHORITY_UNRESOLVED; non-`int`, `bool` or
negative → INVALID_AUTHORITY_INPUT; bit length > 64 → SNAPSHOT_LIMIT_EXCEEDED.

### 7.5 Request scan

```
1  len(request) > REQUEST_MAX_KEYS           -> REQUEST_LIMIT_EXCEEDED (no key iterated)
2  one dict.items(request) pass:
     key   not exact str -> malformed; exact str > 256 chars -> size
     value not exact str -> malformed; exact str > 256 chars -> size
3  size -> REQUEST_LIMIT_EXCEEDED; malformed -> INVALID_AUTHORITY_INPUT
4  keyed checks: set(request) == the eight fields; all values nonempty
5  no-op: proposed_revision == expected_revision
          AND proposed_digest == expected_digest -> INVALID_AUTHORITY_INPUT
6  bound copy
```

## 8. Single-use scope

Per invocation, `commit_if_epoch` is called at most once. Per snapshot epoch,
at most one attempt receives COMMITTED (depends on E1 and seam atomicity). No
request-level replay protection, nonce, or idempotency key exists; an
identical request resubmitted is a new authorization against current state
(P§4).

## 9. RED test layout

No implementation exists. The RED PR adds:

| File | Content |
|---|---|
| `fixture_phage_authority_reference_source_v0_1.py` | Reference source: store, epoch counter, write counter, controllable clock, pre-commit hook, the three source seams implementing §2.1–2.2. Test support only; not a product module. |
| `test_phage_authority_lineage_hhn_v0_2.py` | Inspection entry |
| `test_phage_authority_protected_use_v0_1.py` | Use-time entry |

Acceptance IDs are those of P§8. Allocation:

| File | IDs |
|---|---|
| hhn v0.2 | all #92 tests carried forward with `state_epoch` and `current_epoch` added; C01, C02, C05; A03, A04; B01–B10; T01–T05 (T04 seam-return row in protected-use); S01–S05; V01–V03; U04 (inspection entry) |
| protected-use v0.1 | C03, C04; A01, A02; U01–U04; Z01–Z03; P01–P03; X01–X04; O01–O05; T04 seam-return row; V01 (use-time entry, all five seams 0) |

Carried-forward #92 tests keep their expected results. A v0.1 test that cannot
carry forward without a changed expectation is a freeze defect, to be raised
in review, not adjusted silently in the RED PR.

RED discipline (as #92/#93): absent module = surface RED, recorded
separately; semantic RED logs preserved through the stub/implementation
sequence. Cycle and self-containing-list tests run in a disposable subprocess
with a 5 s wall-clock timeout. No CI workflow is added in this freeze PR;
whether the RED PR adds one is decided there.

## 10. Freeze scope

On freeze, the following are fixed for v0.2: entry and seam signatures (§1–2),
request and snapshot schemas (§3–4), result shapes and reason codes (§5),
resolution order and precedence (§6), constants, safe-traversal rules,
visit formula and classification (§7). Any change to these after freeze
requires a new interface version.

Not fixed here and not claimed: production state source, CAS, consensus,
epoch persistence across restore, trusted-time acquisition, replay
protection, Gateway / tool-effect integration, runtime enforcement closure.
Principle 0 non-`str` / subclass gap remains a separate fix line. No
CLAIMS_STATUS change; no maturity promotion. #96 stays NOT FROZEN as the
rationale record.

## 11. Review checklist for freeze

- Every rule in §2–8 traceable to #91, #92 or #96 (P§ references).
- No rule in #96 omitted that changes observable behavior.
- §9 allocation covers every P§8 ID exactly once per entry it applies to.
- Reference figures in §7.3 reproduced independently.
