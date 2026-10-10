# Offline record validator — contract v0.1

Status: FROZEN at rev 3. Contract-consistency review passed 2026-10-11
(Asia/Taipei); in effect from the merge of the PR that adds this file.
Prepared 2026-10-10, revised 2026-10-11. After freeze, content changes only
through an errata record or a new version.
Baseline: main `c270cac` (merge of #106).
Implementation / tests: NOT STARTED. No implementation branch, no code.

Sequence: contract review → **freeze (this record)** → RED tests →
implementation → re-review.

Freeze scope: the review covered the internal consistency of this contract.
Fit to customer data (data availability) and Problem Adoption are not covered
and remain unverified (§2.3).

## 0. Revision log

rev 2 closes the review of rev 1 (2026-10-10):

| Item | rev 1 defect | rev 2 location |
|---|---|---|
| R1 | COMPLETE read as "ready for the next step"; §7 called the schema a minimum | §1, §2.3, §10 |
| R2 | `FIELD_MISSING` applied to "any field", including optional `ext` and `source.digest`; `ext: null` undefined | §3.4, §3.6, §5.1 |
| R3 | Reference string format undefined; malformed references were resolved; duplicate index scope unstated | §3.3, §5.3 |
| R4 | B3-before-B4 and "no `RecursionError`" were not implementable together with a standard decoder; depth, empty containers and key counting undefined | §4 |
| R5 | `1e400`, floats in `ext`, escaped lone surrogates, string and integer budgets, and Python's integer-conversion limit unaddressed | §3.8, §4.2 |
| R6 | "RFC 3339" stated while rejecting forms RFC 3339 allows; profile not explicit | §3.7 |
| R7 | Granularity of `FIELD_UNKNOWN` and `SOURCE_MALFORMED`, unknown-type handling, summary key set, and `INTERNAL_ERROR` scope unstated | §5, §6, §7 |
| — | "Report carries no customer data" overstated: a `record_id` can itself be sensitive | §6.2 |
| — | Q1–Q6 resolved | §11 |
| — | Case list renumbered; count stated by case ID | §9 |

rev 3 closes the review of rev 2 (2026-10-11):

| Item | rev 2 defect | rev 3 location |
|---|---|---|
| P1 | Beyond `MAX_DEPTH` phase 1 "checked grammar only", but fractions, exponents and lone surrogates are grammatical JSON and are B3 here | §4.1, OV-B16 |
| P2 | Phase 1 said it "builds no values", yet duplicate detection needs unescaped keys; key retention after a key-count or key-length overrun unstated | §4.1, OV-B17 |
| P3 | "Always reads to the end" implied error recovery after a grammar error | §4.1, §4.2 |
| P4 | `TypeError` message not fixed; bytes subclasses and hook-free rejection not tested | §3.1, OV-B1 |
| P5 | OV-B5 and OV-B7 lost their escape sequences when written: the file showed `"a"` and a literal emoji instead of the escaped forms | §9, OV-B5, OV-B7 |

## 1. Purpose

Pilot 1 (internal audit sidecar, offline) will eventually ask of a record
bundle: did any operation execute after the authorization it relied on was
revoked or had expired? This validator does not ask that. It checks **field
format, source locators and missingness** against the format defined here.

A COMPLETE result means only that the bundle meets this format's structural
requirements. Whether a bundle is sufficient to answer any particular question
is decided separately. A bundle holding a single well-formed grant is COMPLETE
and answers nothing about post-revocation operations (OV-A4).

## 2. Scope

### 2.1 In scope

| Check | Meaning |
|---|---|
| Format | Each field has the declared JSON type and syntax: identifiers, the timestamp profile (§3.7), enumerated literals, lengths |
| Source locator | Each record carries `source.system` and `source.locator`; optional `source.digest` is syntax-checked only |
| Missingness | Absent required fields, fields declared unavailable (`null`), empty bundles, references to IDs not in the bundle |

### 2.2 Out of scope (normative: the validator must not do these)

| Not done | Reason |
|---|---|
| Decide whether any authorization was valid, in force or applicable | Adjudication, not structure |
| Emit ALLOW / DENY, or any verdict on an operation | Pilot 1 hard limit |
| Compare any two timestamps, within a record or across records | Comparison belongs to adjudication; e.g. `effective_at` earlier than `occurred_at` is not flagged |
| Treat `TASK_CANCELLATION` as, or infer from it, an `AUTHORIZATION_REVOCATION` | Cancelling work and withdrawing authority are different events (§5.4) |
| Judge whether a declared `grant_kind` (a ticket assignment, a PR approval) is in fact an authorization | The mapping declares it; the validator checks only that it is declared |
| Infer an executor, or an authorization relationship, from `AGENT_RUN` | Structural record only (§11 Q6) |
| Dereference a locator, fetch a source, or verify a digest | Offline; a locator is a caller-supplied pointer, not verified origin |
| Count operations after revocation or expiry | Same as the first row |

### 2.3 Separate gates

Three questions stay separate, and this validator tests only the first:

1. Does a given bundle meet this format? (this validator)
2. Can a customer produce such a bundle from their records at all? (data
   availability; tested only with customer data)
3. Does the customer have the problem and want it solved? (Problem Adoption)

The schema in §3 is a candidate. It has not been checked against any customer's
records.

## 3. Input format

### 3.1 Entry

Proposed `validate_bundle(raw) -> dict`, in a new module (name settled at RED;
proposed `phage_offline_record_validator_v0_1.py`).

- `raw` must be exactly `bytes` (`type(raw) is bytes`). Anything else, including
  a `bytes` subclass, raises `TypeError("raw must be bytes")` before any other
  work. The check reads only `type(raw)`: no method, attribute or property of
  `raw` is called, including `__class__`, `__len__`, `__eq__`, `__hash__` and
  `decode`. This is caller misuse, not a bundle finding.
- The validator parses the bytes itself (§4). It accepts no pre-parsed Python
  objects, so it never runs caller-defined methods.

### 3.2 Bundle

Only the normalized bundle below is accepted (§11 Q1). Mapping from native logs
(ticketing, Git hosting, CI, IAM) is out of scope. It is done by the customer or
analyst, and each normalized record points back to its native record through
`source.locator`.

```json
{
  "bundle_version": "phage.offline_records.v0.1",
  "bundle_id": "<identifier>",
  "records": [ { "...": "record" } ]
}
```

Top-level keys are exactly these three. `bundle_id` follows §3.3. `records` is a
list.

### 3.3 Identifiers and references

An identifier is a `str` of 1–128 characters, each in ASCII
`[A-Za-z0-9._:-]`. The rule applies to `bundle_id`, `record_id`, and every
reference field (`grant_ref`, `run_ref`, `authorization_ref`). A reference names
a `record_id` in the same bundle.

### 3.4 Record envelope (all record types)

| Field | Required | Type / format | `null` allowed |
|---|---|---|---|
| `record_type` | Yes | one of §3.5 | No |
| `record_id` | Yes | identifier | No |
| `occurred_at` | Yes | timestamp (§3.7) | Yes |
| `source` | Yes | object: `system`, `locator`, optional `digest`, no other key | No |
| `source.system` | Yes | `str`, 1–128 chars | No |
| `source.locator` | Yes | `str`, 1–1024 chars | No |
| `source.digest` | No | `sha256:` + 64 lowercase hex | No (omit instead) |
| `ext` | No | object; contents not inspected beyond §4 | No (omit instead) |

### 3.5 Record types and type-specific fields

All fields in this table are required. "`null` allowed" means the key must be
present, and may hold `null` to declare the value unavailable.

| `record_type` | Field | Type / format | `null` allowed |
|---|---|---|---|
| `AUTHORIZATION_GRANT` | `grant_kind` | `str`, 1–128 chars, declared by the mapping | No |
| | `scope_ref` | `str`, 1–1024 chars, opaque | Yes |
| | `valid_until` | timestamp (§3.7), or the literal `"NO_EXPIRY"` | Yes |
| `AUTHORIZATION_REVOCATION` | `grant_ref` | reference to an `AUTHORIZATION_GRANT` | No |
| | `revocation_kind` | `str`, 1–128 chars | No |
| | `effective_at` | timestamp (§3.7) | Yes |
| `TASK_CANCELLATION` | `task_ref` | `str`, 1–1024 chars, opaque (not a reference) | No |
| | `cancellation_kind` | `str`, 1–128 chars | No |
| `AGENT_RUN` | `task_ref` | `str`, 1–1024 chars, opaque | Yes |
| | `ended_at` | timestamp (§3.7) | Yes |
| `OPERATION` | `run_ref` | reference to an `AGENT_RUN` | Yes |
| | `authorization_ref` | reference to an `AUTHORIZATION_GRANT` | Yes |
| | `operation_kind` | `str`, 1–128 chars | No |
| | `target_ref` | `str`, 1–1024 chars, opaque | Yes |

A known type accepts exactly the envelope fields plus its own fields. Any other
key is an unknown field (§5.2).

For `OPERATION`, `occurred_at` is the execution time recorded by the source. For
`AUTHORIZATION_REVOCATION`, `occurred_at` is when the revocation was recorded and
`effective_at` is when the source says it took effect. Both are kept because they
can differ; the validator does not compare them.

`"NO_EXPIRY"` records that the source, as mapped, declares no expiry. The
validator does not check whether that declaration is true (§11 Q3).

### 3.6 Field states

| State | Applies to | Encoding | Finding |
|---|---|---|---|
| Present | any field | value of the declared type and format | none |
| Missing | required fields only | key absent | `FIELD_MISSING` |
| Declared unavailable | fields marked `null` allowed | `null` | `FIELD_DECLARED_UNAVAILABLE` |
| Malformed | any field | wrong type or format, or `null` where not allowed | `FIELD_MALFORMED` |

An absent optional field (`ext`, `source.digest`) produces no finding. Two
required fields have their own codes: an absent `record_type` is
`RECORD_TYPE_UNKNOWN`, and an absent `source` is `SOURCE_MISSING` (§5.1).

### 3.7 Timestamp profile

This is a fixed profile, narrower than RFC 3339. Rejecting a form is a format
decision. `FIELD_MALFORMED` does not claim that the source's time is wrong.

```
YYYY-MM-DD "T" hh:mm:ss [ "." 1*9DIGIT ] ( "Z" / ( "+" / "-" ) HH:MM )
```

| Rule | Accepted | Rejected |
|---|---|---|
| Digits | ASCII `0`–`9` only | any other Unicode digit |
| Separator | uppercase `T` | `t`, space |
| UTC designator | uppercase `Z`, or `+00:00` | `z` |
| Date | year 0001–9999; a valid Gregorian date, including 29 February in leap years | year 0000, month 13, `2026-02-29` |
| Time | hour 00–23, minute 00–59, second 00–59; seconds required | second `60` (no leap seconds), `hh:mm` without seconds |
| Fraction | 1–9 digits after `.` | `.` with no digits, 10 or more digits |
| Offset | `±HH:MM`, HH 00–23, MM 00–59 | `-00:00` (RFC 3339 §4.3: offset unknown), `+24:00`, `+08:60`, `+0800`, no offset, date only |

Each check concerns one field. No two timestamps are compared.

### 3.8 Budgets

These are engineering budgets for this validator. They make no claim about the
size of any customer's data (§11 Q4).

| Budget | Value | Applies to |
|---|---|---|
| `MAX_BUNDLE_BYTES` | 16 MiB (16 777 216) | raw input |
| `MAX_DEPTH` | 32 | container nesting (§4.1) |
| `MAX_OBJECT_KEYS` | 64 | key occurrences per object, duplicates included |
| `MAX_STRING_CHARS` | 1024 | every string, key or value, in code points after unescaping; a surrogate pair counts as one |
| Integer range | −2^63 … 2^63−1 | every integer |
| `MAX_RECORDS` | 10 000 | `len(records)` |

Numbers with a fraction or an exponent are not part of this format (§4.2), so a
value such as `1e400` never reaches numeric conversion.

Because `MAX_STRING_CHARS` equals the 1024-character field limits, an over-long
locator or opaque reference is a bundle-level `BUNDLE_LIMIT_EXCEEDED`, never a
record-level finding. The 128-character limits are checked per field.

## 4. Parsing and bundle-level rules

### 4.1 Two phases

**Phase 1** scans the decoded text once, iteratively, with an explicit stack.
It does not build a JSON value tree. It keeps only parse state and the key data
that duplicate detection needs (below).

Termination: phase 1 stops at the first B3 condition, since B3 is then
certain; no error recovery is defined or needed. A B4 condition does not stop
it: the scan continues until a B3 condition is found or the input ends. The
result therefore does not depend on where in the document a condition occurs.

- Depth: each object or array, including an empty one, is one level. The
  outermost container is depth 1; scalars add no depth. In a well-formed bundle
  the top object is depth 1, `records` 2, a record 3, `source` and `ext` 4.
- Key data: for every open object at depth ≤ `MAX_DEPTH`, phase 1 keeps the
  unescaped form of each key seen so far. It keeps doing so after that object
  exceeds `MAX_OBJECT_KEYS`, and for keys longer than `MAX_STRING_CHARS`, so a
  later duplicate is still detected and still takes B3 precedence. Memory stays
  bounded by input size.
- Beyond `MAX_DEPTH` the input is already B4. There phase 1 keeps one byte of
  stack per level and still applies every token rule of B3: grammar, control
  characters, escapes, lone surrogates, fractions, exponents and `NaN` /
  `Infinity`. It omits only duplicate-key detection and the budget accounting
  that can no longer change the result (key counts, string lengths, integer
  range).

**Phase 2** runs only if phase 1 found no B3 or B4 condition. It builds the value
with the standard decoder, with duplicate-key and constant hooks kept as a second
line of defense. Depth is then at most `MAX_DEPTH`, so no recursion limit can be
reached. If phase 2 rejects something phase 1 accepted, that is a validator
defect and yields `INTERNAL_ERROR` (§7).

### 4.2 Bundle-level checks

| Order | Phase | Condition | Code |
|---|---|---|---|
| B1 | pre | `len(raw) > MAX_BUNDLE_BYTES` | `BUNDLE_LIMIT_EXCEEDED` |
| B2 | pre | not strict UTF-8 (including encoded surrogates), or a leading BOM | `BUNDLE_MALFORMED` |
| B3 | 1 | any of: RFC 8259 grammar error (including trailing data, unescaped control characters, invalid escapes); an escaped surrogate not part of a valid pair; a number with a fraction or exponent; `NaN` / `Infinity` literals; a duplicate key, compared after unescaping, in an object at depth ≤ `MAX_DEPTH` | `BUNDLE_MALFORMED` |
| B4 | 1 | any of: depth > `MAX_DEPTH`; an object with more than `MAX_OBJECT_KEYS` key occurrences; a string over `MAX_STRING_CHARS`; an integer outside the integer range | `BUNDLE_LIMIT_EXCEEDED` |
| B5 | 2 | top level not an object; keys not exactly §3.2; wrong `bundle_version`; `bundle_id` not an identifier; `records` not a list | `BUNDLE_MALFORMED` |
| B6 | 2 | `len(records) > MAX_RECORDS` | `BUNDLE_LIMIT_EXCEEDED` |

Precedence:

- B1 and B2 run before phase 1, in that order.
- Phase 1 returns B3 at the first B3 condition. Otherwise, if it recorded any
  B4 condition by the end of the input, the result is B4. Position in the
  document does not matter.
- B3 token rules apply at every depth. Only duplicate-key detection is limited
  to depth ≤ `MAX_DEPTH`; a duplicate key deeper than that is not detected, and
  such input is B4.
- Duplicate detection continues after an object exceeds `MAX_OBJECT_KEYS` and
  for keys over `MAX_STRING_CHARS`.
- Integer range is decided from the digit count before conversion: more than 19
  digits is out of range without converting. Otherwise the token is converted
  and compared. No integer can reach Python's string-conversion limit.
- The first hit among B1, B2, B5 and B6 ends evaluation. No record is evaluated
  after any bundle-level finding.

An empty `records` list is not a bundle-level rejection. It yields `BUNDLE_EMPTY`
and status INCOMPLETE: no records is an unknown, not a zero.

## 5. Record-level rules

### 5.1 Checks

Every record is checked, and findings accumulate. Each field gets at most one
finding.

| Code | Condition | Field | Class |
|---|---|---|---|
| `RECORD_NOT_OBJECT` | record is not an object | `null` | MALFORMED |
| `RECORD_TYPE_UNKNOWN` | `record_type` absent, not a `str`, or not in §3.5 | `record_type` | MALFORMED |
| `RECORD_ID_DUPLICATE` | the same well-formed `record_id` appears on more than one record; every occurrence gets it | `record_id` | MALFORMED |
| `FIELD_MALFORMED` | §3.6 | the field | MALFORMED |
| `FIELD_UNKNOWN` | §5.2 | `null` | MALFORMED |
| `SOURCE_MALFORMED` | `source` present but not per §3.4 | `source` | MALFORMED |
| `REFERENCE_AMBIGUOUS` | §5.3 | the reference field | MALFORMED |
| `REFERENCE_TYPE_MISMATCH` | §5.3 | the reference field | MALFORMED |
| `FIELD_MISSING` | required field absent (not `record_type`, not `source`) | the field | INCOMPLETE |
| `SOURCE_MISSING` | `source` absent | `source` | INCOMPLETE |
| `FIELD_DECLARED_UNAVAILABLE` | `null` where allowed | the field | INCOMPLETE |
| `REFERENCE_UNRESOLVED` | §5.3 | the reference field | INCOMPLETE |

Class rule: absence is INCOMPLETE and wrong form is MALFORMED. The one exception
is an absent `record_type`, which is MALFORMED because no schema can be applied
without it.

Granularity:

- `SOURCE_MALFORMED` is reported once per record, however many defects
  `source` has, including a missing key, an extra key, or `digest: null`.
- `ext: null`, or `ext` of any type other than object, is `FIELD_MALFORMED` on
  `ext`.

### 5.2 Unknown fields and unknown types

- For a known type, each key outside its field set gets one `FIELD_UNKNOWN`
  with `field: null`. Two unknown keys give two findings. Key names are not
  reported.
- For an unknown type (`RECORD_TYPE_UNKNOWN`), only the envelope fields of
  §3.4 are checked. No type-specific field is checked and no `FIELD_UNKNOWN` is
  reported, since there is no schema to compare against.

### 5.3 References

1. A reference value that is not an identifier (§3.3) is `FIELD_MALFORMED`. It is
   not resolved.
2. `null` where allowed is `FIELD_DECLARED_UNAVAILABLE`, and is not resolved.
3. Otherwise the reference is resolved against an index of every record that is
   an object with a well-formed `record_id`, including records of unknown type.
   Records with a malformed or absent `record_id` are not indexed. Position does
   not matter, so forward references resolve.
4. Outcome, first match wins:
   - zero matches: `REFERENCE_UNRESOLVED`;
   - two or more matches: `REFERENCE_AMBIGUOUS`. No type is checked, even if the
     matches have different types;
   - one match whose `record_type` is not the expected type, including an unknown
     type: `REFERENCE_TYPE_MISMATCH`;
   - one match of the expected type: no finding, even if that target record is
     itself MALFORMED. The target's own findings stand separately.

`RECORD_ID_DUPLICATE` is likewise computed only among well-formed IDs. Two
records with the same malformed `record_id` each get `FIELD_MALFORMED`, not
`RECORD_ID_DUPLICATE`.

### 5.4 Cancellation is not revocation

- `TASK_CANCELLATION` is checked against its own schema only.
- It has no `grant_ref` field. A `grant_ref` key on it is `FIELD_UNKNOWN`, so a
  cancellation cannot be linked to a grant through this format.
- A revocation whose `grant_ref` resolves to a `TASK_CANCELLATION` is
  `REFERENCE_TYPE_MISMATCH`.
- The summary counts the two types separately and never adds one to the other.

### 5.5 Status

A record with any MALFORMED-class finding is MALFORMED; otherwise, with any
INCOMPLETE-class finding, INCOMPLETE; otherwise COMPLETE.

| Bundle status | Condition |
|---|---|
| `REJECTED` | any of B1–B6 |
| `INTERNAL_ERROR` | §7 |
| `MALFORMED` | any record MALFORMED |
| `INCOMPLETE` | no record MALFORMED; any record INCOMPLETE, or `BUNDLE_EMPTY` |
| `COMPLETE` | at least one record, and every record COMPLETE |

## 6. Report

### 6.1 Shape

```json
{
  "report_version": "phage.offline_records.report.v0.1",
  "structural_status": "COMPLETE | INCOMPLETE | MALFORMED | REJECTED | INTERNAL_ERROR",
  "bundle_findings": [ { "code": "..." } ],
  "records": [
    { "index": 0,
      "record_id": "<well-formed record_id> | null",
      "record_type": "<known record_type> | null",
      "status": "COMPLETE | INCOMPLETE | MALFORMED",
      "findings": [ { "code": "...", "field": "<schema field name> | null" } ] }
  ],
  "summary": {
    "records_total": 0,
    "by_type": { "AUTHORIZATION_GRANT": 0, "AUTHORIZATION_REVOCATION": 0,
                 "TASK_CANCELLATION": 0, "AGENT_RUN": 0, "OPERATION": 0,
                 "UNKNOWN": 0 },
    "by_status": { "COMPLETE": 0, "INCOMPLETE": 0, "MALFORMED": 0 }
  }
}
```

- `bundle_findings` is empty or holds exactly one code: a B1–B6 code,
  `BUNDLE_EMPTY` or `INTERNAL_ERROR`. With a B1–B6 code or `INTERNAL_ERROR`,
  `records` is empty and every count is zero.
- `summary` always contains all six `by_type` keys and all three `by_status`
  keys, zeros included, for every status. A record that is not an object, or is
  of unknown type, is counted under `UNKNOWN`.
- Records appear in input order. Within a record, findings follow field order:
  `record_type`, `record_id`, `occurred_at`, `source`, `ext`, then the type's
  fields in §3.5 order, then all `FIELD_UNKNOWN` findings. `RECORD_NOT_OBJECT`
  is the only finding on its record.

### 6.2 Input values in the report

The report reproduces exactly two input-derived values: a well-formed
`record_id`, and a `record_type` that is one of §3.5. Analysts locate a native
record through the input index and that `record_id` (§11 Q5). No locator,
digest, timestamp, opaque reference, unknown key name, `ext` content or
malformed `record_id` appears.

This is minimization, not anonymization. A `record_id` can itself carry
sensitive information; the mapping step decides what it contains.

### 6.3 No verdict vocabulary

Report keys are a fixed allowlist. No key, status or code contains `allow`,
`deny`, `authoriz`, `valid`, `verified`, `compliant`, `violation`, `safe` or
`approved` (case-insensitive). Schema names are exempt: `field` values (e.g.
`valid_until`), and `record_type` values and `by_type` keys (e.g.
`AUTHORIZATION_GRANT`). They name what was mapped, not a finding about it.

## 7. Internal error boundary

- Covered: an `Exception` raised inside the validator after the `bytes` type
  check, other than `MemoryError`; and a phase 2 rejection of input phase 1
  accepted (§4.1). Either yields status `INTERNAL_ERROR` and the single bundle
  finding `INTERNAL_ERROR`, with no record results. It is never reported as
  MALFORMED, INCOMPLETE or COMPLETE (the G1/G2 split).
- Not covered and not promised: `MemoryError`, `KeyboardInterrupt`,
  `SystemExit`, other `BaseException`, interpreter or process failure. These
  propagate.
- Expected rejections are never `INTERNAL_ERROR`. Every parse and budget
  condition in §4 is classified as B1–B6, including depth 100 000 and a
  5000-digit integer.

RED needs fault-injection hooks for both covered paths to make them
deterministic.

## 8. Purity

The validator reads no clock, network, file system or environment, and has no
side effects. The same bytes give an identical report. Its correctness does not
depend on the current time, because it compares no timestamps.

## 9. Planned RED cases

62 case IDs. RED decides how case IDs map to test methods, and its record counts
case IDs, test methods and subtests separately. Each case asserts
`structural_status`, the exact `(code, field)` findings, and the summary.

**A. Controls**

| ID | Input | Expected |
|---|---|---|
| OV-A1 | one well-formed record of each type; references resolve | COMPLETE; zero findings |
| OV-A2 | OV-A1 plus `ext` nested to depth 32, integers at both range limits, a 1024-code-point string | COMPLETE; `ext` not reported |
| OV-A3 | `valid_until` = `"NO_EXPIRY"` | COMPLETE |
| OV-A4 | a single well-formed `AUTHORIZATION_GRANT` | COMPLETE (COMPLETE is not sufficiency) |
| OV-A5 | no `ext`, no `source.digest` anywhere | COMPLETE; no `FIELD_MISSING` |

**B. Bundle level**

| ID | Input | Expected |
|---|---|---|
| OV-B1 | `raw` is `str`, `bytearray`, `memoryview`, `None`; a `bytes` subclass instance whose `__class__`, `__len__`, `__eq__`, `__hash__`, `__iter__`, `__getitem__`, `__bytes__` and `decode` record each access | `TypeError("raw must be bytes")`, exact message; no report; recorder empty |
| OV-B2 | exactly 16 777 216 bytes (valid JSON padded with whitespace); one byte more | cap: evaluated; over: REJECTED / `BUNDLE_LIMIT_EXCEEDED` |
| OV-B3 | invalid UTF-8; leading BOM; encoded surrogate (`ED A0 80`) | REJECTED / `BUNDLE_MALFORMED` |
| OV-B4 | non-JSON; trailing data; trailing comma; single quotes; raw control character in a string | REJECTED / `BUNDLE_MALFORMED` |
| OV-B5 | duplicate key at top level, in a record, in `ext` at depth ≤ 32; one object with key `"a"` and key `"\u0061"`, the latter written as the six-character escape in the raw JSON bytes | REJECTED / `BUNDLE_MALFORMED` |
| OV-B6 | `NaN`, `Infinity`, `-Infinity`, `1.0`, `1e3`, `1e400` | REJECTED / `BUNDLE_MALFORMED` |
| OV-B7 | lone escapes `"\ud800"`, `"\udc00"`, `"\ud800x"`; escaped pair `"\ud83d\ude00"` written as twelve escape characters in the raw JSON bytes; the same character as direct UTF-8 bytes `F0 9F 98 80` | lone: `BUNDLE_MALFORMED`; escaped pair and UTF-8 form: evaluated, each one code point for §3.8 |
| OV-B8 | depth 32 and 33, counted with empty containers; arrays nested 100 000; objects nested 100 000 | 32: evaluated; 33 and deeper: `BUNDLE_LIMIT_EXCEEDED`; no exception |
| OV-B9 | object with 64 and 65 key occurrences | 64: evaluated; 65: `BUNDLE_LIMIT_EXCEEDED` |
| OV-B10 | string value and key of 1024 and 1025 code points, built with escapes and a surrogate pair | 1024: evaluated; 1025: `BUNDLE_LIMIT_EXCEEDED` |
| OV-B11 | `9223372036854775807`, `-9223372036854775808`, `9223372036854775808`, `-9223372036854775809`, a 5000-digit integer | in range: evaluated; others: `BUNDLE_LIMIT_EXCEEDED`, never `INTERNAL_ERROR` |
| OV-B12 | precedence: grammar error after a depth-40 region; grammar error before it; duplicate key only at depth 33; over-size bytes that are also invalid UTF-8 | `BUNDLE_MALFORMED`; `BUNDLE_MALFORMED`; `BUNDLE_LIMIT_EXCEEDED`; `BUNDLE_LIMIT_EXCEEDED` (B1) |
| OV-B13 | top level a list; a scalar; extra top-level key; no `records`; wrong `bundle_version`; malformed `bundle_id`; `records` an object | REJECTED / `BUNDLE_MALFORMED` |
| OV-B14 | 10 000 and 10 001 records | 10 000: evaluated; 10 001: `BUNDLE_LIMIT_EXCEEDED` |
| OV-B15 | `records: []` | INCOMPLETE; `BUNDLE_EMPTY`; counts zero |
| OV-B16 | inside a region nested to depth 33: `1.0`; `1e400`; `"\ud800"`; `NaN` | `BUNDLE_MALFORMED` each (B3 token rules apply beyond `MAX_DEPTH`) |
| OV-B17 | one object with 65 distinct keys; 65 keys where the 65th repeats the 1st; one key of 1025 code points; two identical keys of 1025 code points in one object | `BUNDLE_LIMIT_EXCEEDED`; `BUNDLE_MALFORMED`; `BUNDLE_LIMIT_EXCEEDED`; `BUNDLE_MALFORMED` |

**C. Envelope**

| ID | Input | Expected |
|---|---|---|
| OV-C1 | record is a string; a number; a list | `RECORD_NOT_OBJECT` only; `by_type.UNKNOWN` |
| OV-C2 | `record_id` absent; `null`; `""`; 129 chars; contains a space; contains a non-ASCII digit | absent: `FIELD_MISSING`; others: `FIELD_MALFORMED`; report `record_id` null |
| OV-C3 | two records with the same well-formed ID; two with the same malformed ID | first: both `RECORD_ID_DUPLICATE`; second: both `FIELD_MALFORMED`, no duplicate finding |
| OV-C4 | `record_type` absent; `"REVOCATION"`; `1`; each with an extra key and no `source` | `RECORD_TYPE_UNKNOWN` and `SOURCE_MISSING`; no `FIELD_UNKNOWN`; report `record_type` null |
| OV-C5 | `ext: null`; `ext: []` | `FIELD_MALFORMED` on `ext` |
| OV-C6 | known type with two unknown keys | two `FIELD_UNKNOWN`, `field` null; key names absent from report |

**D. Field states and format**

| ID | Input | Expected |
|---|---|---|
| OV-D1 | `effective_at` absent vs `null` | `FIELD_MISSING` vs `FIELD_DECLARED_UNAVAILABLE`; both INCOMPLETE |
| OV-D2 | `valid_until` absent / `null` / `"NO_EXPIRY"` | `FIELD_MISSING` / `FIELD_DECLARED_UNAVAILABLE` / none |
| OV-D3 | `null` in `grant_kind`, `revocation_kind`, `operation_kind` | `FIELD_MALFORMED` |
| OV-D4 | `true`, `1`, `[]`, `{}` in a `str` field | `FIELD_MALFORMED` |
| OV-D5 | `grant_kind` of 128 and 129 chars | 128: none; 129: `FIELD_MALFORMED` |
| OV-D6 | one record with malformed `occurred_at`, missing `operation_kind`, an unknown key and a malformed `source` | four findings, in §6.1 order |

**E. Timestamp profile**

| ID | Input | Expected |
|---|---|---|
| OV-E1 | `…T12:00:00Z`, `+00:00`, `+08:00`, `-05:30`; fraction of 1 and 9 digits; `2024-02-29` | no finding |
| OV-E2 | no offset; date only; space separator; lowercase `t`; lowercase `z`; `-00:00`; second `60`; 10-digit fraction; `.` without digits; `hh:mm` without seconds; `2026-02-29`; month 13; year 0000; `+24:00`; `+08:60`; `+0800`; non-ASCII digit; `"NO_EXPIRY"` in `occurred_at`; `"no_expiry"` in `valid_until` | `FIELD_MALFORMED` each |

**F. Source locator**

| ID | Input | Expected |
|---|---|---|
| OV-F1 | `source` absent | `SOURCE_MISSING`; INCOMPLETE |
| OV-F2 | `source` a string; `locator` empty; `system` absent; extra key; `digest: null` | one `SOURCE_MALFORMED` each |
| OV-F3 | `source` with three defects at once | exactly one `SOURCE_MALFORMED` |
| OV-F4 | `digest` uppercase hex; 63 hex; `md5:` prefix | `SOURCE_MALFORMED` |
| OV-F5 | well-formed `digest` | no finding; no report field implies verification |

**G. References**

| ID | Input | Expected |
|---|---|---|
| OV-G1 | `authorization_ref` names an ID not in the bundle | `REFERENCE_UNRESOLVED`; INCOMPLETE |
| OV-G2 | `authorization_ref` absent vs `null` | `FIELD_MISSING` vs `FIELD_DECLARED_UNAVAILABLE` |
| OV-G3 | reference with a space; of 129 chars; an integer | `FIELD_MALFORMED`; no resolution finding |
| OV-G4 | `run_ref` resolves to an `AUTHORIZATION_GRANT` | `REFERENCE_TYPE_MISMATCH` |
| OV-G5 | reference to a record later in the list | resolves; no finding |
| OV-G6 | reference resolves to a record of unknown type | `REFERENCE_TYPE_MISMATCH` |
| OV-G7 | ID duplicated on two records of the expected type; on one expected and one other type | `REFERENCE_AMBIGUOUS` in both; no type mismatch |
| OV-G8 | reference resolves to a MALFORMED record of the expected type | no finding on the referrer |

**H. Cancellation is not revocation**

| ID | Input | Expected |
|---|---|---|
| OV-H1 | grant, run, `TASK_CANCELLATION` for the run's task, then an operation | COMPLETE; `AUTHORIZATION_REVOCATION` 0, `TASK_CANCELLATION` 1 |
| OV-H2 | `TASK_CANCELLATION` carrying `grant_ref` | `FIELD_UNKNOWN`, `field` null |
| OV-H3 | revocation whose `grant_ref` resolves to a `TASK_CANCELLATION` | `REFERENCE_TYPE_MISMATCH` |

**I. No adjudication**

| ID | Input | Expected |
|---|---|---|
| OV-I1 | operation `occurred_at` after revocation `effective_at`, vs a twin bundle with it before | identical reports |
| OV-I2 | operation after grant `valid_until`, vs a twin before | identical reports |
| OV-I3 | revocation `effective_at` earlier than its own `occurred_at` | no finding |

**J. Report rules, purity, internal error**

| ID | Input | Expected |
|---|---|---|
| OV-J1 | a sentinel string placed in a locator, a digest-shaped value, an opaque ref, a timestamp field, an unknown key name, `ext`, and a malformed `record_id` | sentinel absent from the serialized report |
| OV-J2 | a well-formed `record_id` | reproduced exactly (minimization, not anonymization) |
| OV-J3 | every report produced by the module | keys within allowlist; §6.3 rule holds |
| OV-J4 | COMPLETE, INCOMPLETE, MALFORMED, REJECTED and INTERNAL_ERROR reports | all six `by_type` and three `by_status` keys present |
| OV-J5 | same bytes twice | equal reports (canonical serialization) |
| OV-J6 | clock, socket, `open` and `os.environ` access patched to raise | reports unchanged; no exception |
| OV-J7 | fault injected in record checking; phase 2 made to reject phase 1 output | `INTERNAL_ERROR`; only `INTERNAL_ERROR`; `records` empty |

Mutants to confirm test strength (scratch, not committed):

- count `TASK_CANCELLATION` as a revocation;
- collapse `null` into absent;
- report `FIELD_MISSING` for an absent optional field;
- stop at the first finding per record;
- resolve malformed references;
- index duplicate IDs by first occurrence;
- echo the locator;
- accept `-00:00` or a naive timestamp;
- skip phase 1 and rely on the standard decoder;
- stop duplicate detection once an object exceeds `MAX_OBJECT_KEYS`;
- apply only grammar, not B3 token rules, beyond `MAX_DEPTH`;
- convert integer tokens before the digit-count check;
- report `INTERNAL_ERROR` as MALFORMED;
- add a timestamp comparison that emits a finding.

## 10. Relation to existing work

| Item | Relation |
|---|---|
| Pilot 1 (offline sidecar, never ALLOW/DENY) | A precondition tool; it is not a pilot and does not start one |
| Interview question on linking grant, run and operation | §3.5 is a candidate schema for that question, not validated against customer data; data availability and Problem Adoption are separate gates (§2.3) |
| EVIDENCE_ORIGIN invariant | `source.locator` is caller-supplied; a well-formed locator does not make a record verified evidence |
| G1/G2 split | §7 |
| AISI-003 semantic-boundary assertion | §6.3 follows the same pattern |
| Safe-input lessons (#99–#106) | exact `bytes` entry; self-parsing; duplicate keys rejected; budgets tested at cap and cap+1 |

## 11. Resolved decisions (review of 2026-10-10)

| ID | Decision |
|---|---|
| Q1 | v0.1 accepts the normalized bundle only. Native adapters are out of scope |
| Q2 | A key outside the field set and outside `ext` is `FIELD_UNKNOWN`, class MALFORMED |
| Q3 | `"NO_EXPIRY"` is kept. It records the source's declaration only; its truth is not checked |
| Q4 | §3.8 values are adopted as engineering budgets. No claim that they fit customer data volumes |
| Q5 | The locator is not echoed. Analysts locate records by input index and well-formed `record_id` |
| Q6 | `AGENT_RUN` is kept as a structural record. No executor or authorization relationship is inferred from it |

## 12. Non-claims

Docs only. No implementation, test, workflow, CLAIMS_STATUS or maturity change.
A COMPLETE result is not evidence that any authorization was valid, that any
operation was permitted, that no operation followed a revocation or expiry, or
that a bundle suffices for any particular question. No customer data has been
examined, no pilot has started, and the report is not anonymized. Pilot remains
gated on external Problem Adoption.
