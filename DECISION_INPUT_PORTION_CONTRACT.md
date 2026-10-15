# Decision input portion support: contract amendment

Status: PROPOSED — docs only; review and merge before RED.
Baseline: b69a466.

## Supersession

For the next checker revision, this document supersedes the top-level
P1-specific S/V findings in DECISION_INPUT_TEST_CONTRACT.md.
Historical fixtures, logs and validation records retain their original
meaning and are not evidence for the amended contract.

Keep relationships A, P, L and C unchanged.
Remove top-level relationships S and V.
Add output_support, mapping every registered output portion ID to:
{citation: finding, verification: finding}.

Compute each portion's support from its own citation and verification
bindings. No literal portion ID selects a privileged support path.
An uncited portion has both findings not_asserted.

Keep adopted_support and its existing prerequisite:
if A is not matched, adopted support is not_assessable.
Otherwise it reports support for each exact adopted portion.
output_support remains independently inspectable when A fails.

No aggregate support flag is introduced.
Existing finding meanings and evidence limitations remain unchanged.

## Revised expectations for the seven existing cases

Retain A/P/L/C and adopted_support expectations unchanged.
For output_support:
- P1 citation takes the former S finding.
- P1 verification takes the former V finding.
- P2 citation and verification are both not_asserted.

This migration applies only to new expected-result revisions.
Preserve the historical result schema in existing execution records.

## Portion-renaming differential

Create a renamed control using the bijection P1 -> Q7, P2 -> R9.
Apply it only to semantic portion identifiers:
- portion IDs in output and all binding content snapshots;
- citation and verification portion_id;
- adopted_portions and presented_portions;
- expected output_support and adopted_support keys.

Do not change text, record IDs, versions, identities, references or scope.
Do not globally replace arbitrary text containing P1/P2.

The renamed result must equal the control result after applying the
same key renaming to output_support and adopted_support.
A/P/L/C and all finding values remain unchanged.
Expected output_support: Q7 matched/matched; R9 not_asserted/not_asserted.
Expected adopted_support: Q7 matched/matched.

The test must independently assert these concrete expected findings;
equivariance alone is insufficient because two wrong results can agree.

## RED interpretation and delivery

Record two distinct failures if observed:
1. Old production S/V lose P1 support after consistent renaming.
2. Old production output lacks the amended output_support schema.

Schema mismatch alone does not prove the hardcoded-ID defect.
Demonstrate the old control/renamed behavior before changing production.
Do not add test-local support computation to manufacture findings.

Sequence: reviewed contract -> fixtures/tests and observed RED record
-> implementation -> GREEN and regression -> validation record
-> separate claim review.

No claim expansion occurs here. A successful renamed control supports
only the tested renaming, not arbitrary identities or external workflows.
