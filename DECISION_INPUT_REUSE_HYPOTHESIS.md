# Decision input traceability: Gate -1 reuse hypothesis

Status: PROPOSED / UNVALIDATED — docs only.
Baseline: d8dbe84.
Decision input traceability remains OPEN.
Independent human judgment remains OUT OF CURRENT SCOPE.

## Question

Can the binding-and-registry pattern represent an adoption record and
detect broken traceability without introducing a new taxonomy?

This concerns reuse of a design pattern, not reuse of DF-011 evidence
or a claim that run_expectation_gate supports human adoption.
An approval event and an adoption event have different meanings.

## Candidate mapping

Bind an adoption record to:
- decision-maker identity and decision context;
- the exact AI output content and version;
- the portions recorded as adopted;
- a presentation record identifying the output made available;
- referenced source records and any separate verification records.

Registry entries must resolve to inspectable, version-bound records.
A version label alone does not establish content identity.
PROPOSAL != EVIDENCE applies at the human consumption boundary:
adoption does not turn an AI proposal into independently verified evidence.

## Separate evidentiary questions

1. What sources does the AI output cite?
2. What content has separately recorded verification support?
3. What output does a presentation record say was made available?

These questions must not collapse into one supported/unsupported flag.
A presentation record does not prove attention, comprehension or judgment.
A source citation alone does not establish verification or independence.
An adoption declaration alone does not prove what was presented.

## Proposed differential cases

Start with one synthetic control containing inspectable, mutually
consistent adoption, output, presentation, source and verification records.
Freeze concrete records and expected findings before executable tests.

Change one relationship at a time:
- Replace output content while retaining its ID/version label.
- Bind adoption to a version different from the presentation record.
- Remove a referenced source from the registry.
- Retain a source citation but remove its verification record.
- Remove presentation support while retaining the adoption declaration.
- Claim adoption of a portion outside the recorded presented content.

Keep unrelated records fixed. Expected findings must distinguish broken
traceability, absent verification support and absent presentation support.
Missing verification alone must not erase otherwise intact traceability.
A complete record must not imply independent human judgment.

## Falsification and decision rule

Reuse is not established merely because the records fit in a dictionary.
It requires detecting the specified broken relationships while preserving
the separate evidentiary questions and the intact control relationships.

If reuse requires treating adoption as approval, treating a proposal as
evidence, or inferring presentation from adoption alone, reject that mapping.
If additional relations are required, document the minimal missing
semantics before proposing any taxonomy or implementation extension.

A successful synthetic reuse test supports only its tested relationships.
It does not establish real-world presentation, source authenticity,
verification independence, decision quality or institutional authority.

## Next checkpoint

Review and merge this hypothesis document.
Then specify concrete bindings, registry trust assumptions, content identity,
presentation/verification evidence rules and differential expected findings.
Review and freeze that specification before RED.
No executable tests, engine changes or claim promotion occur here.
