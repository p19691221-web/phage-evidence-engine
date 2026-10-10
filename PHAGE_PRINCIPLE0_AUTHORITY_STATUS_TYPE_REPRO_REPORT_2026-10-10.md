# Principle 0 authority-status typing — reproduction and severity assessment

Date: 2026-10-10 (Asia/Taipei). Baseline: main
`6eb0ee2` (merge of #103).
Origin: follow-up recorded after #53 ("None/non-str passthrough and str-subclass
hook risk, severity pending repro").
Revision 2 (same day): reachability wording limited to what was checked;
P0-T3 restated as caller-hook `RuntimeError` leakage. Decisions on §4 are in
PHAGE_PRINCIPLE0_AUTHORITY_STATUS_TYPE_DECISION_v0_1.md.
Scope: reproduction and assessment only. No Principle 0 implementation,
test, workflow, CLAIMS_STATUS or maturity change.

Evidence file: `repro_principle0_authority_status_type_v0_1.py`. It is a
characterization module: it asserts **current** behavior so each gap is
reproducible, and it is expected to fail once a fix lands. It is not a `test_*`
module and no workflow runs it.

Run: `python -m unittest -v repro_principle0_authority_status_type_v0_1`
Result: 18/18 pass on CPython 3.12.3 and 3.13.16. Existing regressions
unchanged: Emergency Override 6/6, Schedule 6/6.

The hook recorder is cleared after the request and grant are built and
immediately before the entry call, so recorded hooks belong to the call alone.

## 1. Affected entries

| Entry | Input | Normalization at 6eb0ee2 |
|---|---|---|
| `phage_principle0_emergency_override_v0_1.evaluate_override` | `request['ordinary_authority_status']` via `request.get` | `isinstance(v, str)` → `AuthorityStatus[v]` (KeyError → ValueError); then `_status_name(v)`: `None` → `"NONE"`, else `v.name` if present, else `str(v)`; compared with `"CLEAN"` |
| `phage_principle0_schedule_v0_1.mutate_schedule` | `authority_status` argument | `_status_name(v)` only; `"CLEAN"` reaches the authorized branch, which raises `NotImplementedError` (out of v0.1 scope) |

No other module contains `AuthorityStatus[...]` or a `_status_name` helper.

## 2. Observed behavior (`evaluate_override`, otherwise-valid request and grant)

| Input | Result | Result `authority_status` | Hooks during call |
|---|---|---|---|
| `AuthorityStatus.CLEAN` | APPLICABLE / NOT_DETERMINED | genuine CLEAN | none |
| exact `"CLEAN"` | APPLICABLE / NOT_DETERMINED | genuine CLEAN | none |
| exact `"AUTHORITY_REVOKED"` | NOT_APPLICABLE / BLOCKED | genuine REVOKED | none |
| exact unknown `str` | raises `ValueError` (#53 design) | — | none |
| `None` | NOT_APPLICABLE / BLOCKED | `None` (raw) | none |
| key missing | identical to `None` | `None` | none |
| `1`, `0`, `b"CLEAN"`, list, dict | NOT_APPLICABLE / BLOCKED | raw object | none |
| object with `.name == "CLEAN"`; foreign `Enum.CLEAN` | **APPLICABLE / NOT_DETERMINED** | raw forged object | none |
| object whose `__str__` returns `"CLEAN"` | **APPLICABLE / NOT_DETERMINED** | raw forged object | `__str__` |
| object whose `.name` raises | raises `RuntimeError` | — | `name` |
| non-`str` object spoofing `__class__ = str`, colliding with `"CLEAN"` | **APPLICABLE / NOT_DETERMINED** | **genuine CLEAN** | `__hash__`, `__eq__` |
| `str` subclass, value `"CLEAN"`, well-behaved | APPLICABLE / NOT_DETERMINED | genuine CLEAN | `__hash__`, `__eq__` |
| `str` subclass, value `"AUTHORITY_REVOKED"`, hash/eq lie as `"CLEAN"` | **APPLICABLE / NOT_DETERMINED** | **genuine CLEAN** | `__hash__`, `__eq__` |
| `str` subclass whose `__hash__` raises | raises `RuntimeError` | — | `__hash__` |
| `str` subclass with side effect in `__hash__`, value REVOKED | NOT_APPLICABLE / BLOCKED | genuine REVOKED | side effect executed |

`mutate_schedule`: `AuthorityStatus.AUTHORITY_REVOKED` and `None` → BLOCKED,
schedule unchanged. `AuthorityStatus.CLEAN` and every forged CLEAN
(`.name`, foreign enum, `__str__`, `str` subclass) → `NotImplementedError`,
schedule unchanged.

Early-return branches (`SCHEDULE_UNRESOLVED`, schedule not `NO_MATCH`) return
the normalized-or-raw value without classifying it, so raw objects and laundered
values also pass through there; those branches do not grant.

## 3. Findings and severity

Severity has two axes. **Fixture severity**: effect on the module's own
fail-closed contract, judged from reproduced results. **Runtime
reachability**: whether a product path reaches the entry.

What was checked for reachability, and its limit: the repro file scans the
repository-root `*.py` files for the two module names and finds no reference
outside `test_*` / `repro_*` files. It does not scan subdirectories,
non-Python callers, dynamic imports or deployments outside this repository.
Both module docstrings exclude Gateway, Tool Adapter and production
execution, and the "permit" outcome is `effect_path = NOT_DETERMINED`, not an
effect. Runtime reachability is therefore **not established** either way;
this report does not claim it is unreachable.

| ID | Finding | Fixture severity | Runtime reachability |
|---|---|---|---|
| P0-T1 | **Status laundering**: a `str` subclass carrying `AUTHORITY_REVOKED`, or a non-`str` object spoofing `__class__`, resolves to the genuine `AuthorityStatus.CLEAN` through hook-driven enum lookup. Result is APPLICABLE and indistinguishable from a real CLEAN downstream. | High | Not established |
| P0-T2 | **Forged CLEAN accepted**: any non-`AuthorityStatus` object with `.name == "CLEAN"` or `__str__() == "CLEAN"` yields APPLICABLE; the forged object is returned as `authority_status`. | High (detectable downstream only by type check) | Not established |
| P0-T3 | **Caller-hook `RuntimeError` leakage**: an exception raised by the caller's own `.name` property or `__hash__` escapes from the entry as `RuntimeError`. No result is returned, so nothing is granted, but the failure mode is determined by the caller object. (The rejection mechanism for non-canonical types was not yet decided at `6eb0ee2`; this is not stated as a violation of a `ValueError` contract for those types.) | Medium | Not established |
| P0-T4 | **Hooks execute in normalization**: `__hash__` / `__eq__` / `__str__` of caller objects run, including side effects. | Medium | Not established |
| P0-T5 | **Raw passthrough and None/missing conflation**: non-canonical values that block are returned as-is (result-shape contract expects `AuthorityStatus`); missing key and explicit `None` are indistinguishable. Outcome is BLOCKED. | Low | Not established |
| P0-T6 | **`mutate_schedule` classifies forged CLEAN as authorized**. Today the authorized branch is unimplemented and raises, so no mutation occurs. | Low now; High once authorized mutation exists | Not established |

Not a finding: exact unknown `str` → `ValueError` is the #53 contract. #53
settled only that case; rejection of other types was undecided at
`6eb0ee2`.

Conclusion: the defects are real and reproducible at fixture level, including
two fail-open paths (P0-T1, P0-T2). Among the repository-root Python modules
checked, no non-test reference to either entry was found; runtime reachability
is not established. Any wiring of either entry into a Gateway, tool-effect or
authorized-mutation path would expose these paths, so they should be closed
before such integration.

## 4. Proposed direction: exact-type acceptance

Accept only:

- an exact `AuthorityStatus` member (`type(v) is AuthorityStatus`), or
- an exact `str` (`type(v) is str`) that equals a canonical member name, looked
  up in a module-level `{name: member}` map built from exact `str` keys.

Everything else is rejected without calling any method of the value (no
`isinstance`, `hasattr`, `str()`, hashing or comparison of the caller object).
Results always carry a genuine `AuthorityStatus`.

Note: `AuthorityStatus` is `(str, Enum)`, so its members are `str` subclass
instances. A plain `type(v) is str` rule would reject the enum members that all
current fixtures use; the exact-enum branch is required.

Decisions needed before RED (spec questions, not settled here):

1. **Rejection mechanism** for types other than exact unknown `str` (#53):
   raise `ValueError`, or return BLOCKED with `AUTHORITY_UNRESOLVED`.
2. **`None` and missing**: same as other rejected values, or a distinct
   classification (e.g. `AUTHORITY_UNRESOLVED`), and whether missing stays
   indistinguishable from `None`.
3. **Early-return branches**: normalize before the schedule-status branches
   (so they never return raw values), which changes what those branches return
   for non-canonical input.
4. **`mutate_schedule`**: apply the same rule, so forged CLEAN is rejected
   before the authorized branch.

## 5. Compatibility impact of exact-type acceptance

| Caller / test | Input used | Impact |
|---|---|---|
| Emergency Override fixtures A–F | `AuthorityStatus` members | None |
| #53 normalization test | exact `"AUTHORITY_REVOKED"` | None |
| #53 unknown-string test | exact `"NOT_A_REAL_AUTHORITY_STATUS"` → `ValueError` | None if decision 1 keeps `ValueError`; must change if decision 1 returns BLOCKED |
| Schedule fixtures A–F (fixture E) | `AuthorityStatus.AUTHORITY_SCOPE_VIOLATION` | None |
| Non-test callers | none found in repository-root Python modules | None found |
| Behavior for `None`, missing, non-`str`, `str` subclasses, foreign enums | — | Changes by design (decisions 1–3); none is covered by an existing test |
| Result shape | — | `authority_status` becomes always `AuthorityStatus`, matching the existing `assert_result_shape` expectation |

## 6. Recommendation

The fix is small (one normalization helper per module, or a shared one), but
four contract decisions in §4 change observable behavior. Recommended sequence:
short decision record (§4 items 1–4) → RED tests converted from this
characterization → fix → review. Not recommended: a direct small patch that
picks those answers implicitly.

## 7. Non-claims

No implementation change. No claim about runtime exploitability in either
direction: the static check covers repository-root Python modules only, and
runtime reachability is not established. The hostile objects are in-process
Python objects; this does not assess any serialization boundary. CLAIMS_STATUS
and maturity unchanged.
