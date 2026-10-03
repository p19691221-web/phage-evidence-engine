# Producer verifier contract candidate v0.2

Status: CANDIDATE; not frozen. PR #85 contains this candidate and its
implementation for review. Repository landing is determined by the PR
merge record, not this document's status. Contract approval/freeze is separate.
Prepared 2026-10-03 (Asia/Taipei).
Baseline: main 9d503474b49cd61404b1d044d5d3ac76c7ccdead;
implementation branch 7b05a9c4a2490d2a01e9d28c0d7417df7df197d8.

Sources: #83, PHAGE_TRUST_BOUNDARY_PRODUCER_AUTHORITY_VERIFIER_BINDING_BEHAVIOR_v0_1.md,
and REPO_GOVERNANCE.md at the baseline main commit.
The diagnostic interface below is a new proposal, not a claim about #83.

## Compatibility and input validation

Keep candidate returns for permitted production and None for ordinary denial.
Verifier failure on the non-diagnostic path raises ProducerVerificationError.
This is an intentional exception-interface extension.
Unsupported caller authority vocabulary raises NotImplementedError before
verification; supported caller values never establish effective authority.
The supported legacy vocabulary remains AUTHORIZED, UNRESOLVED, REVOKED.
UNKNOWN_STATE is an unsupported input, distinct from verifier result UNKNOWN.
All supported caller values are ignored for both permitting and denying
production. Caller REVOKED or UNRESOLVED does not override an AUTHORIZED
verifier result. Cancellation requires a separately specified interface.

## Proposed observable interface

Reserve an optional keyword diagnostics=None on the public producer entry.
If a dictionary is supplied, populate it with exactly these fields for the
verification decision: authentication_status, authority_status, reason.
It is output only: overwrite caller-provided values; never read them for
authorization. Do not forward diagnostics to the producer or store it in
trusted evidence. The dictionary contains gate decisions, not production
completion results. Reject non-plain dictionaries (including subclasses),
and the trusted-origin binding registry itself, with TypeError before any
verification or diagnostic mutation. The module's globals dictionary and
any dictionary containing the evidence trust-marker key are also rejected.
The caller must supply a dedicated diagnostic container, not an evidence
candidate or a shared state dictionary. These checks reject known dangerous
aliases; they do not identify every possible shared plain dictionary.

If diagnostics is omitted or None, verifier exceptions, reported
VERIFICATION_ERROR, and unexpected verifier results raise the dedicated
ProducerVerificationError. It exposes stage ("authentication" or "authority")
and reason (AUTHENTICATION_VERIFICATION_ERROR or AUTHORITY_VERIFICATION_ERROR).
Authentication errors still prohibit authority evaluation; all verifier
errors prohibit production. Ordinary denials continue returning None.
With a valid diagnostic sink, verifier errors return None and populate the
distinct error fields. Consumers choosing the diagnostic path must inspect
the status fields and reason before interpreting the outcome.
The original verifier exception is not propagated or chained:
ProducerVerificationError has neither __cause__ nor __context__.
Unsupported legacy input raises before writing diagnostics; no verification
decision is produced for that invalid request.

Authentication vocabulary: ESTABLISHED, NOT_ESTABLISHED, VERIFICATION_ERROR.
Authority vocabulary: AUTHORIZED, UNRESOLVED, REVOKED, UNKNOWN,
VERIFICATION_ERROR, and not_evaluated (gate diagnostic only).
Missing/unverified authentication evidence retains NOT_ESTABLISHED; this
is the current seam's representation of the governance UNVERIFIED outcome.

## Composition and reasons

1. Validate legacy authority vocabulary.
2. Invoke authentication verifier once.
3. NOT_ESTABLISHED: return None, authority not_evaluated, reason
   AUTHENTICATION_NOT_ESTABLISHED. Authority and producer calls: zero.
4. Authentication exception or unexpected verifier result: fail closed as
   VERIFICATION_ERROR, authority not_evaluated, reason
   AUTHENTICATION_VERIFICATION_ERROR. Do not propagate the verifier exception.
5. Only ESTABLISHED permits one authority-verifier invocation.
6. Authority UNRESOLVED, REVOKED or UNKNOWN: preserve that exact result,
   return None, reason AUTHORITY_UNRESOLVED, AUTHORITY_REVOKED or
   AUTHORITY_UNKNOWN respectively.
7. Authority exception or unexpected verifier result: fail closed as
   VERIFICATION_ERROR, reason AUTHORITY_VERIFICATION_ERROR.
8. ESTABLISHED + AUTHORIZED: invoke producer exactly once, return its
   candidate, reason VERIFIED_PRODUCTION_PERMITTED.

The default authority verifier may still return only AUTHORIZED and
UNRESOLVED for its existing fixtures. Injecting other results tests the
gate's contract; it does not establish real revocation or policy support.
Producer exceptions are outside verifier-error classification and propagate.
VERIFIED_PRODUCTION_PERMITTED records the gate decision made before invoking
the producer; it does not claim that production completed successfully.
Every gate denial/verifier-error path must preserve trusted-origin bindings.
An invalid diagnostic sink is rejected without changing the registry.

## Merge and freeze boundaries

PR #85 includes the three pre-existing branch commits plus separate commits
for test migration (e1abb30), compatibility repair (5bd45cb), candidate/RED
tests (71c187a), and implementation (ac96110). These are separate commits
within one PR, not separate PR A/B/C submissions. Review corrections follow
as additional commits. Do not describe the contract as frozen until reviewed,
explicitly approved and recorded through the contract change process.
The candidate does not change G1-G5, evidence origin evaluation, G6, L/M,
or claim maturity. The PR changes the existing CI workflow to run the new
test file. CI results are established by run records, not this document.
