# Repo Governance

Status: working principles and proposed controls. The common pattern below is `HYPOTHESIZED`.

This document records repository dogfooding controls, not PHAGE product claims. It is separate from the frozen `PHAGE_TRUST_BOUNDARY_INVARIANTS v0.1`; it does not amend that document or promote any product claim. Repository implementation status described here comes from the discussion and has not been independently audited against a checkout.

| Claim subject | Evidence maturity | Enforcement authority |
|---|---|---|
| **Product claims** | `CLAIMS_STATUS` six-level scale; `FIXTURE_SUPPORTED ⇢ pilot` depends on external Problem Adoption and real institutional decision flows. | `gate.py` / verifier / L/M; runtime authority closure remains incomplete. |
| **Repo governance** | Three initial observations; the induced common pattern is `HYPOTHESIZED`. | Consumer mutation can be constrained by CI path checks plus CODEOWNERS; branch deletion has not yet been brought into a governed path. |

## Edge rules

- **Across rows, within one column:** comparison/analogy edges are permitted; evidence edges are prohibited. Repository governance progress cannot promote product claim maturity, and product evidence cannot establish that a repository control is enforced.
- **Across columns, within one row:** the two assessment axes do not imply each other. Evidence maturity is not enforcement status. For example, regression closure does not imply runtime enforcement closure.

The cleanup workflow may carry `analogous mechanism: POLICY_MUTATION authority containment`. This records a comparison edge and design analogy; it creates no evidence edge.

## Initial observations and proposed controls

These observations have different roles and have not established a common invariant through regression or counterexample testing.

| Observation | Nature | Proposed control | Enforcement status |
|---|---|---|---|
| Proxy must not replace target evidence. | Claim promotion / epistemic discipline. | Validate `CLAIMS_STATUS` against an evidence schema. Any claim at `PILOT_SUPPORTED` or above must reference an `evidence_type: external_decision_flow` record; fixture or integration paths alone are insufficient. | Proposed; schema, evidence validation, and CI enforcement require implementation and verification. |
| Consumers must not mutate the producer contract they consume. | Dependency authority / governance. | Block L/M PR diffs touching verifier modules or contract files with a CI path check. Use CODEOWNERS for review ownership. Contract changes require a separate contract/verifier PR, followed by consumer rebase. | Proposed; required CI enforcement and ownership controls require verification. CODEOWNERS alone is not a mutation gate. |
| Branch cleanup must preserve development lineage. | Provenance preservation. | Restrict branch deletion through repository rulesets and reserve the authorized deletion path for a cleanup workflow that archives and verifies the original tip before deletion. | Proposed; deletion authority remains outside the governed path until restrictions and workflow capabilities are configured and verified. |

### Observed enforcement gap — PR #84

On 2026-10-02, `repo-governance-pattern-anchor-v0_1` was deleted through GitHub UI before an archive tag was established, then restored. This demonstrates that branch deletion was not confined to an archive-before-delete path.

On 2026-10-03, the restored tip was verified as `9b69032bfc4d2127edf011f6f628b7898a4b13d1`. The tag `archive/repo-governance-pattern-anchor-v0_1` was created and verified to point to that commit before the branch was deleted again.

