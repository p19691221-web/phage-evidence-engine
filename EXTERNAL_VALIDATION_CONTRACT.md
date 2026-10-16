# External-shaped validation: evidence and execution contract

Status: PROPOSED — docs only; review and merge before RED.
Baseline: b7b1357.
This round uses synthetic external-shaped data only.
No institutional data, external validation or claim promotion is included.

## Boundary

An external-validation wrapper separates source evidence, adaptation,
input validation and checker execution.
Existing inspect_adoption semantics remain unchanged in this proposal.

Classification uses a pre-execution frozen mapping manifest and source
coverage evidence. Never infer a category from exception text alone.
Findings attach to individual fields or records; multiple categories
may coexist in one case. No aggregate PASS is implied.

## Evidence findings

EXTERNAL_RECORD_ABSENT:
A scoped, authoritative source observation establishes an empty value
or absent record under documented null/absence semantics.
An export omission alone is insufficient.
Report normally; affected relationships are not assessable.

ADAPTER_UNMAPPABLE:
The frozen manifest declares that a required target field cannot be
mapped faithfully from the supplied source representation.
Report normally; do not invent replacement values.

SOURCE_COVERAGE_UNKNOWN:
Available evidence cannot distinguish source absence from omission,
filtering, access restrictions or incomplete export coverage.
Report unresolved; neither a workflow failure nor a successful check.
Do not silently reclassify this as EXTERNAL_RECORD_ABSENT.

## Fail-loud execution boundary

CHECKER_EXECUTION_ERROR:
After adaptation and checker-input validation succeed, an unexpected
checker failure is raised with this diagnostic code and original cause.
Do not translate it into absence, unmappability or a normal missing finding.

An adapter producing invalid input despite declaring a supported mapping
is an adapter contract violation, not automatically a checker defect.
It must also fail loudly, retaining stage=adaptation or input_validation.
Freeze its concrete exception type/code before executable tests.

Missing keys, duplicate portions, invalid identities and inconsistent
record kinds are not classified merely by their ValueError messages.
Use source evidence, mapping obligations and input validation to identify
the stage. Unknown attribution must not be invented after execution.

## Frozen mapping manifest

Record manifest ID/version and immutable source snapshot references.
For every checker-required field or record, specify:
- target path and applicable record scope;
- source field/query and source snapshot reference;
- mapping status: MAPPABLE or UNMAPPABLE;
- exact transformation and target type, when mappable;
- null, empty-value and absent-record semantics;
- coverage scope, exclusions and supporting evidence references;
- expected preflight finding, if any.

Record who supplied coverage assertions and when, and the manifest's
reviewed revision before execution. Coverage is scoped evidence,
not a global boolean inferred from export contents.

Do not manufacture output versions, presentation records or authority.
Adapter-generated bookkeeping IDs must be marked as such and cannot
stand in for source version identity or evidence of presentation.

## Root-record preflight

If adoption or its required output cannot be supplied, the wrapper must
not invoke inspect_adoption. Return checker_invoked=false,
checker_result=null, and the evidence-based findings with target paths
and evidence references.

Confirmed source absence yields EXTERNAL_RECORD_ABSENT.
A declared mapping limitation yields ADAPTER_UNMAPPABLE.
Uncertain export coverage yields SOURCE_COVERAGE_UNKNOWN.
These may coexist for different targets. None means PASS.

Do not fabricate an adoption/output record or call the checker merely
to obtain a ValueError. Do not fabricate relationship findings for
checks that were not executed.

Non-root omissions may reach the checker only when its input contract
permits them. Preserve checker findings separately from source-evidence
classification: checker "missing" alone does not prove source absence.

## Execution failure record

Normal evidence findings include code, target path, source snapshot,
manifest revision, evidence references and explanation.
Execution records also state checker_invoked and checker_result.

Unexpected failure raises a dedicated exception with stage, diagnostic
code and chained original cause. Persist a failure record, then re-raise.
Do not return a normal successful result after catching the exception.

The test harness may catch the raised failure to assert it; the production
wrapper must not swallow it. Missing evidence and execution failure are
independent observations, not mutually exclusive case labels.

## Required synthetic cases

Freeze concrete manifests, source snapshots and expected records
before executable tests. Include:

1. Complete mappable control: checker invoked once; preserve its result.
2. Confirmed absent adoption: EXTERNAL_RECORD_ABSENT; checker calls=0.
3. Confirmed absent output: EXTERNAL_RECORD_ABSENT; checker calls=0.
4. Required version mapping declared UNMAPPABLE:
   ADAPTER_UNMAPPABLE; checker calls=0.
5. Root omitted from an export of unknown coverage:
   SOURCE_COVERAGE_UNKNOWN; checker calls=0.
6. Same omitted root with authoritative scoped absence evidence:
   EXTERNAL_RECORD_ABSENT; checker calls=0.
7. Mapping promises valid input but adapter violates target shape:
   fail loudly at adaptation/input_validation; checker calls=0.
8. Valid checker input plus injected unexpected checker ValueError:
   CHECKER_EXECUTION_ERROR at checker_execution; calls=1;
   original exception retained as the cause.
9. Distinct blocked targets in one snapshot: preserve all applicable
   absence, unmappability and unknown-coverage findings; calls=0.

Cases 5 and 6 hold the exported records fixed and vary only the
pre-execution coverage evidence. Never classify from export omission alone.
Expected evidence findings are test expectations, not classification input.

## Baseline and delivery

First record current checker behavior for missing adoption, missing
output and injected unexpected ValueError. Preserve exception type,
message and execution context. Shared exception types show insufficient
diagnostic separation; messages alone do not establish source categories.

Then test the wrapper contract. An absent wrapper is an absent-entry
baseline, not nine executed differential failures.

Freeze concrete serialization, entry point, preflight rules, input
validation obligations, exception codes and failure-record persistence
before RED. Manifest defects must not masquerade as source findings.

Sequence: reviewed contract -> concrete test specification -> baseline
and RED -> implementation -> GREEN/regression -> validation record.
No claim promotion or real-institution validation follows from this round.
