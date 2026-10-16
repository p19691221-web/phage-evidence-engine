# External-shaped validation: executable test specification

Status: proposed; review before baseline/RED.
Base revision: fb23f87.
Governing contract: EXTERNAL_VALIDATION_CONTRACT.md.
Scope: synthetic external-shaped data only.

## Entry point and boundaries

Planned module: external_validation.py.
Planned entry point:
run_external_validation(*, source_snapshot, manifest,
                        adapter, checker, failure_sink)

The adapter receives the source snapshot and frozen manifest.
It returns keyword arguments for inspect_adoption.
The checker is injectable; production uses inspect_adoption.
Tests count checker calls and preserve original exceptions.
Neither source inputs nor the manifest may be mutated.

## Normal execution record

Return a JSON-compatible object containing:
- manifest_revision;
- source_snapshot_id;
- findings;
- checker_invoked;
- checker_result.

Each finding contains code, target_path, source_snapshot_id,
manifest_revision, evidence_refs and explanation.
Blocked root inputs require checker_invoked=false and
checker_result=null. Do not fabricate relationship results.
A successful checker call preserves its complete result.
There is no aggregate PASS field.

## Frozen manifest and source snapshot

The source snapshot contains snapshot_id and payload.
The manifest contains manifest_revision, source_snapshot_id,
reviewed_by, reviewed_at, evidence and mappings.
Its source_snapshot_id must match the supplied snapshot.

Each evidence entry has a unique evidence_id, reference,
asserted_by, asserted_at and explicit coverage scope.
Synthetic assertions must be labelled synthetic.
Freezing records the reviewed revision before execution;
it does not establish the truth of supplied assertions.

Each mapping contains:
- target_path and required_for_checker;
- source_path, using JSON Pointer when mappable;
- mapping_status: MAPPABLE or UNMAPPABLE;
- transformation and target_type;
- absence_semantics for missing, null and empty values;
- coverage_scope and exclusions;
- coverage_evidence_refs.

UNMAPPABLE entries also contain a reason.
Every required target must have a mapping entry.
Missing entries are invalid manifests, not UNMAPPABLE.
Evidence references must resolve within the manifest.
Expected findings belong only in test expectations;
they must not be supplied as classification inputs.

Tests use an identity transformation initially.
Additional transformations require explicit specification.
Adapter bookkeeping IDs must be identified separately
and cannot substitute for source version identities.

## Preflight classification rules

Validate the manifest before classifying source evidence.
For each mapping, apply these rules independently:

1. UNMAPPABLE produces ADAPTER_UNMAPPABLE.
2. For MAPPABLE entries, inspect the declared source path.
3. A missing, null or empty value establishes absence only
   when its documented semantics and referenced evidence
   establish source absence for that exact coverage scope.
4. Otherwise an omitted or ambiguous value produces
   SOURCE_COVERAGE_UNKNOWN.
5. A present value proceeds to adaptation and validation;
   its presence alone does not establish semantic validity.

EXTERNAL_RECORD_ABSENT requires scoped absence evidence.
Export omission alone cannot satisfy this requirement.
Conflicting coverage assertions cannot establish absence;
report SOURCE_COVERAGE_UNKNOWN with both evidence references.

Findings are collected for all mappings before deciding
whether checker execution is blocked.
Any finding on a required_for_checker target blocks execution.
Blocked execution skips both adapter and checker.
Other findings remain in the execution record.

Non-root missing records may reach the checker only where
its input contract permits their omission.
A checker result of "missing" does not independently prove
EXTERNAL_RECORD_ABSENT in the source workflow.

Never classify by exception message or expected test result.
Absence, mapping limits and unknown coverage are findings;
none is a successful validation of the affected relationship.

## Preflight classification rules

Validate the manifest before classifying source evidence.
For each mapping, apply these rules independently:

1. UNMAPPABLE produces ADAPTER_UNMAPPABLE.
2. For MAPPABLE entries, inspect the declared source path.
3. A missing, null or empty value establishes absence only
   when its documented semantics and referenced evidence
   establish source absence for that exact coverage scope.
4. Otherwise an omitted or ambiguous value produces
   SOURCE_COVERAGE_UNKNOWN.
5. A present value proceeds to adaptation and validation;
   its presence alone does not establish semantic validity.

EXTERNAL_RECORD_ABSENT requires scoped absence evidence.
Export omission alone cannot satisfy this requirement.
Conflicting coverage assertions cannot establish absence;
report SOURCE_COVERAGE_UNKNOWN with both evidence references.