Evidence: [PR #84 timeline](https://github.com/p19691221-web/phage-evidence-engine/pull/84) and the archive tag.

The recovery preserved lineage for this branch; it does not establish that bypass deletion paths are prevented. Enforcement status remains: branch deletion is not confined to a governed path.

This event supports the existence of an enforcement gap. It is not a second independent observation of the pattern: it arose in the same repo-governance domain that generated the hypothesis and was recognized with knowledge of the pattern. The pattern remains `HYPOTHESIZED`; no product claim maturity is promoted.
### Controlled cleanup requirements

The cleanup workflow must capture the branch tip, inspect PR/merge history, assess semantic landing, create `archive/<branch>` at the original tip, verify the tag, and only then delete the branch. If the branch tip changes during the process, abort and reassess. An existing archive tag pointing elsewhere must not be overwritten silently.

Ancestry reachability alone is insufficient after squash merge. `git cherry main <branch>` and content comparisons are diagnostic inputs, not automatic proof of semantic landing: squash commits may not be patch-equivalent to individual commits, and `git diff main...<branch>` compares from the merge base rather than directly proving that the branch's content is present in current main. Ambiguous results require review before deletion.

The archive tag must retain the pre-deletion development tip, not the squash commit on main. Protect archive refs from unintended mutation or deletion. A post-deletion event cannot substitute for archive-before-delete: the GitHub `delete` payload does not preserve the deleted tip SHA. Actual enforcement depends on preventing bypass deletion paths and verifying ruleset/bypass permissions.

## HYPOTHESIZED — constraint non-substitution pattern

> An operation should not be permitted to rewrite, substitute for, or destroy the constraint or evidence on which its own validity depends.

This wording was induced from the three initial repository observations: substitute corresponds to proxy/target, rewrite to consumer mutation, and destroy to cleanup lineage. Those observations are the hypothesis's source, not independent validation. The shared structure is currently a working hypothesis, not a PHAGE product invariant or established methodology.

### Independent observation and promotion condition

The first repository commit recording this pattern is the pattern anchor. Preserve its exact SHA in a durable record associated with the documentation-only PR; do not substitute the conversation date, file modification time, or an uncommitted draft. If the PR is squash-merged, retain both the original anchor commit and the resulting main commit so the original record remains resolvable.

An eligible fixture's creation commit must be strictly subsequent to the pattern anchor. Establish this ordering through repository ancestry (the pattern anchor is an ancestor of the fixture creation commit), rather than commit timestamps alone. If squash or another history transformation changes the anchor used for ancestry checks, record the mapping to the main commit explicitly. A fixture created before the anchor, or during the uncommitted interval, cannot satisfy this subsequent-observation condition through a retrospective declaration.

Promotion requires a subsequent product-level fixture designed without reference to this pattern, with the structural match identified only afterward. Cases sought or constructed using the pattern count as confirmation, not independent observation. An eligible independent observation supports a promotion review; it does not automatically establish an invariant.

Independence provenance must be recorded when the fixture is created, before a structural match is observed. Record `pattern_reference_at_design: false` in the fixture's creation metadata and retain the creation commit alongside it. The boolean is a contemporaneous declaration with provenance, not proof of independence by itself.

Required record elements:

- Fixture identifier and creation metadata containing `pattern_reference_at_design`.
- The retained pattern anchor commit and verified ancestry/order relation to the fixture creation commit.
- The exact creation commit that first contains that metadata and the fixture design. Retain this commit reference in an append-only registry or equivalent durable record; do not invent a self-referential SHA inside that commit.
- Design provenance identifying the inputs used at creation, so the declaration can be assessed.
- A separate later observation record with its own commit, structural-match rationale, and reference to the retained creation commit.

Missing creation-time metadata, a field added only after the match, or an unresolvable creation commit makes independence unestablished. A retrospective annotation may record that limitation, but cannot make the fixture eligible as an independent observation. Neither the independence record nor any repository control progress creates a cross-row evidence edge into product claim maturity.

## Producer-to-consumer convergence boundary

The agreed sequence is:

`caller identity → authority binding → producer-verifier contract freeze → main → L/M rebase → L/M integration → FIXTURE_SUPPORTED (cross-boundary) ⇢ pilot`

The final dashed transition depends on external Problem Adoption, not CI. Green integration supplies fixture evidence and cannot establish `PILOT_SUPPORTED`.

The producer contract must specify hard-stop composition: if identity verification returns `UNVERIFIED` or `VERIFICATION_ERROR`, do not execute authority verification. Record authority as explicit `not_evaluated` with the failed prerequisite. Each verifier must separately distinguish unverifiable subject/evidence from verifier failure (the G1/G2 distinction). Freeze these semantics through the contract change process before extending consumer behavior.
