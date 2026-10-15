# Decision input reuse: pre-RED test contract

Status: PROPOSED — docs only.
Inspection and semantic specification baseline: 081a09e.
Decision input traceability remains OPEN.

## Component inspection

expectation_provenance_gate.py:
- _supported requires an approver distinct from the governed actor.
- Authority records must grant APPROVE_EXPECTATION_SET.
- run_expectation_gate delegates to assessment run_gate.

These operations enforce expectation approval semantics, not adoption
traceability. This experiment will not invoke them as an adoption checker
or fabricate approval records to satisfy their requirements.

The inspected module exposes no semantics-neutral binding/resolution
component for direct reuse. This is a module-scoped finding, not a
repository-wide claim that no reusable component exists.

Pattern-level reuse remains a hypothesis. Executable component reuse
is not established. Python equality and dictionary lookup alone do not
constitute reuse of a PHAGE component.

## Proposed execution boundary

Proposed module: decision_input_traceability.py.
Proposed entry point:
inspect_adoption(*, adoption_id, registry, canonical_identities).

The checker inspects records without authorizing execution or invoking
run_gate, an evaluator, or external tools. It must not mutate its inputs.
Registry trust and canonical identities are supplied policy assumptions.

The returned findings describe individual record relationships.
No aggregate CLEAN, approval or independent-judgment result is specified.

## Serialization

Use UTF-8 JSON. Each fixture contains:
- fixture_id and spec_revision;
- input: adoption_id, registry, canonical_identities;
- expected: relationship findings, never passed to the checker.

registry maps exact record IDs to objects whose id matches the key.
Each object has a kind: adoption, output, presentation, source or
verification. These are experiment record discriminators, not additions
to PHAGE's diagnostic taxonomy.

Shared output binding:
{output_id, output_version, content}.
content is an ordered list of [portion_id, exact_text] pairs.
Versions are positive JSON integers; booleans are not versions.
Portion IDs are unique within content.

adoption:
{id, kind, decision_maker, decision_context, output_binding,
 adopted_portions, presentation_ref}.

output:
{id, kind, version, producer, content, citations}.
Each citation is {portion_id, source_id, source_version,
 source_content, verification_ref}.
Control has one P1 citation; P2 has no citation.

presentation:
{id, kind, recorder, recipient, decision_context, output_binding,
 presented_portions}.

source:
{id, kind, version, content}.

verification:
{id, kind, recorder, output_binding, portion_id, portion_text,
 source_id, source_version, source_content}.

Concrete values are those fixed in DECISION_INPUT_REUSE_SPEC.md.
Control verification_ref is VERIFY-01, retained when that record is
removed in the missing-verification case.
Policy identities are HUMAN-01, AGENT-01, PRESENTER-01 and VERIFIER-01.
No alias resolution, normalization or mutable latest-version lookup.

## Result contract

Return a JSON-compatible object with:
- adoption_id;
- relationships: a mapping using the six keys below;
- adopted_support: per-adopted-portion citation and verification findings.

Relationship keys:
A: adoption output_binding matches the registered output.
S: P1 citation resolves to the exact source ID/version/content.
V: P1 verification binds to the registered output and exact source.
P: presentation binds to the registered output, recipient and context.
L: adoption and presentation output bindings, person and context agree.
C: adopted portions are included in recorded presented portions.

Experiment-local finding values:
- matched: all required records and bindings agree.
- mismatch: available records contradict a required binding.
- missing: a required referenced record cannot be resolved.
- not_asserted: no citation or verification assertion exists.
- not_assessable: prerequisite mismatch prevents this check.

These are test result values, not a PHAGE diagnostic taxonomy.
Evaluate relationships separately; do not short-circuit all findings
because adoption or another relationship fails.

For C, missing presentation yields missing. Otherwise, if A, P or L
is not matched, C is not_assessable. With those prerequisites matched,
an existing output portion outside presented_portions yields mismatch.

## Exact relationship expectations

| Case | A | S | V | P | L | C |
|---|---|---|---|---|---|---|
| control | matched | matched | matched | matched | matched | matched |
| content replacement | mismatch | matched | mismatch | mismatch | matched | not_assessable |
| version mismatch | mismatch | matched | matched | matched | mismatch | not_assessable |
| missing source | matched | missing | missing | matched | matched | matched |
| missing verification | matched | matched | missing | matched | matched | matched |
| missing presentation | matched | matched | matched | missing | missing | missing |
| unpresented adopted portion | matched | matched | matched | matched | matched | mismatch |

L may match two retained snapshots even when both differ from the
registered output; content replacement deliberately tests that distinction.

## Adopted portion support

adopted_support maps each adopted portion ID to:
{citation: finding, verification: finding}.

If A is not matched, both findings are not_assessable: support for the
registered output must not be attributed to a mismatched adopted snapshot.
Otherwise resolve support for that exact adopted portion.
No citation yields not_asserted for both fields.
A citation with no verification assertion yields verification=not_asserted;
a declared verification_ref whose record is absent yields missing.

Exact expectations:
- control: P1 citation=matched, verification=matched.
- content replacement: P1 both not_assessable.
- version mismatch: P1 both not_assessable.
- missing source: P1 citation=missing, verification=missing.
- missing verification: P1 citation=matched, verification=missing.
- missing presentation: P1 citation=matched, verification=matched.
- unpresented adopted portion: P2 both not_asserted.

Missing presentation does not erase independently inspectable support.
Recorded source/verification support does not establish presentation.

## RED and evidence discipline

Tests compare every relationship and adopted-support finding against
the frozen expectations, and verify that input records remain unchanged.
They also assert that no assessment gate or evaluator is invoked.

If the proposed production entry point does not exist, record an absent
entry point as baseline evidence. Import failure is not seven executed
differential cases. Do not fabricate a baseline checker returning answers
or reinterpret a DF-011 rejection as traceability validation.

If a new checker is required, record that executable reuse was not
established. Subsequent GREEN can support the new checker and, within
these cases, the pattern hypothesis; it cannot establish code reuse.

Preserve fixture, test, code and specification revisions with raw results.
No independent-judgment, source-truth or real-presentation claim follows.
No CLAIMS_STATUS promotion occurs in this docs-only change.
