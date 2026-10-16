# External validation: schema manifest contract

Status: proposed; review before RED and implementation.
Base implementation: 2572409.
Extends EXTERNAL_VALIDATION_CONTRACT.md.
Scope: synthetic multi-decision snapshots only.

## Purpose and compatibility

Replace hand-written per-record mappings with reusable,
kind-scoped rules and deterministic concrete expansion.
Existing snapshot-specific manifests retain their historical
scope; do not rewrite their fixtures or execution records.
No institutional validation or claim promotion follows.

## Frozen schema and execution artifacts

Freeze schema_revision, rule IDs, selectors, path templates,
transformations, types, absence semantics and blocking policy
before executing against a source snapshot.
Schema rules must not embed particular decision or record IDs.

Separately freeze the source snapshot, decision inventory
and scoped coverage assertions before execution.
Coverage evidence may identify concrete records without
requiring a separate hand-written mapping for each record.

Persist an expansion artifact linking schema_revision,
source_snapshot_id, decision inventory revision, rule_id,
decision_id, bound record_id and concrete source/target paths.
Record zero-match selections explicitly.
Expansion is mechanical execution evidence, not a claim that
each expanded record received independent human review.

Never derive classifications from checker exception messages
or alter frozen rules to fit an observed checker result.

## Decision inventory and expected roots

The schema declares how to obtain a decision inventory.
Each entry identifies decision_id and its adoption reference,
with source paths and provenance for those identities.
Decision IDs must be unique within the inventory.
Do not construct the inventory solely from existing adoption
records: that would hide omitted adoption roots.

Inventory extraction rules and the resulting inventory are
versioned separately. Mechanical extraction is permitted;
inventing source identities or expected decisions is not.
An inventory derived only from an export does not establish
that all decisions in the source workflow were exported.
Record inventory coverage and exclusions explicitly.

Resolve an expected adoption by its inventory reference.
Resolve its output by the adoption's output binding.
An independently supplied output reference may also be used
when its provenance and resolution rule were frozen.
Conflicting references are input-validation failures;
never choose one silently.

An absent referenced root remains an expansion subject.
Apply scoped absence/coverage classification at that root,
even though no registry object matches the expected kind.
Do not invent descendants or an output ID when an absent
adoption provides no output reference.
Record downstream resolution as blocked by that ancestor.

A present record with the wrong kind is an input-validation
failure, not a zero-match selection or proof of absence.
An unavailable inventory is not an empty inventory.
Report unknown coverage or unmappability according to the
frozen evidence; do not report a successful empty batch.

## Template binding and selection

Each rule has a unique rule_id, expected record kind,
decision-scoped selector, source/target path templates,
mapping status, transformation, type, absence semantics,
coverage requirements and blocking policy.

For this revision, {record_id} is the only path variable.
It occupies one complete JSON Pointer segment.
Bind it to the exact registry key selected or referenced;
escape "~" as "~0" and "/" as "~1" before substitution.
Never interpret an ID as a path, wildcard or executable text.
Reject unknown variables, partial-segment variables and
malformed JSON Pointer escapes during schema validation.

Example: an output-kind rule with target template
/registry/{record_id}/version applies to each selected output.
The schema stores this rule once, regardless of batch size.
Concrete IDs belong in snapshots, inventories and expansion
artifacts, not in reusable schema rules.

Selectors follow frozen decision references: adoption root,
bound output, presentation reference, output citations and
their source/verification references.
Do not attach every registry record of a matching kind to
every decision. Shared referenced records may participate
in several decisions; preserve each decision association.

A referenced missing record is an expected subject, not
an optional empty selection. A present wrong-kind record
must fail validation before checker invocation.
Multiple rules producing the same decision/target path are
invalid, even if their declarations appear identical.
Sort expansion by decision_id, rule_id and concrete target
path; registry insertion order must not affect the result.

## Zero matches and classification

Zero matches alone establish neither absence nor success.
For an expected reference, preserve the referenced ID and
classify the missing record using frozen scoped evidence:
- established source absence: EXTERNAL_RECORD_ABSENT;
- declared representation limit: ADAPTER_UNMAPPABLE;
- insufficient or conflicting coverage: SOURCE_COVERAGE_UNKNOWN.

An optional collection with no asserted members records
selection_count=0 and no per-member finding.
This does not establish completeness of source coverage.
A required selection with no resolvable identity reports
unknown coverage or unmappability at its reference path;
never fabricate a record ID merely to expand a template.

A valid, explicitly empty decision inventory records zero
decisions and its coverage evidence. It is not aggregate PASS.
Missing or malformed selection declarations are schema
validation errors, not ordinary zero-match findings.

## Decision isolation and fail-loud behavior

Collect evidence findings per decision.
Required-input findings block only affected decisions.
Unaffected decisions remain eligible for checker execution.
Shared-record findings retain every affected decision ID.

Execution failures remain distinct from evidence findings.
Persist the failing stage, diagnostic code, original cause,
partial expansion and completed decision records; then raise.
Do not return an ordinary successful batch after catching
an execution failure. Unexecuted decisions must be marked
not executed, never inferred successful.
Deterministic decision order governs partial execution.
No aggregate PASS is introduced.

## Ancestor findings and report detail

When an expected record is absent, emit one primary finding
at its concrete record path for each affected decision.
Do not emit separate primary findings for every unreachable
child field. Record blocked descendant rule IDs and known
target paths as affected_targets beneath that finding.
Do not invent paths requiring unresolved record identities.

Grouping requires the same decision, missing ancestor,
classification and supporting evidence.
Preserve independently established child findings with
different classifications or evidence; never merge them
merely because their paths share a prefix.
A missing version field in a present output remains a
field-level finding, not an absent-output finding.

Each primary finding retains code, decision_id, rule_id,
concrete target_path, snapshot/schema/inventory revisions,
evidence references and explanation.
affected_targets retain their rule IDs, resolvable paths
and blocking effect. Grouping must not change eligibility
for checker execution or discard the expansion artifact.

Group within a decision before presenting cross-decision
summaries. Shared records must not erase decision attribution.
Persist sufficient detail to reconstruct which rules were
blocked and why. Historical flat findings remain unchanged.

## Required synthetic tests before implementation

Freeze a multi-decision snapshot and one reusable schema.
Include at least two evaluable decisions and one decision
with a missing adoption root retained in the inventory.
Assert complete results, expansion and per-decision call counts.

Required variations:
- add decisions with new IDs without editing schema rules;
- rename record IDs consistently, including IDs with "/" and "~";
- reorder registry entries without changing semantic results;
- keep an unaffected decision executable beside a blocked one;
- use identical exports with absent versus unknown evidence;
- cover missing output, optional zero members and a shared source;
- reject wrong-kind roots and duplicate expanded target paths;
- reject malformed templates and unresolved variables;
- distinguish an unavailable inventory from a valid empty one;
- retain field-level findings in otherwise present records;
- group missing-root descendants without losing blocking detail;
- inject a later checker failure and retain completed results,
  original cause and explicit not-executed decisions;
- retain the existing 45-test regression scope.

Record baseline and RED honestly.
An absent schema entry point is an availability observation,
not executed differential failure for every skipped case.
Freeze executable expectations before implementation.

Sequence: reviewed contract, frozen synthetic tests,
baseline/RED checkpoint, implementation, GREEN/regression,
validation record. No real institutional data before this
schema boundary has been implemented and checked.
No CLAIMS_STATUS promotion is part of this change.