Findings are collected for all mappings before deciding
whether checker execution is blocked.
Any finding on a required_for_checker target blocks execution.
Blocked execution skips both adapter and checker.
Other findings remain in the execution record.

Non-root missing records may reach the checker only where
its input contract permits their omission.
A checker result of "missing" does not independently prove
EXTERNAL_RECORD_ABSENT in the source workflow.

Never classify by exception message or expected test result.
Absence, mapping limits and unknown coverage are findings;
none is a successful validation of the affected relationship.

## Fail-loud execution failures

ExternalValidationError is the dedicated wrapper exception.
It carries stage, code and failure_record.
Wrap the original exception using explicit exception chaining.

Freeze these stage/code pairs:
- manifest_validation / MANIFEST_INVALID;
- adaptation / ADAPTER_EXECUTION_ERROR;
- input_validation / ADAPTED_INPUT_INVALID;
- checker_execution / CHECKER_EXECUTION_ERROR.

Input validation checks the checker argument structure,
canonical identities, registry key/id/kind consistency,
required root records, and unique portion/citation IDs.
It must also check field types used by the checker.
An adapter output that violates these obligations fails
before checker invocation; do not infer source absence.

The failure record contains the normal execution fields,
plus stage, code, cause_type and cause_message.
checker_result is null when checker execution fails.
checker_invoked records whether the checker was called.
Previously collected evidence findings remain attached.

Call failure_sink(record) before raising the wrapper error.
The sink must acknowledge persistence by returning normally.
If it raises, still raise the original wrapper error:
retain the original cause and attach the sink exception
as persistence_error. Never report persistence as successful.
The caller must receive an exception, not a normal result.

Tests use a collecting sink and inspect chained exceptions.
A separate sink-failure test checks both errors survive.

## Nine core synthetic cases

Each case freezes its snapshot, manifest and expectations
before execution. Call counts below refer to the checker.

1. Complete mappable control: no findings; one call;
   preserve the full result from the existing checker.
2. Confirmed absent adoption: EXTERNAL_RECORD_ABSENT
   on the adoption root; zero calls; null checker_result.
3. Confirmed absent output: EXTERNAL_RECORD_ABSENT
   on the output root; zero calls; null checker_result.
4. Required output version declared UNMAPPABLE:
   ADAPTER_UNMAPPABLE; zero calls; null checker_result.
5. Adoption omitted from export, coverage unknown:
   SOURCE_COVERAGE_UNKNOWN; zero calls.
6. Identical export payload to case 5, but frozen scoped
   evidence establishes adoption absence:
   EXTERNAL_RECORD_ABSENT; zero calls.
7. Valid manifest and present source values; injected
   adapter returns an invalid registry record:
   ADAPTED_INPUT_INVALID at input_validation; zero calls.
8. Valid adapted input; injected checker raises ValueError:
   CHECKER_EXECUTION_ERROR at checker_execution; one call;
   preserve that exact exception as the chained cause.
9. Three distinct targets independently establish absence,
   unmappability and unknown coverage:
   retain all three findings; zero calls.

For cases 2-6 and 9, assert adapter calls are also zero.
Normal blocked records must have checker_invoked=false
and checker_result=null. No relationship result is invented.
Compare complete records, including target paths and
evidence references; code-only assertions are insufficient.

## Boundary tests and baseline evidence

Additional tests cover invalid manifests, adapter exceptions,
conflicting coverage evidence and failure-sink exceptions.
Invalid manifests and adapter failures must invoke no checker.
Also test optional missing presentation: retain its source
finding while preserving the checker's permitted missing result.
Assert input immutability on normal and exceptional paths.

Record the current checker baseline separately:
- missing adoption raises ValueError;
- missing output raises ValueError;
- an injected execution fault also raises ValueError.
Retain exact types, messages, inputs and revision.
This demonstrates type-level conflation, not identical causes.
Do not classify these observations by parsing their messages.

An absent wrapper entry point is an availability baseline,
not differential RED for all nine cases.
After tests and fixtures are frozen, record which assertions
fail against existing behavior and why, before implementation.
Do not use skips or expected failures as evidence of support.

Expected records are test-owned artifacts, never wrapper inputs.
For cases 5 and 6, assert export payloads are exactly equal.
Their differing findings must follow only from the separately
frozen coverage evidence and documented absence semantics.

Keep existing checker regression tests in the GREEN run.
Record executed counts and distinguish baseline from RED.
This specification establishes no external validation,
institutional result or promotion of CLAIMS_STATUS.
