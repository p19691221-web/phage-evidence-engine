# H/H′/N v0.2 — errata record v0.1

Date: 2026-10-09 (Asia/Taipei). Baseline: main
`a853f35d7603ebf9b7f79c4ea2fab62c941d0a12`.
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

## Non-claims

E1–E3 change no signature, schema, budget, reason code, precedence rule or
acceptance expectation other than replacing the unreachable Z03 case. #96
remains NOT FROZEN as the rationale record.
