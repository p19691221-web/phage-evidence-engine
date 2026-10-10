# Principle 0 authority-status type boundary — fix record

Date: 2026-10-10 (Asia/Taipei). Baseline: main `3e09f17` (merge of #105, RED).
Contract: PHAGE_PRINCIPLE0_AUTHORITY_STATUS_TYPE_DECISION_v0_1.md rev 2
(D1–D5, Q1 resolved). Tests: `test_phage_principle0_authority_status_type_v0_1.py`
(#105), unchanged in this PR.

Status: GREEN at fixture level for the authority-status type boundary of
`evaluate_override` and `mutate_schedule`.

## 1. Commit sequence

| Commit | Content | Purpose |
|---|---|---|
| 1 | Workflow `principle0-authority-status-type.yml`; implementation unchanged | This PR's own semantic RED, and CI from here on |
| 2 | `phage_principle0_emergency_override_v0_1.py`, `phage_principle0_schedule_v0_1.py` | Fix → GREEN |
| 3 | Remove `repro_principle0_authority_status_type_v0_1.py`; this record | Evidence; retire the characterization module |

Commit hashes are assigned when the series is applied; this record refers to
commits by position.

## 2. Semantic RED (commit 1)

There is no stub step. Both modules already exist and are exercised by the A–F
regressions, so replacing them with a fail-closed stub would break those
regressions without adding information. The defective base implementation is
this PR's semantic RED baseline.

Identical on CPython 3.12.3 and 3.13.16: 15 methods, 5 ok (controls K1–K3,
M2, M5), 10 FAIL, 111 failing subtests, 0 errors. This matches the #105 RED
record rev 2. Existing regressions: Emergency Override 6/6, Schedule 6/6.

## 3. Fix (commit 2)

Both modules gain `_normalize_authority_status(value, field)`:

```python
if type(value) is AuthorityStatus:   return value
if type(value) is str:
    member = _STATUS_BY_NAME.get(value)        # exact str keys
    if member is not None:           return member
    raise ValueError(f"unknown {field}: {value}")   # exact str only (#53, Q1)
raise ValueError(f"invalid {field}")                # fixed; value untouched
```

| Decision | Where implemented |
|---|---|
| D1 accepted values | `type()` checks; `_STATUS_BY_NAME` built from the enum |
| D2 rejection | `ValueError`; only an exact `str` is echoed; no `isinstance`, `hasattr`, `str()`, hashing or comparison on other values |
| D3 `None` / missing | `request.get(..., _MISSING)`; both reach the fixed-message branch |
| D4 order | `evaluate_override` normalizes first, before reading `schedule_status` |
| D5 `mutate_schedule` | normalization before `deepcopy`; CLEAN still reaches the existing `NotImplementedError` |

The `_status_name` helpers (`.name` / `str()` fallback) are removed from both
modules; status comparisons now use identity with `AuthorityStatus.CLEAN`.
`phage_principle0_schedule_v0_1` now imports `AuthorityStatus`. No other
module referenced `_status_name`. The remaining `isinstance` checks in the
schedule module concern schedule fields, which are out of scope.

## 4. GREEN (commit 2)

Identical on CPython 3.12.3 and 3.13.16:

| Suite | Result |
|---|---|
| `test_phage_principle0_authority_status_type_v0_1` | 15/15 OK |
| Emergency Override A–F (including #53 cases) | 6/6 PASS |
| Schedule A–F | 6/6 PASS |

## 5. Mutation check

The five mutants named in the decision and RED record, each run in an isolated
directory with copies of the tests (CPython 3.12.3). An unmutated control copy
passes. None is committed.

| Mutant | New-module result | Killed by (first failing assertion) | A–F regressions |
|---|---|---|---|
| `isinstance(value, str)` instead of `type(value) is str` | 23 failures | R4, R5, R6 (`str` subclasses / spoof accepted), R7 (`RuntimeError`), M3 | 6/6, 6/6 |
| `.name` / `str()` fallback retained before rejection | 39 failures | R3, R4, R6 (forged CLEAN accepted), R7 (`RuntimeError`), M3 | 6/6, 6/6 |
| Normalization after the schedule-status branches | 82 failures | R6 (results returned on early branches), R7 (raw `str` in result) | 6/6, 6/6 |
| Validation after `deepcopy` in `mutate_schedule` | 17 failures | M3, M4 (`['deepcopy'] != []`) | 6/6, 6/6 |
| Rejection message formats the rejected object | 67 failures | R1–R6, M3 (message mismatch) | 6/6, 6/6 |

5 of 5 killed. Every mutant passes the existing A–F regressions, so the new
module is the only suite that detects these defects.

## 6. Repro module removed (commit 3)

`repro_principle0_authority_status_type_v0_1.py` characterized the base
behavior and asserts the gaps; after the fix its gap assertions fail. It is
removed as planned (decision §6, RED record §5). It remains available at
merge commits `60fe364` (#104) and `3e09f17` (#105). The report
PHAGE_PRINCIPLE0_AUTHORITY_STATUS_TYPE_REPRO_REPORT_2026-10-10.md is kept
unchanged as the historical finding record.

## 7. CI

`.github/workflows/principle0-authority-status-type.yml`: Python 3.12,
`contents: read`; push and pull-request path filters on both modules,
`phage_authority_engine_v0_1.py`, the three Principle 0 test modules and the
workflow. Steps: the new module (`-v`), then both A–F regressions. Expected on
commit 1 alone: red (semantic RED). Expected on this PR head: green.

## 8. Findings status

| Finding (report rev 2) | Status after this PR |
|---|---|
| P0-T1 status laundering | Closed at fixture level (R4, R5) |
| P0-T2 forged CLEAN | Closed at fixture level (R3) |
| P0-T3 caller-hook `RuntimeError` leakage | Closed at fixture level (R3, R4: `ValueError`, zero hooks) |
| P0-T4 hooks executed | Closed at fixture level (zero recorder, including `__class__`) |
| P0-T5 raw passthrough, None/missing | Closed at fixture level (R1, R2, R6, R7) |
| P0-T6 `mutate_schedule` forged CLEAN | Closed at fixture level (M3) |

## 9. Non-claims

Fixture level only, for the authority-status input of the two entries. Runtime
reachability remains not established (report rev 2). No safe-traversal claim
for the request, schedule, grant or mutation objects, and no hardening of
`request.get` against a hostile mapping. Selected mutants do not establish
exhaustive coverage. No CLAIMS_STATUS or maturity change in this PR.
