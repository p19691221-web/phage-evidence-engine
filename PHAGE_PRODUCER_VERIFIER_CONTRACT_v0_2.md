# Producer verifier contract v0.2

Status: freeze proposed. This contract becomes FROZEN only when the separate
contract-freeze PR containing this document is explicitly approved and merged.
That PR's merge record supplies the approval and effective revision; this
unmerged proposal does not authorize consumer expansion.
Prepared 2026-10-03 (Asia/Taipei).

## Scope and provenance

This document freezes the public producer gate semantics implemented by PR #85,
squash commit 86cef24, reviewed at head e1d884ad289c1a88e1cd910218956c940e91b683.
The historical candidate remains PHAGE_PRODUCER_VERIFIER_CONTRACT_CANDIDATE_v0_2.md.
This v0.2 document governs the observable interface and composition specified
below; the v0.1 boundary distinctions remain applicable. The v0.1 document's
NOT YET IMPLEMENTED statement describes its original baseline, not current main.

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

## Observable interface

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

## Approval and change boundary

Approval of the separate freeze PR accepts these semantics and the disclosed
shared-dictionary limitation. Record the freeze PR URL and merge revision through
GitHub's durable PR/merge history; do not invent a self-referential commit SHA.
After approval and merge, consumers must use this frozen contract. Later changes
require a separate contract/verifier PR and consumer rebase. L/M integration must
not rewrite verifier modules or this contract to satisfy consumer requirements.

## Validation and limits

Implementation-head CI at e1d884a: eight checks passed. Local contract tests:
20/20; legacy origin regression: 5/5; G6 harness: 11/11. Reviewer closeout reported
25/25 targeted mutants detected and P7/P8/N07 closed, with no remaining findings.
Reviewer runtime was Python 3.13; CI runtime was Python 3.11. Targeted mutations
are not exhaustive. The e1abb30 test migration was not independently reviewed.
These records establish the reviewed gate scope, not general revocation support,
thread safety, external pilot support, or consumer integration closure.

This documentation-only freeze changes no executable behavior, G1-G5 semantics,
evidence-origin evaluation, G6, L/M implementation, or product claim maturity.
