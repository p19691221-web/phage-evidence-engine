# DF-016 Authority-Lineage Compatibility Gate — Record v0.1

Status: RETROACTIVE RECORD, PROPOSED FOR REVIEW. NOT FROZEN.
Prepared: 2026-10-07 (Asia/Taipei).
Assessed at: main `f92cc736aa1a0fcea49298b774f0b132511f5f3c`.

## 1. Provenance and timing (read first)

This gate was defined before H/H′/N work began: any criterion A/B/C that is
FAIL or UNKNOWN selects a dedicated authority-lineage resolver instead of
reusing DF-016 lineage machinery.

**The gate was not executed or recorded before H/H′/N development.** PRs #91
(proposal), #92 (interface/RED) and #93 (fixture resolver) contain no DF-016
assessment. This document is an after-the-fact record. It must not be cited as
a gate that ran before #93, and it does not retroactively approve #93's design
choices beyond what is stated in §4.

Validity of retroactive assessment: the assessed DF-016 artifacts are
byte-identical between the H/H′/N proposal baseline (`6882afe`) and the
assessment commit (`f92cc73`):

    git diff --stat 6882afe f92cc73 -- \
      phage_lineage_contract_v0_1.py lineage.py \
      phage_digital_custody_v0_1.py DF016_DIGITAL_CUSTODY_DESIGN_v0_1.md \
      test_phage_lineage_contract_v0_1.py
    # (empty)

So the findings below describe the DF-016 state that was available when the
H/H′/N route was chosen.

## 2. Assessed artifacts

- `phage_lineage_contract_v0_1.py` — DF-016 lineage integrity contract
  (`Evidence`, `LineageChecker`, `LineageStatus`, `LineagePolicy`).
- `lineage.py` — Epistemic Constitution checker (`LineageCycleDetected`,
  `LineageMaxDepthExceeded` as `GovernanceViolation`).
- `phage_digital_custody_v0_1.py` — custody event validator.
- `DF016_DIGITAL_CUSTODY_DESIGN_v0_1.md` — status DESIGN DRAFT, no
  implementation claim.
- Comparison target: `phage_authority_lineage_hhn_v0_1.py` (#93).

## 3. Criteria

### A — Versioning

Requirement: query derivation state at a specific policy/grant version, not
only the currently supplied state.

Evidence:
- `Evidence` fields are `evidence_id`, `observed_at`, `available_at`,
  `derived_from` (`phage_lineage_contract_v0_1.py:19-23`). No revision,
  digest, or version field.
- `LineageChecker` evaluates the supplied store as given; there is no as-of /
  at-version query.
- `phage_digital_custody_v0_1.py` has no version dimension.

A caller could pre-select a version-specific store, but versioning would then
live entirely outside DF-016. H/H′ needs version binding inside the decision
(#93 binds `policy_id`, `expected_revision`, `expected_digest` and root anchor
`revision`/`digest`).

Determination: **FAIL** (no native version semantics).

### B — Graph semantics

Requirement: real parent/ancestor/dependency relations with traversal, not
flat metadata.

Evidence:
- `derived_from: tuple[str, ...]` gives real multi-parent edges; DFS traverses
  all ancestors and reports missing ancestors
  (`phage_lineage_contract_v0_1.py:84-136`).
- Edge semantics are evidential derivation only. There is no issuer/subject,
  delegation permission, operation/target scope, scope attenuation
  (child ⊆ parent), or time-window containment — all of which H/H′ evaluates
  per edge (`phage_authority_lineage_hhn_v0_1.py:_resolve`).

Determination: **PASS** (graph structure and traversal, as the criterion
states). The missing authority edge semantics are a separate integration gap,
recorded in §5. They are not part of criterion B as originally defined and are
not added to it retroactively.

### C — Cycle semantics

Requirement: represent cycles and reject them fail-closed (no loop,
truncation, or undefined behaviour), as N requires.

Evidence:
- `LineageChecker` tracks `active_path` and returns
  `LINEAGE_CYCLE_DETECTED`; depth bound `max_depth=64` returns
  `LINEAGE_MAX_DEPTH_EXCEEDED` (`phage_lineage_contract_v0_1.py:84-100`).
- Regression coverage: `test_phage_lineage_contract_v0_1.py:65`.
- `lineage.py` raises `LineageCycleDetected` / `LineageMaxDepthExceeded`.
- Codes belong to the evidence taxonomy (`LINEAGE_*`); DF-016 design §taxonomy
  requires the taxonomies remain distinguishable until an integration design
  is validated. N's result code is `AUTHORITY_CYCLE_DETECTED`.

Determination: **PASS for mechanism**; taxonomy is not directly reusable
without an explicit mapping.

## 4. Outcome

| Criterion | Determination |
|---|---|
| A Versioning | FAIL |
| B Graph structure and traversal | PASS; authority edge semantics pending integration |
| C Cycle rejection mechanism | PASS; taxonomy mapping pending integration |

Under the gate rule, A alone selects a dedicated resolver. The route taken in
#93 is consistent with the rule. That consistency is an outcome observed after
the fact, not evidence that the gate governed the decision.

## 5. Observations for later integration (not decisions)

- Authority edge semantics (issuer/subject, delegation permission,
  operation/target scope attenuation, time-window containment) are absent from
  DF-016 edges; #93 evaluates them per edge. Required for any reuse.
- #93 traverses a single-parent chain (`parent_id`); DF-016 supports
  multi-parent DAGs. Any future integration must decide whether authority
  lineage may have multiple parents.
- C's mechanism (active-path detection plus depth bound) matches N's
  requirement; reuse at mechanism level, with a separate authority taxonomy, is
  a candidate for the integration review, not adopted here.
- Integration with formal state sources and the protected-use boundary remains
  open; nothing here bears on it.

## 6. Non-claims

This record changes no code, contract, or CLAIMS_STATUS entry. It establishes
no runtime/enforcement closure, no DF-016 C compatibility claim, and no reuse
of DF-016 or G6H3 machinery by authority-lineage resolution.
