# L/M executable boundary proposal v0.1

Status: PROPOSED TEST INTERFACE — requires review before implementation.
Prepared 2026-10-03 (Asia/Taipei); semantic source: reconstructed L/M
requirements approved through PR #87, main f904d02. This is a new interface
proposal, not recovered wording from the 2026-09-08 specification.

## Issuance scope and explicit modeling assumption
Evidence-producer authority does not establish authority to issue an operational
Decision or audit receipt. The issue_* entries below are fixture-only origin
constructors, not operational decision makers or audit services. A shared
producer request can construct both fixture kinds; this is a modeling assumption
for origin testing, not an inference of cross-kind authority.
No decision-issuer/receipt-issuer authority resolver is implemented or claimed.
Operational issuance is outside this interface and requires a separately
specified artifact-kind and payload-scoped authority boundary before use.

Store the issuing evidence's origin token in the artifact's private provenance
record alongside its kind and content snapshot. This links fixture construction
to the actual successful evidence-producer event. It does not establish payload
authorization, issuer legitimacy, or decision validity beyond origin.
The regression-only _issuance_provenance_for_test(artifact) returns only
artifact_kind for trace assertions; it must not expose the evidence origin token
or evidence candidate. The regression-only
_issuance_matches_evidence_for_test(artifact, candidate) returns exact True only
when candidate carries the identical evidence origin token recorded privately
for that artifact, and exact False for a different or missing token. This is an
origin-event identity comparison, not a field-equality check or an authorization
resolver. Neither hook returns the token or evidence candidate; trace results
are not authorization inputs.

## Module and issuance
Module: phage_trust_boundary_lm_v0_1.
issue_decision and issue_audit_receipt accept keyword payload (a plain dict
of fixture data) and producer_request (the existing producer entry kwargs).
They return artifact (opaque issued object or None) and producer_diagnostics.

Issuance must call phage_trust_evidence_origin_v0_1.
produce_trusted_evidence_authorized with a newly allocated dedicated
diagnostics dictionary. Reject non-plain payload dicts and any diagnostics key in producer_request
with TypeError before calling the gate or mutating state.
Callers must not supply diagnostics in producer_request.
Only a returned candidate together with ESTABLISHED, AUTHORIZED and
VERIFIED_PRODUCTION_PERMITTED permits artifact issuance. Preserve denial
and verifier-error diagnostics; do not issue an artifact on either path.
The payload must be isolated by a deep snapshot and content-bound to the
opaque artifact's module-private origin token. Evidence production is a
gate prerequisite; its dict must not be represented as a Decision or receipt.
Payloads here are fixture observations, not authoritative policy or decisions.

## Verification and protected use
verify_decision_origin and verify_audit_receipt_origin return exact True
only for a valid issued artifact with intact content, and exact False for
unverified origin. An exception or any non-boolean verifier return is a
verification error. The public consume_decision and consume_audit_receipt
accept candidate and on_verified keywords. Each call invokes the explicit
verifier before any callback, including repeat uses of the same artifact.
No cached or offline result may replace verification at use time.

Return exactly origin_status and effect_path. Origin statuses are
DECISION_ORIGIN_VERIFIED / DECISION_ORIGIN_UNVERIFIED /
DECISION_VERIFICATION_ERROR for L, and AUDIT_ORIGIN_VERIFIED /
AUDIT_ORIGIN_UNVERIFIED / AUDIT_VERIFICATION_ERROR for M.
Unverified and error results return BLOCKED and do not invoke the callback.
Verified results invoke the callback once with a deep copy of the bound
payload and return NOT_DETERMINED. Callback failures propagate, outside
verifier-error classification. Verification only permits fixture consumption;
it does not authorize an operational effect, Gateway ALLOW, or execution.
No receipt single-use or revocation policy is introduced.

The regression-only _tamper_decision_for_test and
_tamper_audit_receipt_for_test hooks change stored artifact payload without
changing its original content binding. It exists
to test hostile post-issuance mutation, not as an authorized receipt edit API.
Mocking the explicit verifier functions supplies deterministic G2 faults.

## RED baseline and scope
The test harness contains 34 tests. If the module is absent, tests fail
with an explicit surface assertion rather than an uncaught import error.
This is a module-surface RED, not evidence of 34 observed behavioral defects.
Once the surface exists, tests exercise positive controls, caller forgeries and cross-kind substitution,
verifier errors, strict verifier results, use-time revalidation, snapshot
isolation, producer hard-stop/denial/error integration, and receipt tampering.

A dedicated GitHub Actions workflow runs this test file directly on push and
pull_request, with Python 3.11. While the module is missing this check must be
RED; existing green checks cannot substitute for this run. Do not mark these
tests skipped or expected failures. Before implementation, retain a separate
surface-only stub commit and its behavioral failure record in the implementation
branch; do not describe the absent-module baseline as behavioral RED.

This PR adds no implementation and does not modify the frozen producer
verifier or contract, Schedule, Emergency Override, or G6. Test-interface
review must resolve any proposed expansion before the implementation PR.
