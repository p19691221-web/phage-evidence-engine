# Principle 0 authority-status typing — reproduction and severity assessment

Date: 2026-10-10 (Asia/Taipei). Baseline: main
`6eb0ee2` (merge of #103).
Origin: follow-up recorded after #53 ("None/non-str passthrough and str-subclass
hook risk, severity pending repro").
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
reachability**: whether any product path reaches the entry. Static check
(in the repro file): no non-test module imports either entry; both module
docstrings exclude Gateway, Tool Adapter and production execution; the
"permit" outcome is `effect_path = NOT_DETERMINED`, not an effect.

| ID | Finding | Fixture severity | Runtime reachability |
|---|---|---|---|
| P0-T1 | **Status laundering**: a `str` subclass carrying `AUTHORITY_REVOKED`, or a non-`str` object spoofing `__class__`, resolves to the genuine `AuthorityStatus.CLEAN` through hook-driven enum lookup. Result is APPLICABLE and indistinguishable from a real CLEAN downstream. | High | None today |
| P0-T2 | **Forged CLEAN accepted**: any non-`AuthorityStatus` object with `.name == "CLEAN"` or `__str__() == "CLEAN"` yields APPLICABLE; the forged object is returned as `authority_status`. | High (detectable downstream only by type check) | None today |
| P0-T3 | **Exception leakage**: a raising `.name` property or `__hash__` escapes as `RuntimeError`, not the contract's `ValueError`. Fails closed by accident. | Medium | None today |
| P0-T4 | **Hooks execute in normalization**: `__hash__` / `__eq__` / `__str__` of caller objects run, including side effects. | Medium | None today |
| P0-T5 | **Raw passthrough and None/missing conflation**: non-canonical values that block are returned as-is (result-shape contract expects `AuthorityStatus`); missing key and explicit `None` are indistinguishable. Outcome is BLOCKED. | Low | None today |
| P0-T6 | **`mutate_schedule` classifies forged CLEAN as authorized**. Today the authorized branch is unimplemented and raises, so no mutation occurs. | Low now; High once authorized mutation exists | None today |

Not a finding: exact unknown `str` → `ValueError` is the #53 contract.

Conclusion: the defects are real and reproducible at fixture level, including
two fail-open paths (P0-T1, P0-T2). They are not reachable from any product
path at `6eb0ee2`. They would become reachable as soon as either entry is wired
into a Gateway, tool-effect or authorized-mutation path, so they should be closed
before any such integration.

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

1. **Rejection mechanism**: raise `ValueError` (consistent with #53's unknown
   string) or return BLOCKED with `AUTHORITY_UNRESOLVED`.
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
| Non-test callers | none exist | None |
| Behavior for `None`, missing, non-`str`, `str` subclasses, foreign enums | — | Changes by design (decisions 1–3); none is covered by an existing test |
| Result shape | — | `authority_status` becomes always `AuthorityStatus`, matching the existing `assert_result_shape` expectation |

## 6. Recommendation

The fix is small (one normalization helper per module, or a shared one), but
four contract decisions in §4 change observable behavior. Recommended sequence:
short decision record (§4 items 1–4) → RED tests converted from this
characterization → fix → review. Not recommended: a direct small patch that
picks those answers implicitly.

## 7. Non-claims

No implementation change. No claim of runtime exploitability: no product path
reaches either entry at `6eb0ee2`. The hostile objects are in-process Python
objects; this does not assess any serialization boundary. CLAIMS_STATUS and
maturity unchanged.
