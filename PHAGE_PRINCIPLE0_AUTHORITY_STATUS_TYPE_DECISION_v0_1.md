# Principle 0 authority-status type boundary — decision record v0.1

Status: DRAFT FOR REVIEW, NOT FROZEN. Prepared 2026-10-10 (Asia/Taipei).
Baseline: main `6eb0ee2`.
Input: PHAGE_PRINCIPLE0_AUTHORITY_STATUS_TYPE_REPRO_REPORT_2026-10-10.md
(findings P0-T1…P0-T6) and the review decisions of 2026-10-10.
Implementation / tests: NOT STARTED.

Sequence: decision review → RED tests → fix → re-review.

## 1. Scope

In scope: the authority-status input of
`phage_principle0_emergency_override_v0_1.evaluate_override`
(`request['ordinary_authority_status']`) and
`phage_principle0_schedule_v0_1.mutate_schedule` (`authority_status`).

Out of scope: safe traversal of the request, schedule, grant or mutation
objects; the type of `request` itself; other fields such as `schedule_status`,
`at`, grant fields. This record does not harden `request.get` against a hostile
mapping.

## 2. Decisions

| ID | Item | Decision |
|---|---|---|
| D1 | Accepted values | An exact `AuthorityStatus` member (`type(v) is AuthorityStatus`), or an exact `str` (`type(v) is str`) equal to a canonical member name |
| D2 | Rejection | Always `ValueError`. Fixed message. No formatting of the rejected object, no `.name`, no `str()`, no hashing, no comparison |
| D3 | `None` and missing key | Both rejected with `ValueError`, same external behavior; covered by separate tests |
| D4 | Order in `evaluate_override` | Authority-status normalization runs before every schedule-status branch, so no result carries a raw input object |
| D5 | `mutate_schedule` | Same rule, validated before `deepcopy` and before the authorized branch. A valid CLEAN still raises the existing `NotImplementedError` |

`AuthorityStatus` is `(str, Enum)`; its members are `str` subclass instances.
D1's exact-enum branch is what keeps every existing fixture valid. An exact
`str` rule alone would reject them.

## 3. Normative behavior

```
_BY_NAME = {member.name: member for member in AuthorityStatus}   # exact str keys

normalize(value, field):
    if type(value) is AuthorityStatus:   return value
    if type(value) is str:
        member = _BY_NAME.get(value)     # exact str: no caller code runs
        if member is not None:           return member
        raise ValueError(<unknown-str message>)
    raise ValueError("invalid " + field)
```

- `type()` is used, not `isinstance`: `type()` ignores a spoofed `__class__`.
- For any value that is neither an exact enum member nor an exact `str`,
  nothing on the value is called or read.
- Results always carry a genuine `AuthorityStatus`.
- `evaluate_override` reads the field once, with a module-private sentinel
  default, so missing and `None` are distinguished internally and both
  rejected (D3).
- `mutate_schedule` has no missing case: `authority_status` is a required
  keyword argument, so omission is a `TypeError` raised by the signature.

Messages:

| Case | `evaluate_override` | `mutate_schedule` |
|---|---|---|
| Unknown exact `str` | `unknown ordinary_authority_status: <value>` (#53, unchanged) | `unknown authority_status: <value>` |
| Everything else rejected (including `None`, missing) | `invalid ordinary_authority_status` | `invalid authority_status` |

Formatting `<value>` is done only when the value is an exact `str`, which runs
no caller code. See Q1.

## 4. Open question for review

- **Q1.** D2 says "fixed message". #53 already fixed a message that includes
  the unknown value for exact `str` input, and its test asserts that text.
  Proposed: keep the #53 message for unknown exact `str` (no caller hooks are
  possible there) and use the fixed message for every other rejection.
  Alternative: one fixed message for all rejections, which changes the #53
  test expectation.

## 5. Planned RED cases

