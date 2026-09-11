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

BLOCKED = "BLOCKED"
NOT_DETERMINED = "NOT_DETERMINED"


_TRUST_MARKER_KEY = "_phage_trusted_origin_token"
_TRUSTED_ORIGIN_BINDINGS = {}


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

    _TRUSTED_ORIGIN_BINDINGS[token] = _content_snapshot(candidate)

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
