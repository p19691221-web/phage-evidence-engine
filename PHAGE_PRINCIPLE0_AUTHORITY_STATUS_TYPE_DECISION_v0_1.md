# Principle 0 authority-status type boundary — decision record v0.1

Status: DRAFT FOR REVIEW rev 2, NOT FROZEN. Prepared 2026-10-10 (Asia/Taipei).
Rev 2: Q1 resolved; M1 widened, signature `TypeError` control added; M4 ordering;
CI deferred to the fix PR; §7 wording.
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
| D2 | Rejection | Always `ValueError`. An unknown exact `str` keeps the #53 message, which includes that string. Every other rejected value gets a fixed message with no part of the value in it. For any value that is not an exact `AuthorityStatus` member or an exact `str`: no formatting, no `.name`, no `str()`, no hashing, no comparison (Q1, resolved) |
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
no caller code (Q1).

## 4. Resolved question

- **Q1 (resolved 2026-10-10).** D2's fixed message applies to every rejection
  except an unknown exact `str`, which keeps the #53 message
  `unknown ordinary_authority_status: <value>` (and, for `mutate_schedule`,
  `unknown authority_status: <value>`). Rationale: formatting an exact `str`
  runs no caller code, and the existing #53 test stays valid. The alternative
  (one fixed message for all rejections) was not adopted.

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
| M1 | every non-CLEAN member (`AUTHORITY_UNRESOLVED`, `AUTHORITY_SCOPE_VIOLATION`, `AUTHORITY_REVOKED`, `AUTHORITY_EXPIRED`), each as the enum member and as its exact `str` name | BLOCKED; schedule unchanged; result carries the genuine member |
| M2 | `AuthorityStatus.CLEAN`; exact `"CLEAN"` | `NotImplementedError` (unchanged) |
| M3 | `None` and the R3–R5 inputs | `ValueError("invalid authority_status")` raised before `deepcopy`: probed with a schedule object whose `__deepcopy__` records; recorder 0; schedule unchanged |
| M4 | unknown exact `str` | `ValueError("unknown authority_status: <value>")` raised before `deepcopy` (same recording-schedule probe as M3); schedule unchanged |
| M5 | `authority_status` omitted | `TypeError` from the keyword-only signature (control: not a `ValueError` path); schedule unchanged |

Mutants to confirm test strength (scratch, not committed): `isinstance`
instead of `type`; `.name` / `str()` fallback retained; normalization after the
schedule branches; validation after `deepcopy`; message that formats the
rejected object.

Existing regressions must stay green unchanged: Emergency Override A–F and
the #53 cases (6/6), Schedule A–F (6/6).

CI: deferred to the fix PR. The RED PR adds no workflow and records its
results from manual runs (surface/semantic RED, per the established
practice), so merging RED alone does not turn main red. The fix PR adds the
new module to CI (a new workflow or a step in the existing Principle 0
workflows, settled there) and keeps its own semantic RED → GREEN record.

## 6. Compatibility

| Caller / test | Impact |
|---|---|
| Emergency Override fixtures A–F (enum members) | None |
| #53 normalization test (exact `"AUTHORITY_REVOKED"`) | None |
| #53 unknown-string test | None (Q1 keeps the #53 message) |
| Schedule fixture E (`AuthorityStatus.AUTHORITY_SCOPE_VIOLATION`) | None |
| Non-test callers | None found in repository-root Python modules |
| `None`, missing, non-`str`, `str` subclasses, foreign enums | Change by design: now `ValueError`, including on early-return branches |
| `mutate_schedule` result for exact canonical `str` | Now carries the genuine member instead of the raw `str` |
| `phage_principle0_schedule_v0_1` imports | Adds `from phage_authority_engine_v0_1 import AuthorityStatus` |
| `repro_principle0_authority_status_type_v0_1.py` | Its gap assertions fail after the fix; the fix PR removes it, and the report keeps the commit reference |

## 7. Non-claims

Defines the intended fix for the authority-status type boundary of the two
entries, at fixture level. Nothing is implemented yet; no gap is closed by
this record. No change to runtime reachability claims, no general safe-traversal
claim for Principle 0 inputs, no CLAIMS_STATUS or maturity change.
