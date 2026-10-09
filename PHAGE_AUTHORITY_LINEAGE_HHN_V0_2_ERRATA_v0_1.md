# H/H′/N v0.2 — errata record v0.1

Date: 2026-10-09 (Asia/Taipei). Baseline: main
`a853f35d7603ebf9b7f79c4ea2fab62c941d0a12` (E1–E3);
`95b397d0c08f8cfcb7c90a43cf6c102db2916569` (E4).
Scope: docs-only. No code, test, CLAIMS_STATUS or maturity change.

## Freeze provenance

PHAGE_AUTHORITY_LINEAGE_HHN_EXECUTABLE_INTERFACE_v0_2.md was frozen at rev 2
by approval and merge of #97:

| Item | Value |
|---|---|
| Pull request | https://github.com/p19691221-web/phage-evidence-engine/pull/97 |
| Approval | Owner comment, not a formal GitHub review: "Freeze approved for head c229819e51ec5850df462c6f360b5976aabc047c, effective on merge." — https://github.com/p19691221-web/phage-evidence-engine/pull/97#issuecomment-6072123761 |
| Approved head | `c229819e51ec5850df462c6f360b5976aabc047c` |
| Merge commit | `a853f35d7603ebf9b7f79c4ea2fab62c941d0a12` (2026-10-09) — https://github.com/p19691221-web/phage-evidence-engine/pull/97#event-32837388330 |

The interface's own rule ("Becomes frozen only on explicit review approval and
merge") is met by these two events.

## Errata

| ID | Location | Defect | Correction | Normative effect |
|---|---|---|---|---|
| E1 | Interface title and status line | Merged text still read "freeze candidate" / `FREEZE CANDIDATE rev 2, NOT FROZEN` | Title suffix removed; status line states frozen at rev 2 by #97 with merge commit and a pointer to this record | None |
| E2 | Interface header | No blank line between the revision-log table and the next line, so Markdown rendered "Becomes frozen only…" as a table row | Blank line inserted | None |
| E3 | #96 §8 (P§8) Z03, as allocated by interface §9 | Case required an intermediate grant expiring before leaf and root. #92 attenuation (`child.expires_at <= parent.expires_at`), unchanged in v0.2, makes it unreachable: on any chain that resolves, the leaf expires first | Z03 is superseded by two reachable cases, below. #96 text is not edited; this record governs Z03 | None. `valid_until = min(chain expires_at)` and attenuation are unchanged |
| E4 | Interface §7.1, §7.2 S-4 step 5, §7.4 | Scope of scalar size checks was not stated in one place; #100 had to derive it (implementation record §5 item 1) | Explicit statement added, below. Interface text is not edited; this record governs | None. States an existing rule; implementation and tests already conform |

### E3 — Z03 as corrected

| Case | Chain expiry (leaf / middle / root) | Expected |
|---|---|---|
| Z03a reachable chain minimum | 50 / 75 / 100; snapshot `at = 10`; pre-commit sets `now = 60` | Resolution succeeds; commit seam receives `snapshot_at = 10`, `valid_until = 50`; NOT_COMMITTED / AUTHORITY_NOT_CURRENT; zero writes; epoch unchanged |
| Z03b intermediate earlier than leaf | 100 / 50 / 100 | NOT_COMMITTED / AUTHORITY_SCOPE_VIOLATION from resolution; `commit_if_epoch` calls 0; zero writes |

Z03b records why the original case cannot be reached, as an executable
check rather than prose.

Origin: raised in PHAGE_AUTHORITY_LINEAGE_HHN_V0_2_RED_RECORD_2026-10-09.md
revision 1 §5; correction decided in review on 2026-10-09; implemented in the
RED PR as `test_P8_Z03_chain_minimum_reachable` and
`test_P8_Z03_intermediate_earlier_than_leaf_is_scope_violation`.

### E4 — scalar size checks in snapshot preflight

Normative statement (added; restates existing rules):

> Snapshot preflight applies the §7.1 size checks to every exact `str` and
> exact `int` scalar value at a position reachable by safe traversal,
> including values under extra or unknown fields and the scalar values of a
> dict whose key gate failed. An exceedance returns SNAPSHOT_LIMIT_EXCEEDED
> under §7.4 and takes precedence over INVALID_AUTHORITY_INPUT. Positions not
> reachable by safe traversal are still not checked.

Basis in the frozen interface:

| Source | Content relied on |
|---|---|
| §7.1 | `SNAPSHOT_MAX_STRING_CHARS` applies to "keys and values"; `SNAPSHOT_MAX_INT_BITS` applies to "every int field" |
| §7.2 S-4 step 5 | On key-gate failure, the dict is "accessed only by `dict.items(d)`; scalar values still size-checked; container values not entered" |
| §7.4 | Phase 1 walks reachable positions and stops at the first size exceedance; LIMIT > malformed > missing over reachable positions; exceedance at an unreachable position is not observed |

Implementation evidence: #100, merged as
`95b397d0c08f8cfcb7c90a43cf6c102db2916569`
(https://github.com/p19691221-web/phage-evidence-engine/pull/100#event-32845740149).
PHAGE_AUTHORITY_LINEAGE_HHN_V0_2_IMPLEMENTATION_RECORD_2026-10-09.md §5 item 1
reports this interpretation for review. Acceptance was given in review on
2026-10-09; the #100 page itself records no comment or review on this point.

Consequences, unchanged by E4:

| Case | Result |
|---|---|
| Extra field in a grant with a 257-char `str` value | SNAPSHOT_LIMIT_EXCEEDED |
| Extra field with an int of 65 bits | SNAPSHOT_LIMIT_EXCEEDED |
| Dict with a non-`str` key and a 257-char scalar value | SNAPSHOT_LIMIT_EXCEEDED (T05 covers the over-long key variant only) |
| Dict with a non-`str` key and an oversized container value | INVALID_AUTHORITY_INPUT (container unreachable; B09, B10) |
| Non-exact object of any size | INVALID_AUTHORITY_INPUT (not measured; T02) |

Not covered by an existing acceptance case: rows 1–3 (oversize scalar value
under an extra field, and oversize scalar value in a key-gate-failed dict).
All five rows were checked against the merged implementation at `95b397d`
before this record was written. E4 does not add a test; a future test
revision may.

## Non-claims

E1–E4 change no signature, schema, budget, reason code, precedence rule or
acceptance expectation other than replacing the unreachable Z03 case. E4
changes no implementation, test, or frozen version. #96
remains NOT FROZEN as the rationale record.
