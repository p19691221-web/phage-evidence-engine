# DF-011 expectation provenance support rules

Status: PROPOSED — docs only.
Freeze these rules through review and merge before writing RED tests.
No implementation or CLAIMS_STATUS promotion is established here.

## Boundary

This gate determines whether supplied provenance supports using an
expectation set in the specified assessment.
It does not determine whether the expectations are substantively correct,
sufficient, lawful, safe, or legitimate in the real world.
Passing this gate does not authorize execution.

## Support requirements

All requirements below must hold:

1. Actor identifiers must resolve unambiguously under an explicitly
   declared identity model. Display names alone do not establish identity.
2. Approval must bind the approver to the exact expectation set and its
   content/version, governed actor, assessment action, and object.
3. The approver must be distinct from the governed actor.
4. Authority references must resolve to inspectable source records
   supporting that approver's permission to approve this expectation set
   for this assessment scope.
5. Approval and authority records must agree on their bindings and scope.
   Missing, ambiguous, conflicting, or unsupported bindings remain unresolved.

The source records and identity model used by the synthetic control must
be specified before RED. Their trust anchors are explicit fixture
assumptions, not proof of institutional authority.

Nonempty approved_by or authority_source_refs fields are insufficient.
Third-party proposal does not establish authority.
Self-proposal alone does not establish invalidity or malicious capture.
Declared authority_status, scope_status, and proposal_relationship are
not substitutes for checking the supporting records and actor identities.
Approval must not be inferred from observations satisfying E.

## Required differential cases

Keep expectations, observations, action, object, and governed actor fixed.
Change only provenance-related inputs and supporting records.

- Self-proposed without supported approval: UNRESOLVED.
- Third-party proposed without authority support: UNRESOLVED.
- Self-proposed and self-approved: UNRESOLVED.
- Control satisfying every support requirement: pass this provenance gate.

For each unresolved case:
- Include EXPECTATION_AUTHORITY_UNRESOLVED and expectation_set_id.
- Skip delta computation.
- Assert evaluator call count equals zero.

For the control:
- With all other gate prerequisites satisfied, assert evaluator call count
  equals one and the computed delta equals the independently fixed value.
- Do not assume the existing gate result carries evaluator output.

Use a counting spy through the evaluator injection boundary.
A called boolean or a SKIPPED output label alone is insufficient evidence.

## Delivery and claims

Sequence: merged rules -> four-case RED record -> minimal implementation
-> GREEN -> validation record -> separate CLAIMS_STATUS PR.

RED must record actual baseline behavior and reproducible commands.
GREEN must cite the frozen rules revision and executed code revision.
Any rule change requires explicit review and renewed affected RED evidence.

Claim support is limited to the executed cases, declared support rules,
and tested execution model. No production or pilot maturity follows.
