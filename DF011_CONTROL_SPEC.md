# DF-011 control and execution-boundary specification

Status: PROPOSED — docs only; review and merge before RED.

Code inspection baseline: 7f3b92f.
Support rules baseline: 471f791 (PR #108).
The changes between these baselines are documentation only.

## Supersession of #108 terminology

For DF-011, this specification supersedes the following wording in
DF011_PROVENANCE_SUPPORT_RULES.md at 471f791:

- "Skip delta computation" means: invoke neither run_gate nor the
  downstream evaluator when expectation provenance is unresolved.
- "the computed delta equals the independently fixed value" means:
  inspect the test evaluator's recorded output for the fixed sentinel.
- "The fixed control delta and its derivation" means:
  the fixed test evaluator sentinel defined below; no delta derivation.

No E/O delta computation is specified or established.
Support requirements and the four differential cases remain unchanged.
The candidate fixture's delta_computation: SKIPPED is a legacy expected
label, not evidence that an E/O delta engine exists.

## Architecture

Add an expectation provenance gate before the existing run_gate.
Only supported provenance may proceed to run_gate and lineage checking.
Supported provenance does not itself imply CLEAN or authorize execution.

Preserve existing run_gate and DownstreamEvaluator.evaluate signatures
and result structures. Do not insert evaluator output into gate results.

## Fixed assessment inputs

All four fixtures retain:
- governed actor: AGENT-ENG-01
- action: CONSTRUCTION_ACCEPTANCE
- object: PIPELINE_CULVERT_INTERSECTION
- expectation set: ES-PUBLIC-001
- expectation: E1 / ACCEPTANCE_FORM_EXISTS / REVIEW_RECORD
- observation: O1 satisfies E1, source INTERNAL_EXECUTION_LOG

Each fixture must also declare the same complete lineage input bundle,
including evidence_id, epistemic_cutoff, evidence_store and
availability_view. That bundle must independently produce CLEAN under
the existing run_gate. A CLEAN label alone is not sufficient.

The concrete bundle must be specified in a reviewed docs-only change
before RED; it must not be selected by observing DF-011 test success.

## Required boundary assertions

Use two counting spies:
1. A delegating spy at the actual run_gate call boundary.
2. A test evaluator recording calls, received inputs and output.

For each of the three unresolved provenance cases:
- provenance outcome is UNRESOLVED;
- dependency includes EXPECTATION_AUTHORITY_UNRESOLVED and set ID;
- run_gate call count equals zero;
- evaluator call count equals zero.

For the supported control, with the fixed CLEAN lineage bundle:
- run_gate call count equals one, with the specified inputs;
- existing gate outcome is CLEAN and evaluation_started is true;
- evaluator call count equals one;
- evaluator receives the specified evidence_id and CLEAN lineage result;
- evaluator records and returns "DF011_EVALUATOR_REACHED_V1".

The sentinel is an arbitrary fixed execution marker, not an assessment
result or computed E/O delta. Assertions inspect spy records rather
than adding output fields to the existing gate result.

## Remaining pre-RED prerequisites

Before executable RED cases, reviewed and merged documentation must fix:
- canonical actor identities and alias handling;
- synthetic authority records and explicit trust assumptions;
- approval binding to expectation content/version and assessment scope;
- the concrete CLEAN lineage input bundle described above.

## Evidence and claims

Validation records must distinguish the provenance boundary, existing
lineage behavior and test evaluator behavior.

Downstream execution uses a test evaluator. This validates provenance
routing and invocation control, not an E/O delta engine.
Evidence/Gap structural assessment remains a separate claim whose
scope is determined by its own evidence.

No CLAIMS_STATUS promotion is established by this document.

## Concrete synthetic identity and approval model

This section supplies the pre-RED specifications listed above.

Canonical identities are exact, case-sensitive ASCII strings:
- AGENT-ENG-01: governed execution actor and self-proposer.
- REVIEWER-01: independent synthetic approver.
- ADVISOR-01: third-party proposer.

No aliases, trimming, case folding or display-name substitution are
supported. Unknown or ambiguous identities remain UNRESOLVED.
Distinct IDs are assumed to represent distinct principals in this
synthetic model; this does not establish real-world independence.

The fixed expectation content is the ordered list containing:
(E1, ACCEPTANCE_FORM_EXISTS, REVIEW_RECORD).
Its set ID is ES-PUBLIC-001 and version is 1.
Approval requires exact equality of ID, version and content; an ID or
version label alone is insufficient.

All approval and authority bindings must exactly match:
- governed_actor: AGENT-ENG-01
- action: CONSTRUCTION_ACCEPTANCE
- object: PIPELINE_CULVERT_INTERSECTION
- expectation set ID, version and content specified above.

AUTH-DF011-001 is a synthetic authority record granting REVIEWER-01
permission APPROVE_EXPECTATION_SET for exactly those bindings.
It is supplied through an assessment-policy source registry, separately
from the actor's proposed provenance. Its trust is a fixture assumption.
A reference resolves only by exact ID to this record; nonempty,
unresolved or conflicting references provide no support.

APPROVAL-DF011-001 records REVIEWER-01 approving exactly those bindings,
citing AUTH-DF011-001. Both records must be inspected and agree.
The approval record and authority registry must be fixture-visible.

## Concrete four-case provenance matrix

Keep proposed_by=AGENT-ENG-01 for candidate, self-approved and control.
Only the third-party negative changes proposed_by to ADVISOR-01.

- Candidate: approved_by=null; authority_source_refs=[]; no approval.
- Third-party negative: approved_by=null; authority_source_refs=[];
  no approval. A distinct proposer supplies no authority.
- Self-approved negative: approved_by=AGENT-ENG-01; approval claims
  the fixed bindings and cites AUTH-DF011-001. That source grants only
  REVIEWER-01, so it does not support the claimed approval.
- Control: approved_by=REVIEWER-01; approval=APPROVAL-DF011-001;
  authority_source_refs=[AUTH-DF011-001].

The policy source registry is identical in all four cases.
Declared authority_status, scope_status and relationship labels are
not decision inputs. Derive support from identities and bound records.
Control remains self-proposed: independent supported approval, rather
than changing proposer identity, is the differentiating condition.

## Concrete CLEAN lineage bundle

All fixtures explicitly carry the following identical bundle:
- evidence_id: DF011-SYNTHETIC-ROOT
- epistemic_cutoff: 2026-08-18T12:00:00+00:00
- evidence_store: one Evidence keyed by that evidence_id, with
  observed_at=available_at=2026-08-18T11:00:00+00:00,
  derived_from=(), source_refs=("fixture:DF-011",).
- availability_view: one ResolvedAvailability keyed by that evidence_id,
  with matching evidence_id, status=AvailabilityStatus.RESOLVED,
  resolved_available_at=2026-08-18T11:00:00+00:00,
  supporting_claim_refs=("availability-DF011-SYNTHETIC-ROOT",).
- checker: existing run_gate default.

Represent timestamps as timezone-aware datetime values at the adapter.
This is a synthetic lineage input, separate from O1 and authority records.
Its CLEAN precondition must be independently checked against existing
run_gate, without the new provenance gate, before interpreting DF-011
results. If it fails, report the prerequisite failure; do not silently
change the bundle to obtain a pass.

## Limits of the synthetic model

No signatures, real identity verification, delegation, revocation,
concurrency or real-world authority legitimacy are established.
The fixed sentinel proves only that the test evaluator was reached.
Any incompatible constructor requirements or binding changes require
a reviewed specification amendment before RED.
