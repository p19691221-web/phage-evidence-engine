# H/H′/N v0.2 — test revision record (TOCTOU after D2, S01, E4)

Date: 2026-10-09 (Asia/Taipei). Baseline: main `e58a2ce` (merge of #101).
Interface: PHAGE_AUTHORITY_LINEAGE_HHN_EXECUTABLE_INTERFACE_v0_2.md (frozen,
#97), errata E1–E4 (#98, #101). Implementation: #100, unchanged.

Scope: test and fixture only. No product module, frozen document, errata,
CLAIMS_STATUS, maturity or workflow change. The existing CI workflow already
covers every touched file through its path filters.

## 1. Changes

| File | Change |
|---|---|
| `fixture_phage_authority_reference_source_v0_1.py` | Adds `ReferenceSource.epoch_read_then(hook)`, a test-only `current_epoch` seam (§2). Inactive unless a test uses it. |
| `test_phage_authority_lineage_hhn_v0_2.py` | S01 strengthened; adds `SupplementaryE4ScalarScope` (inspection) |
| `test_phage_authority_protected_use_v0_1.py` | Adds `SupplementaryTOCTOU` and `SupplementaryE4ScalarScope` (use-time) |
| this record | Design, mutant RED, GREEN |

Supplementary IDs (`SUPP_*`) are outside #96 §8 (P§8) and outside interface
§9's allocation. They add coverage and change no P§8 expectation. The only
edit to an existing test is the added S01 assertion.

## 2. TOCTOU hook: where it runs

`epoch_read_then(hook)` returns a callable passed as the `current_epoch` seam.
On each call it reads the source epoch; on the first call only, it then runs
`hook(source)` and returns the value it read.

On the authorized path, the resolver's single `current_epoch` call is D2, its
last seam call (frozen interface §6 stage 7, §6.1). The hook therefore runs
**after D2 has read the bound epoch E and before that value is returned to the
resolver**. It does not run after resolution has returned, and this record
does not claim the two points are identical. What the point does establish is
sufficient for the race under test: the resolver receives E while the source
is already at E+1, and a correct consumer must still pass E to
`commit_if_epoch`.

Why not inside `commit_if_epoch`: a consumer that re-reads the epoch reads it
before calling the seam. A hook inside the seam runs after that read, so the
re-read still returns E and the defect is invisible.

Rejected alternatives:

| Option | Reason |
|---|---|
| Patch `phage_authority_protected_use_v0_1._resolver._resolve` | Hook point is exact, but binds tests to private names; a refactor could bypass it silently |
| Fire from `verify_grant` | Runs before D2; that race is already C01/C02 |

Self-checks in each TR01 case: the hook fired exactly once, and D2 observed
E = 0. A failure of these is reported as a fixture defect, so an
implementation that reorders its seam calls cannot pass silently.

## 3. Cases

| ID | Entry | Setup | Expected |
|---|---|---|---|
| SUPP_TR01a | use-time | Hook revokes leaf after D2 read (E 0 → 1) | NOT_COMMITTED / AUTHORITY_STATE_CHANGED (asserted first); seam `expected_epoch = 0`; writes 0; source epoch 1; policy unchanged; leaf revoked; `current_epoch` called once |
| SUPP_TR01b | use-time | Hook changes unrelated grant after D2 read | Same as TR01a |
| SUPP_TR01c | use-time | Hook makes no change (control) | COMMITTED, `committed_epoch` 1; hook fired once; D2 observed `[0]` |
| S01 (strengthened) | inspection | Shared vs unshared `targets` | Results equal, **and both** equal the AUTHORIZED positive control |
| SUPP_E4_1 | both | Grant extra field, `str` 256 / 257 chars | 256: INVALID_AUTHORITY_INPUT; 257: SNAPSHOT_LIMIT_EXCEEDED |
| SUPP_E4_2 | both | Grant extra field, int `2**64 - 1` / `2**64` | 64 bits: INVALID_AUTHORITY_INPUT; 65 bits: SNAPSHOT_LIMIT_EXCEEDED |
| SUPP_E4_3 | both | Grant with `OpaqueKey` key, scalar 256 / 257 chars | 256: INVALID_AUTHORITY_INPUT; 257: SNAPSHOT_LIMIT_EXCEEDED; `OpaqueKey` hooks 0 |

The at-limit controls are INVALID, not AUTHORIZED, because the extra field or
non-`str` key is itself malformed (errata E4).

E4 at both entries: zero `verify_grant` calls. Use-time additionally: zero
`commit_if_epoch` calls, writes 0, epoch unchanged, result
NOT_COMMITTED with the same reason. In the `OpaqueKey` case the snapshot is
built first, the recorder is cleared, then the entry is called; the use-time
provider returns that snapshot directly, so no deepcopy touches the key during
the call.

## 4. Mutant RED

Each mutant ran in an isolated directory with copies of the revised tests,
fixture and v0.1 module (CPython 3.12.3). None is committed.

| Mutant | Change | Target case | First failing assertion |
|---|---|---|---|
| M1 | `expected_epoch = current_epoch()` before the seam (re-read) | TR01a, TR01b | Result: COMMITTED (epoch 2; in TR01a with the leaf already revoked) instead of NOT_COMMITTED / AUTHORITY_STATE_CHANGED |
| M2 | Fail-closed stub (#100 commit 1) as resolver | S01 | Result: VERIFICATION_ERROR instead of AUTHORIZED (before: S01 passed under this stub) |
| M3 | Scalar size check only under known field names | E4_1 (and E4_2) | Over-limit row: INVALID_AUTHORITY_INPUT instead of SNAPSHOT_LIMIT_EXCEEDED, both entries |
| M4 | Int bit cap only for named int fields | E4_2 | Same, both entries |
| M5 | No scalar check in a key-gate-failed dict | E4_3 | Same, both entries |

In every row, the at-limit subtest still passed; only the over-limit subtest
failed.

Further kills, recorded for completeness:

- M1 also fails TR01c, through its D2 read check (observed `[0, 0]` instead of
  `[0]`); the result there is correctly COMMITTED. M1 also still fails P§8
  C04 on call sequence. TR01a/b are now the result-based catch;
  #100 record §6 noted that previously only C04 caught this.
- M2 fails most other tests and the E4/TR01 cases as well (expected for a
  stub; use-time errors because the stub lacks the resolver internals).
- M3–M5 fail no test outside their target cases.

## 5. GREEN (unmodified implementation)

| Suite | Tests | CPython 3.12.3 | CPython 3.13.16 |
|---|---|---|---|
| hhn v0.2 | 51 (48 + 3) | OK | OK |
| protected-use v0.1 | 36 (30 + 6) | OK | OK |
| hhn v0.1 (#92) | 18 | OK | OK |

## 6. Non-claims

Fixture level only. The hook models a source change between D2 and the
consumer's seam call in a single-threaded reference source; it does not
exercise real concurrency. No implementation change was needed and none was
made. Interface §9's allocation is unchanged. No CLAIMS_STATUS or maturity
change.
