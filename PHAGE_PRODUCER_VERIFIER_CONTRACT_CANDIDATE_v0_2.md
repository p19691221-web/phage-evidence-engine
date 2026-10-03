# Producer verifier contract candidate v0.2

Status: CANDIDATE; not frozen, not merged. A separate local implementation
patch is supplied for review; this is not a main-branch implementation claim.
Prepared 2026-10-03 (Asia/Taipei).
Baseline: main 9d503474b49cd61404b1d044d5d3ac76c7ccdead;
implementation branch 7b05a9c4a2490d2a01e9d28c0d7417df7df197d8.

Sources: #83, PHAGE_TRUST_BOUNDARY_PRODUCER_AUTHORITY_VERIFIER_BINDING_BEHAVIOR_v0_1.md,
and REPO_GOVERNANCE.md at the baseline main commit.
The diagnostic interface below is a new proposal, not a claim about #83.

## Compatibility and input validation

Keep produce_trusted_evidence_authorized's candidate-or-None return interface.
Unsupported caller authority vocabulary raises NotImplementedError before
verification; supported caller values never establish effective authority.
The supported legacy vocabulary remains AUTHORIZED, UNRESOLVED, REVOKED.
UNKNOWN_STATE is an unsupported input, distinct from verifier result UNKNOWN.

## Proposed observable interface

Reserve an optional keyword diagnostics=None on the public producer entry.
If a dictionary is supplied, populate it with exactly these fields for the
verification decision: authentication_status, authority_status, reason.
It is output only: overwrite caller-provided values; never read them for
authorization. Do not forward diagnostics to the producer or store it in
trusted evidence. This preserves existing return semantics while exposing
the states needed by tests and later consumers. Callers omitting it retain
the existing candidate-or-None interface.
Reject a non-dictionary diagnostic sink with TypeError before verification.
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
Producer exceptions are outside verifier-error classification.
Every denied/error path must preserve the trusted-origin binding count.

## Merge and freeze boundaries

PR A test migration and the separate compatibility repair remain separate
changes. This candidate and its RED tests form PR B. Implement its behavior
in a separate PR C. Do not describe this contract as frozen until the
agreed interface is implemented and its regressions pass.
The candidate does not change G1-G5, evidence origin evaluation, G6, L/M,
or claim maturity. Required CI integration for the new test file is part
of PR B; a local RED record is not evidence that CI already runs it.
