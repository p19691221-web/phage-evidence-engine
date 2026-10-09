# H/H′/N v0.2 and protected-use — implementation record

Date: 2026-10-09 (Asia/Taipei). Baseline: main
`7550ad1` (merge of #99, RED tests).
Interface: PHAGE_AUTHORITY_LINEAGE_HHN_EXECUTABLE_INTERFACE_v0_2.md, frozen
by #97, corrected by errata #98 (E1–E3). Tests: #99, unchanged in this PR.

Status: GREEN at fixture level. Not runtime enforcement closure (§8).

## 1. Commit sequence

| Commit | Content | Purpose |
|---|---|---|
| 1 | Fail-closed stubs for both modules (frozen signatures and constants only) + workflow `authority-lineage-hhn-v0_2.yml` | This PR's own semantic RED |
| 2 | `phage_authority_lineage_hhn_v0_2.py`, `phage_authority_protected_use_v0_1.py` | Implementation → GREEN |
| 3 | this record | Evidence |

Commit hashes are assigned when the series is applied; this record refers to
commits by position. No test, fixture, frozen document, v0.1 module or
CLAIMS_STATUS is changed.

## 2. Semantic RED (commit 1, own stub)

Stub behavior: frozen signatures and stage-0 `TypeError` checks; every other
call returns AUTHORITY_VERIFICATION_ERROR (inspection) or COMMIT_ERROR
(use-time) without calling any seam. This is distinct from the #99 diagnostic
baselines, which are not reused here.

Identical on CPython 3.13.16 and 3.12.3 (`python -m unittest -v <module>`):

| Suite | Tests | ok | FAIL methods | ERROR methods | Failures / errors | `SURFACE_RED` |
|---|---|---|---|---|---|---|
| hhn v0.2 | 48 | 2 | 46 | 0 | 159 / 0 | 0 |
| protected-use v0.1 | 30 | 5 | 23 | 4 (2 also FAIL) | 40 / 5 | 0 |
| hhn v0.1 (#92) | 18 | 18 | 0 | 0 | 0 / 0 | 0 |

Passing under the stub, and why:

| Test | Reason |
|---|---|
| hhn `S01` | Differential: compares aliased and unaliased results; equal under any constant stub (§6) |
| hhn `U04`, use-time `U04` | Keyword-only signature rejects extra keywords |
| use-time O01, O05, visit figures, reference rejections | Fixture-only (`ReferenceSourceModel`) |

The four ERROR methods (P02, P03, Z01, U01) raise `KeyError` inside the test
because the pre-commit hook never ran: the stub never reaches
`commit_if_epoch`. They are genuine semantic RED reported as errors, not
fixture defects. The tests are not edited in this PR.

No failure is `SURFACE_RED`; both modules import.

## 3. GREEN (commit 2)

Identical on CPython 3.13.16 and 3.12.3:

| Suite | Tests | Result |
|---|---|---|
| hhn v0.2 | 48 | OK |
| protected-use v0.1 | 30 | OK (no skips) |
| hhn v0.1 (#92) | 18 | OK |

## 4. Test strength check (mutation)

Because GREEN came on the first implementation run, each mutant below
breaks one rule in a scratch copy. Each mutant runs in an isolated directory
with copies of the tests and fixture (`PYTHONPATH` cannot be used: with
`-m unittest` the working directory precedes it). An unmutated control copy
passes all tests. Nothing here is committed.

| Mutant | Killed by |
|---|---|
| D2 "greater" branch removed | A03, C01, C02, O04 |
| No-op request check removed | V01, V03 (both entries) |
| Visit cap off by one (`>` for `>=`) | B04, B05, S04 |
| Int bit-length cap removed | A04, B05 |
| `record.get('id')` before the whole-dict key gate | T01, T04, T05 |
| `valid_until` from the last (root) record instead of the chain minimum | P03, Z03 reachable |
| Seam exception not contained | X01, X02 |
| `expected_epoch` re-read from `current_epoch()` before the seam | C04 only (call sequence) |
| `committed_epoch == expected_epoch` accepted | X03 |
| Request: malformed checked before oversize | T05 |
| Descending into a key-gate-failed snapshot dict | B09 |

11 of 11 killed.

## 5. Implementation choices within the frozen interface

Reported for review. None adds a reason code or changes an expectation.

1. **Scalar size checks apply to every exact `str` / `int` at a reachable
   position**, including values under extra or unknown keys and scalars of a
   key-gate-failed dict (S-4 step 5). An oversize extra-field value yields
   SNAPSHOT_LIMIT_EXCEEDED, not INVALID_AUTHORITY_INPUT. This follows
   §7.1 ("every int field"; strings "keys and values") and §7.4
   (LIMIT > malformed over reachable positions).
2. **Visit charging order** follows §7.3 structurally (container, then pairs,
   then children). Because any exceedance stops the scan and yields LIMIT,
   the order does not affect results.
3. **Second preflight over the private copy** is kept (stage 5). It adds no
   seam call and, under O1a, cannot change the result.
4. **Root identifiers** must be nonempty strings (#93 rule). An empty root key
   is INVALID_AUTHORITY_INPUT.
5. **Constants** are defined in the resolver module and imported by
   protected-use; the use-time entry calls the resolver's internal stages
   directly. It does not call `resolve_policy_change` and cannot accept its
   result.
6. **Pre-seam guard** (`snapshot_at < valid_until`) is present and returns
   COMMIT_ERROR. It is unreachable under the resolver and has no test, as
   §5.2 specifies.

## 6. Coverage observations (no test change proposed here)

- **S01** passes under any constant stub. S02 covers the positive aliasing
  path, so no gap results; noted for future strengthening.
- **TOCTOU by re-read.** A consumer that reads `current_epoch()` immediately
  before the seam is caught only by C04's call-sequence assertion. P§8's
  pre-commit hook runs inside the seam, after any such re-read. A hook point
  between resolution and the seam call would give a behavioral test.
  Candidate for a future test revision, not required by the frozen
  allocation.
- **Leaf vs chain minimum.** Indistinguishable under attenuation (errata E3);
  Z03 reachable and P03 still kill a root-based `valid_until`.

## 7. CI

`.github/workflows/authority-lineage-hhn-v0_2.yml`: Python 3.12, `contents:
read`, push and pull-request path filters on both modules, the fixture, the
three test files, the v0.1 module and the workflow. Runs the three suites as
separate steps. Expected on this PR head: green. Expected on commit 1 alone:
red (semantic RED), as recorded in §2.

## 8. Non-claims

- Fixture-level only. The state source is the in-memory reference model; no
  production backend, CAS, concurrency, replication, epoch persistence or
  trusted-time acquisition is exercised.
- Source obligations E1, O1, O1a, O2, O3 remain unverifiable by the resolver;
  O02/O03 continue to show undetectable O1 violations committing.
- No replay protection (#96 §4).
- Not Gateway integration, tool-effect binding, or runtime enforcement
  closure.
- No CLAIMS_STATUS change and no maturity promotion in this PR. Any
  FIXTURE_SUPPORTED entry is a separate, reviewed change.
- Principle 0 non-`str` / subclass gap is untouched (separate fix line).
  Pilot remains gated on external Problem Adoption.