New test module (name proposed:
`test_phage_principle0_authority_status_type_v0_1.py`) converts the
characterization cases into contract cases. The hook recorder is cleared after
inputs are built and before each call.

`evaluate_override`:

| ID | Input | Expected |
|---|---|---|
| K1 | each `AuthorityStatus` member | CLEAN → APPLICABLE; others → NOT_APPLICABLE / BLOCKED; result carries the same member |
| K2 | each canonical name as exact `str` | Same as K1, result carries the genuine member |
| K3 | unknown exact `str` | `ValueError`, #53 message (per Q1) |
| R1 | explicit `None` | `ValueError("invalid ordinary_authority_status")` |
| R2 | key missing | Same as R1, separate test |
| R3 | `1`, `0`, `b"CLEAN"`, list, dict, object with `.name == "CLEAN"`, foreign enum CLEAN, object with `__str__` → CLEAN, object whose `.name` raises | `ValueError`, fixed message; recorder 0 |
| R4 | `str` subclasses: well-behaved CLEAN; REVOKED lying as CLEAN; raising `__hash__`; side-effecting `__hash__` | `ValueError`, fixed message; recorder 0; side effect not executed |
| R5 | non-`str` object spoofing `__class__` | `ValueError`, fixed message; recorder 0 |
| R6 | R1–R5 inputs with `schedule_status` = `SCHEDULE_UNRESOLVED` and = `SCHEDULE_MATCH` | `ValueError` (D4); valid inputs on those branches keep their current results with a genuine member |
| R7 | every non-raising result in this module | `type(result['authority_status']) is AuthorityStatus` |

`mutate_schedule`:

| ID | Input | Expected |
|---|---|---|
| M1 | `AuthorityStatus.AUTHORITY_REVOKED`; exact `"AUTHORITY_REVOKED"` | BLOCKED; schedule unchanged; result carries the genuine member |
| M2 | `AuthorityStatus.CLEAN`; exact `"CLEAN"` | `NotImplementedError` (unchanged) |
| M3 | `None` and the R3–R5 inputs | `ValueError("invalid authority_status")` raised before `deepcopy`: probed with a schedule object whose `__deepcopy__` records; recorder 0; schedule unchanged |
| M4 | unknown exact `str` | `ValueError("unknown authority_status: <value>")` |

Mutants to confirm test strength (scratch, not committed): `isinstance`
instead of `type`; `.name` / `str()` fallback retained; normalization after the
schedule branches; validation after `deepcopy`; message that formats the
rejected object.

Existing regressions must stay green unchanged: Emergency Override A–F and
the #53 cases (6/6), Schedule A–F (6/6).

CI: the RED PR adds the new module to a workflow (new workflow, or a step in
the two existing Principle 0 workflows; to be settled in that PR).

## 6. Compatibility

| Caller / test | Impact |
|---|---|
| Emergency Override fixtures A–F (enum members) | None |
| #53 normalization test (exact `"AUTHORITY_REVOKED"`) | None |
| #53 unknown-string test | None if Q1 keeps the #53 message; must change otherwise |
| Schedule fixture E (`AuthorityStatus.AUTHORITY_SCOPE_VIOLATION`) | None |
| Non-test callers | None found in repository-root Python modules |
| `None`, missing, non-`str`, `str` subclasses, foreign enums | Change by design: now `ValueError`, including on early-return branches |
| `mutate_schedule` result for exact canonical `str` | Now carries the genuine member instead of the raw `str` |
| `phage_principle0_schedule_v0_1` imports | Adds `from phage_authority_engine_v0_1 import AuthorityStatus` |
| `repro_principle0_authority_status_type_v0_1.py` | Its gap assertions fail after the fix; the fix PR removes it, and the report keeps the commit reference |

## 7. Non-claims

Closes only the authority-status type boundary of the two entries, at fixture
level. No change to runtime reachability claims, no general safe-traversal
claim for Principle 0 inputs, no CLAIMS_STATUS or maturity change.
