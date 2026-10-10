# Principle 0 authority-status type boundary — RED record

Date: 2026-10-10 (Asia/Taipei). Baseline: main `60fe364` (merge of #104).
Contract: PHAGE_PRINCIPLE0_AUTHORITY_STATUS_TYPE_DECISION_v0_1.md rev 2,
cases K1–K3, R1–R7, M1–M5.
Scope: tests only. No Principle 0 implementation change, no workflow
(decision §5: CI is enabled by the fix PR).

## 1. File

`test_phage_principle0_authority_status_type_v0_1.py`: 15 test methods, one
per decision case. Hostile input classes are defined in the module itself, so
it does not depend on `repro_principle0_authority_status_type_v0_1.py`, which
the fix PR removes. Hook and deepcopy recorders are cleared after inputs are
built and immediately before each call. Exceptions are captured and checked
by exact type and message, so a wrong exception is a FAIL, not an ERROR.

Run: `python -m unittest -v test_phage_principle0_authority_status_type_v0_1`

## 2. RED type

There is no surface RED: both modules exist. The current implementation is
the defective baseline, so every failure below is semantic RED against
`60fe364` itself.

## 3. Manual run

Identical on CPython 3.12.3 and 3.13.16:

| Result | Count |
|---|---|
| Test methods | 15 |
| ok | 5 |
| FAIL | 10 (91 failing subtests) |
| ERROR | 0 |

| Case | Result | First failing assertion (representative) |
|---|---|---|
| K1 each enum member | ok (control) | — |
| K2 each canonical exact name | ok (control) | — |
| K3 unknown exact `str`, #53 message | ok (control) | — |
| R1 explicit `None` | FAIL (1) | result returned instead of `ValueError` |
| R2 missing key | FAIL (1) | result returned instead of `ValueError` |
| R3 non-`str` values | FAIL (10) | result returned; `RuntimeError` instead of `ValueError` (raising `.name`) |
| R4 `str` subclasses | FAIL (4) | result returned; `RuntimeError` instead of `ValueError` (raising `__hash__`) |
| R5 `__class__` spoof | FAIL (1) | result returned (laundered CLEAN) |
| R6 normalization before schedule branches | FAIL (14) | result returned on `SCHEDULE_UNRESOLVED` / `SCHEDULE_MATCH` for every invalid input; valid-input controls on those branches pass |
| R7 raise `ValueError` or return genuine member | FAIL (39) | raw `None`, `int`, `bytes`, `list`, `dict`, forged objects in `authority_status`; `RuntimeError` escapes |
| M1 non-CLEAN member and exact name | FAIL (4) | exact-name inputs return the raw `str`, not the genuine member; enum inputs pass |
| M2 CLEAN keeps `NotImplementedError` | ok (control) | — |
| M3 rejected before `deepcopy` | FAIL (16) | result returned after `deepcopy`; `NotImplementedError` for forged CLEAN; `RuntimeError` |
| M4 unknown exact `str` before `deepcopy` | FAIL (1) | result (BLOCKED) returned instead of `ValueError` |
| M5 omitted argument | ok (control) | signature `TypeError`; `deepcopy` not reached |

Notes:

- In R3–R5 and M3 the first failing assertion is usually the result or
  exception type, so the zero-hook assertion is not reached at baseline. It
  takes effect once rejection is implemented.
- R7 passes for inputs that the baseline launders to a genuine member
  (`HookStr`, `LyingStr`, `SideEffectStr`, `ClassSpoof`); those are caught by
  R4 and R5, not by R7.

Existing regressions at the same baseline, unchanged: Emergency Override 6/6
(including the #53 cases), Schedule 6/6. The repro module still passes 18/18
(it characterizes the baseline).

## 4. Expectations for the fix PR

- All 15 methods pass; existing regressions stay 6/6 and 6/6.
- CI added for this module (decision §5).
- Own semantic RED → GREEN record, plus the decision's mutants (`isinstance`
  instead of `type`; retained `.name` / `str()` fallback; normalization after
  the schedule branches; validation after `deepcopy`; message formatting the
  rejected object).
- `repro_principle0_authority_status_type_v0_1.py` removed (its gap
  assertions will fail).

## 5. Non-claims

No gap is closed by this PR. Fixture level only; runtime reachability remains
not established (report rev 2). No CLAIMS_STATUS or maturity change.
