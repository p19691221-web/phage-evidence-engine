# H/H′/N v0.2 and protected-use — RED record

Date: 2026-10-09 (Asia/Taipei). Baseline: main
`a853f35d7603ebf9b7f79c4ea2fab62c941d0a12`.
Interface: PHAGE_AUTHORITY_LINEAGE_HHN_EXECUTABLE_INTERFACE_v0_2.md (frozen by
merge of #97). Acceptance IDs: #96 §8 (`P§8`), allocated per interface §9.
Runtime: CPython 3.13.16, `python -m unittest`.

Status: RED. No `phage_authority_lineage_hhn_v0_2` or
`phage_authority_protected_use_v0_1` exists. Nothing here is implementation or
GREEN evidence.

## 1. Files in this PR

| File | Role |
|---|---|
| `fixture_phage_authority_reference_source_v0_1.py` | Reference source (§2.1 atomic step; E1, O1, O1a, O2, O3), base fixtures, normative visit counter, hook-recording types, `Collider` / `OpaqueKey`. Test support only. |
| `test_phage_authority_lineage_hhn_v0_2.py` | Inspection entry: #92 carried forward + allocated P§8 IDs |
| `test_phage_authority_protected_use_v0_1.py` | Use-time entry: allocated P§8 IDs + fixture-model checks |
| this record | Surface RED, semantic RED, coverage, raised defects |

No product module, no workflow, no change to frozen documents, v0.1 module or
CLAIMS_STATUS.

## 2. Surface RED (module absent)

Command, repository root, no extra path:

```
python -m unittest test_phage_authority_lineage_hhn_v0_2
python -m unittest test_phage_authority_protected_use_v0_1
```

| File | Tests | Failed | Of which `SURFACE_RED` | Passed | Skipped |
|---|---|---|---|---|---|
| hhn v0.2 | 48 | 48 | 48 | 0 | 0 |
| protected-use v0.1 | 29 | 24 | 24 | 4 | 1 |

Every failure message is `SURFACE_RED: <module> absent; not behavioral
evidence`. No import, syntax, or fixture error occurs. The four passing tests
are `ReferenceSourceModel` (visit figures 55/65536/65537, O01, O05, reference
rejections write nothing); they validate the fixture only. The skip is Z03
(§5).

These results say only that the modules do not exist.

## 3. Semantic RED (behavior mismatch)

Semantic RED needs a module that exists and behaves wrongly. No v0.2 stub has
been delivered, so the tests were run against two **throwaway baseline stubs**
kept outside the repository (source in Appendix A):

- **B-hhn**: #93's v0.1 resolver behind the frozen v0.2 signature. Ignores
  `state_epoch`, never calls `current_epoch`, no request/snapshot budgets, no
  v0.2 safe traversal, new result keys always `None`.
- **B-use**: naive consumer over B-hhn. Re-reads the epoch at commit time,
  passes `snapshot_at=0` and `valid_until=2**63`, no return validation, no
  exception containment.

Command: `PYTHONPATH=<baseline dir> python -m unittest -v <test module>`.

| File | Tests | ok | FAIL | ERROR | Skipped | `SURFACE_RED` |
|---|---|---|---|---|---|---|
| hhn v0.2 | 48 | 21 | 27 (60 failing subtests) | 0 | 0 | 0 |
| protected-use v0.1 | 29 | 12 | 13 | 4 (X03 has both) | 1 | 0 |

Every failure was inspected. Each is a behavioral mismatch: a wrong
reason/status, a `None` where v0.2 requires a value, a recorded hook call, a
missing `TypeError`, or an exception escaping where §5.2 requires
COMMIT_OUTCOME_UNKNOWN. No failure was traced to a fixture, helper or test
defect.

### 3.1 hhn v0.2 against B-hhn

| Group | Result | Mismatch observed |
|---|---|---|
| Carried forward: HP01/HP02, root/intermediate validity, seam isolation | FAIL | `state_epoch` / `snapshot_at` / `valid_until` are `None` (§5.1) |
| Carried forward: request/API table | FAIL | non-callable `snapshot_provider` not rejected (baseline wraps it) |
| Carried forward: other 14 | ok | #92 behavior preserved |
| C01, C02 | FAIL | AUTHORIZED instead of AUTHORITY_STATE_CHANGED (no D2) |
| C05 | ok | denial path, `current_epoch` not called |
| A03 | FAIL | AUTHORIZED for less / bool / str / float / exception / greater epoch |
| A04 | FAIL | missing `state_epoch` authorized |
| B01, B02, B05 (request rows), B06 | FAIL | INVALID_AUTHORITY_INPUT or AUTHORIZED instead of REQUEST_LIMIT_EXCEEDED |
| B03, B04, B05 (snapshot rows), B08, B10 | FAIL | INVALID / UNRESOLVED / NOT_CURRENT / SCOPE_VIOLATION / AUTHORITY_LIMIT instead of SNAPSHOT_LIMIT_EXCEEDED |
| B09 | FAIL | `OpaqueKey.__hash__` / `__eq__` called |
| B07 | ok | traversal budget unchanged |
| T01 | FAIL | some subclass positions AUTHORIZED; `str.__ne__` / `__hash__` called |
| T04 | FAIL | `Collider.__eq__` called (snapshot row) |
| T05 | FAIL | INVALID instead of LIMIT |
| T02, T03 | ok | already held by #93 preflight |
| S02, S04 | FAIL | result keys `None` |
| S03 | FAIL | no visit budget |
| S01, S05 | ok | |
| V01 | FAIL | no-op request AUTHORIZED |
| V02 | FAIL | result keys `None` |
| V03 | FAIL | authentication outcome reported instead of INVALID_AUTHORITY_INPUT |
| U04 | ok | keyword-only signature rejects extra keywords |
| Source positive control (not a P§8 ID) | FAIL | result keys `None` |

### 3.2 protected-use v0.1 against B-use

| Group | Result | Mismatch observed |
|---|---|---|
| C03, A01, A02, U01, P01 | FAIL | reason `EPOCH_MISMATCH` instead of AUTHORITY_STATE_CHANGED |
| C04 | FAIL | seam received `snapshot_at=0`, `valid_until=2**63` |
| Z01 | FAIL | TIME_REGRESSION and NOT_CURRENT not reached (wrong seam arguments); mapping absent |
| P02, P03 | FAIL | wrong mapping; `valid_until` not the chain minimum |
| X01, X02 | ERROR | seam exception escapes |
| X03 | FAIL + ERROR | malformed returns accepted or raise |
| T04 seam row | ERROR | `KeyError` from keyed access on the colliding dict |
| O04 | FAIL | COMMITTED on content newer than its label (no D2) |
| V01, V03 | FAIL | no-op request committed / authentication reported first |
| O02, O03 | ok | expected: these are non-claim tests (undetectable O1 violations commit) |
| U02, U03, U04, V02, Z02, X04 | ok | behavior already coincides on these paths |
| O01, O05, figures, reference rejections | ok | fixture-only |

## 4. Coverage against interface §9

| File | P§8 IDs present |
|---|---|
| hhn v0.2 | C01, C02, C05; A03, A04; B01–B10; T01, T02, T03, T04 (6 rows), T05; S01–S05; V01–V03; U04 |
| protected-use v0.1 | C03, C04; A01, A02; U01–U04; Z01, Z02, Z03 (skipped, §5); P01–P03; X01–X04; O01–O05; T04 seam-return row; V01–V03 |

All 18 #92 tests carry forward. Their reason/status/effect expectations are
unchanged. Mechanical edits required by the frozen interface, applied
uniformly: fixtures gain `state_epoch`; calls pass `current_epoch`; result
dicts gain the three §5.1 keys; the API table adds a non-callable
`current_epoch` row; the cycle worker passes `current_epoch`. `current_epoch`
calls are logged separately so #92 call-sequence assertions stay identical.

V01–V03 follow the per-entry table in interface §9 (inspection V02 =
AUTHORIZED; use-time V02 = COMMITTED).

## 5. Raised for review (not adjusted)

**SPEC_DEFECT_Z03.** P§8 Z03 requires an intermediate grant that expires
before both leaf and root. #92 attenuation, unchanged in v0.2, requires
`child.expires_at <= parent.expires_at`, so the leaf's expiry is always the
chain minimum. A fixture with an intermediate expiring before the leaf fails
resolution with AUTHORITY_SCOPE_VIOLATION and never reaches the commit seam.
Z03 is implemented as written and marked `skip` with this reason; its
expectation is not changed. Consequence: no reachable test can distinguish
"minimum over the chain" from "leaf's `expires_at`". C04 and P03 still pin
`valid_until` to the leaf value. Reviewer decision needed: remove Z03, or
restate it as "`valid_until` equals the leaf's `expires_at`, which is the
chain minimum under attenuation".

**Interface status line.** The merged interface still reads
`FREEZE CANDIDATE rev 2, NOT FROZEN`. The document states it becomes frozen on
approval and merge, which #97 completed. Updating the line is a separate
docs-only change; not touched here.

## 6. CI decision

No workflow is added. Adding these tests to CI now would turn main red until
the implementation PR. Recommended: the implementation PR adds a workflow
running both test files, with `ReferenceSourceModel` expected to pass from
the first commit.

## 7. Non-claims

The baseline stubs are diagnostic devices, not candidate implementations, and
are not in the repository. Their pass results carry no weight beyond showing
which tests already coincide with #93 behavior. The implementation PR must
record its own semantic RED against its own stub before turning GREEN, per
the #92/#93 discipline. The fixture validates only the reference source
model; no production source, CAS, concurrency or trusted-time acquisition is
exercised.

## Appendix A — baseline stubs (not committed)

`phage_authority_lineage_hhn_v0_2.py` (B-hhn):

```python
import phage_authority_lineage_hhn_v0_1 as v1

def resolve_policy_change(*, request, authenticate, snapshot_provider, current_epoch, verify_grant):
    if not callable(current_epoch):
        raise TypeError('callable seams required')
    def provider():
        state = snapshot_provider()
        if type(state) is dict and 'state_epoch' in state:
            state = {k: v for k, v in state.items() if k != 'state_epoch'}
        return state
    result = v1.resolve_policy_change(request=request, authenticate=authenticate,
                                      snapshot_provider=provider, verify_grant=verify_grant)
    result.update(state_epoch=None, snapshot_at=None, valid_until=None)
    return result
```

`phage_authority_protected_use_v0_1.py` (B-use):

```python
import phage_authority_lineage_hhn_v0_2 as resolver

def commit_policy_change(*, request, authenticate, snapshot_provider, current_epoch,
                         verify_grant, commit_if_epoch):
    result = resolver.resolve_policy_change(request=request, authenticate=authenticate,
        snapshot_provider=snapshot_provider, current_epoch=current_epoch, verify_grant=verify_grant)
    if result['authorization_status'] != 'AUTHORIZED':
        status = 'COMMIT_ERROR' if result['authorization_status'] == 'VERIFICATION_ERROR' else 'NOT_COMMITTED'
        return dict(commit_status=status, reason=result['reason'], effect_path='BLOCKED',
                    request_binding=None, committed_epoch=None)
    out = commit_if_epoch(expected_epoch=current_epoch(), snapshot_at=0,
                          valid_until=2 ** 63, binding=result['request_binding'])
    if out['outcome'] == 'COMMITTED':
        return dict(commit_status='COMMITTED', reason='POLICY_CHANGE_COMMITTED',
                    effect_path='EFFECT_APPLIED', request_binding=result['request_binding'],
                    committed_epoch=out['committed_epoch'])
    return dict(commit_status='NOT_COMMITTED', reason=out['outcome'], effect_path='BLOCKED',
                request_binding=None, committed_epoch=None)
```
