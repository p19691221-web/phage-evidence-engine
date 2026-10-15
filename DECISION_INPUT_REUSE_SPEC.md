# Decision input reuse: synthetic differential specification

Status: PROPOSED — docs only; freeze through review before RED.
Hypothesis baseline: 2e2dbaa.
Decision input traceability remains OPEN.
No DF-011 evidence or implementation support transfers.

## Synthetic control records

Decision-maker: HUMAN-01.
Decision context: DECISION-01 / MATERIAL_SELECTION.
AI producer: AGENT-01.
Presentation recorder: PRESENTER-01.
Verification recorder: VERIFIER-01.

Identifiers are exact case-sensitive ASCII strings, with no aliases.
Identity, recorder authenticity and distinct-principal assumptions are
supplied by synthetic policy, not established by these records.

AI output OUT-01 version 1 contains exactly these ordered portions:
- P1: "Option A has lower upfront cost."
- P2: "Option B requires further review."

Content identity is the exact ordered list of portion ID/text pairs.
No whitespace, Unicode, punctuation or case normalization is performed.
ID/version labels alone are insufficient. A digest may supplement but
must not replace comparison to the fixed content in this synthetic test.

ADOPT-01 binds HUMAN-01 and DECISION-01 to OUT-01/version 1,
the complete content snapshot above, and adopted portion P1.
It cites presentation record PRESENT-01.

PRESENT-01 records PRESENTER-01 making OUT-01/version 1 available
to HUMAN-01 in DECISION-01, with the same complete content snapshot.
Its presented portions are [P1].
It does not assert that HUMAN-01 read or understood the material.

OUT-01 cites SOURCE-01/version 1 for P1.
SOURCE-01 contains exactly: "Synthetic cost comparison: A=10, B=20."
VERIFY-01 binds VERIFIER-01 to P1's exact text, OUT-01/version 1
and SOURCE-01/version 1 with that exact source content snapshot.
It records a verification assertion, not proof of truth or independence.

All records are inspectable entries in a policy-supplied registry.
Freeze registry snapshots in each fixture; do not resolve mutable latest
versions or infer missing records from adoption declarations.

## Separate relationship checks

Report findings per relationship; do not collapse them into one PASS flag:
- adoption-to-output identity and adopted-portion membership;
- output citation-to-source resolution and source content identity;
- verification-record binding to the exact P1 output/source snapshots;
- presentation-record binding to recipient, context and output snapshot;
- adopted portions being a subset of recorded presented portions.

These are descriptive checks for this experiment, not a new product
taxonomy. An intact relationship does not repair a different broken one.
Verification and presentation findings describe recorded support only.

## Seven fixed differential cases

Control: all specified relationships are intact. Adopted P1 is covered
by the presentation record and the P1 verification record.

1. Content replacement: change only OUT-01 P1 text to
   "Option A has higher upfront cost.", retaining ID/version.
   Adoption, presentation and verification snapshots no longer match
   that output. The source entry itself still resolves.

2. Version mismatch: change only ADOPT-01's output version to 2.
   Adoption cannot bind to registered OUT-01/version 1 or PRESENT-01.
   Original P1 source, verification and presentation records remain
   mutually consistent for version 1.

3. Missing source: remove only SOURCE-01 from the registry.
   The citation cannot resolve; VERIFY-01 cannot be corroborated
   against that source. Adoption/output and presentation links remain.

4. Missing verification: remove only VERIFY-01.
   P1 has no recorded verification support. Adoption/output,
   source resolution and presentation relationships remain intact.

5. Missing presentation: remove only PRESENT-01.
   Adoption cannot resolve its presentation reference. Do not infer
   presentation from ADOPT-01. Output/source/verification links remain.

6. Unpresented adopted portion: change only ADOPT-01's adopted portions
   from [P1] to [P2].
   P2 exists in the output but is outside presented portions [P1].
   P2 has no specified citation or verification support; absence of
   those assertions is not a broken P1 citation or verification.
   The original P1 records and output identity remain intact.

## Evidence interpretation

Broken bindings, missing records and absent assertions must remain
distinguishable. Do not treat an unverified assertion as verified,
or absence of support as proof that an assertion is false.
No case establishes attention, comprehension, independent human
judgment, automation bias or substantive correctness.

## Gate -1 evaluation boundary

Reuse means reusing exact binding comparison and registry resolution
as structural operations while preserving adoption semantics.
Do not encode adoption as DF-011 approval or manufacture an authority
grant to make run_expectation_gate accept an adoption record.

Before RED, the test plan must name the concrete existing operations
being reused, or explicitly record that no reusable operation exists.
A new checker passing these cases alone does not prove code reuse.

If only the design pattern transfers, report pattern-level reuse
separately from executable component reuse. DF-011 test support
does not transfer in either case.

## Delivery boundary

This document fixes semantic records and expected findings only.
Concrete serialization, result fields and entry points must be reviewed
before executable RED tests; they must preserve these distinctions.
No taxonomy, executable fixture, implementation or claim promotion
is established here. Decision input traceability remains OPEN.
