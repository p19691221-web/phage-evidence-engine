"""
Minimal PHAGE Trust Evidence Origin implementation v0.1.

Implements only the frozen G1-G3 regression boundary:
- G1 forged evidence origin fails closed
- G2 verifier internal failure fails closed distinctly
- G3 public entry delegates through the verifier seam

This is a research-prototype trust marker, not a production
identity, signature, attestation, or provenance system.
"""

EVIDENCE_ORIGIN_VERIFIED = "EVIDENCE_ORIGIN_VERIFIED"
EVIDENCE_ORIGIN_UNVERIFIED = "EVIDENCE_ORIGIN_UNVERIFIED"
EVIDENCE_VERIFICATION_ERROR = "EVIDENCE_VERIFICATION_ERROR"
_PRODUCER_AUTHORITY_VERIFIED_FIXTURE = object()
BLOCKED = "BLOCKED"
NOT_DETERMINED = "NOT_DETERMINED"


_TRUST_MARKER_KEY = "_phage_trusted_origin_token"
_TRUSTED_ORIGIN_BINDINGS = {}

_CALLER_AUTHENTICATION_VERIFIED_FIXTURE = object()
def _result(*, origin_status, effect_path):
    return {
        "origin_status": origin_status,
        "effect_path": effect_path,
    }

def _content_snapshot(candidate):
    return (
        candidate.get("value"),
        candidate.get("source"),
        candidate.get("schedule_ref"),
        candidate.get("policy_version"),
        candidate.get("observed_at"),
    )
def verify_caller_authentication(*args, **kwargs):
    """
    Trusted caller-authentication verifier seam.

    The module-owned verified fixture represents the current
    verifier-positive prototype path.

    Missing or other supplied evidence fails closed.
    """

    if (
        len(args) == 1
        and not kwargs
        and args[0] is _CALLER_AUTHENTICATION_VERIFIED_FIXTURE
    ):
        return "ESTABLISHED"

    return "NOT_ESTABLISHED"

def produce_trusted_evidence_authorized(
    *,
    authority_status,
    caller_authentication_status=None,
    caller_authentication_evidence=None,
    **producer_kwargs,
):
    """
    Producer-authority gated entry point.

    Caller-supplied authentication status is retained only for
    compatibility and is not authoritative.

    Trusted production requires verifier-established authentication.
    """

    if authority_status == "UNRESOLVED":
        return None

    if authority_status == "REVOKED":
        return None

    if authority_status != "AUTHORIZED":
        raise NotImplementedError(
            "producer-authority behavior is not implemented for "
            f"{authority_status}"
        )

    if caller_authentication_evidence is None:
        effective_authentication_status = verify_caller_authentication()
    else:
        effective_authentication_status = verify_caller_authentication(
            caller_authentication_evidence
        )

    if effective_authentication_status != "ESTABLISHED":
        return None

    return _produce_trusted_evidence(**producer_kwargs)
def _produce_trusted_evidence(
    *,
    value,
    source,
    schedule_ref,
    policy_version,
    observed_at,
):
    """
    Minimal in-process producer path for the prototype.

    Current G1-G3 regression does not independently validate
    positive trusted-origin acceptance.
    """
    token = object()

    candidate = {
        "value": value,
        "source": source,
        "schedule_ref": schedule_ref,
        "policy_version": policy_version,
        "observed_at": observed_at,
        _TRUST_MARKER_KEY: token,
    }

    _TRUSTED_ORIGIN_BINDINGS[token] = (
        _content_snapshot(candidate)
    )
    return candidate

def _default_verifier(candidate):
    if not isinstance(candidate, dict):
        return False

    token = candidate.get(_TRUST_MARKER_KEY)

    if token not in _TRUSTED_ORIGIN_BINDINGS:
        return False

    return (
        _TRUSTED_ORIGIN_BINDINGS[token]
        == _content_snapshot(candidate)
    )


def _evaluate_evidence_origin_with_verifier(*, candidate, verifier):
    try:
        verified = bool(verifier(candidate))
    except Exception:
        return _result(
            origin_status=EVIDENCE_VERIFICATION_ERROR,
            effect_path=BLOCKED,
        )

    if not verified:
        return _result(
            origin_status=EVIDENCE_ORIGIN_UNVERIFIED,
            effect_path=BLOCKED,
        )

    return _result(
        origin_status=EVIDENCE_ORIGIN_VERIFIED,
        effect_path=NOT_DETERMINED,
    )


def evaluate_evidence_origin(*, candidate):
    return _evaluate_evidence_origin_with_verifier(
        candidate=candidate,
        verifier=_default_verifier,
    )
def verify_producer_authority(*args, **kwargs):
    if (
        len(args) == 1
        and not kwargs
        and args[0] is _PRODUCER_AUTHORITY_VERIFIED_FIXTURE
    ):
        return "AUTHORIZED"

    return "UNRESOLVED"
