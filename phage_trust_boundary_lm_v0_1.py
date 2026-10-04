"""Fixture-only L/M origin boundary; no operational issuance authorization.

Issued artifacts are opaque handles. Their payload, origin binding, and issuing
evidence token live in module-private records, not on the returned handle.
Python module privacy is a convention, not an isolation or cryptographic boundary.
"""

from copy import deepcopy
from dataclasses import dataclass
from weakref import WeakKeyDictionary

import phage_trust_evidence_origin_v0_1 as producer


class _Artifact:
    __slots__ = ("__weakref__",)


class _OriginToken:
    __slots__ = ("__weakref__",)


@dataclass(frozen=True)
class _OriginBinding:
    kind: str
    payload_snapshot: dict


@dataclass
class _ArtifactState:
    origin_token: _OriginToken
    evidence_origin_token: object
    payload: dict


# Weak keys release both records when the issued handle is no longer retained.
_ARTIFACT_STATES = WeakKeyDictionary()
_ORIGIN_BINDINGS = WeakKeyDictionary()


def _issue(kind, *, payload, producer_request):
    if type(payload) is not dict:
        raise TypeError("payload must be a plain dict")
    if "diagnostics" in producer_request:
        raise TypeError("callers must not supply diagnostics")

    diagnostics = {}
    evidence = producer.produce_trusted_evidence_authorized(
        diagnostics=diagnostics, **producer_request
    )
    permitted = (
        evidence is not None
        and diagnostics.get("authentication_status") == "ESTABLISHED"
        and diagnostics.get("authority_status") == "AUTHORIZED"
        and diagnostics.get("reason") == "VERIFIED_PRODUCTION_PERMITTED"
    )
    if not permitted:
        return {"artifact": None, "producer_diagnostics": diagnostics}

    snapshot = deepcopy(payload)
    state = _ArtifactState(
        origin_token=_OriginToken(),
        evidence_origin_token=evidence[producer._TRUST_MARKER_KEY],
        payload=deepcopy(snapshot),
    )
    artifact = _Artifact()
    _ORIGIN_BINDINGS[state.origin_token] = _OriginBinding(kind, snapshot)
    _ARTIFACT_STATES[artifact] = state
    return {"artifact": artifact, "producer_diagnostics": diagnostics}


def issue_decision(*, payload, producer_request):
    return _issue("decision", payload=payload, producer_request=producer_request)


def issue_audit_receipt(*, payload, producer_request):
    return _issue("audit_receipt", payload=payload, producer_request=producer_request)


def _state(candidate):
    if type(candidate) is not _Artifact:
        return None
    return _ARTIFACT_STATES.get(candidate)


def _verify(kind, candidate):
    state = _state(candidate)
    if state is None:
        return False
    binding = _ORIGIN_BINDINGS.get(state.origin_token)
    if binding is None or binding.kind != kind:
        return False
    return bool(binding.payload_snapshot == state.payload)


def verify_decision_origin(candidate):
    return _verify("decision", candidate)


def verify_audit_receipt_origin(candidate):
    return _verify("audit_receipt", candidate)


def _result(origin_status, effect_path):
    return {"origin_status": origin_status, "effect_path": effect_path}


def _consume(*, candidate, on_verified, verifier, prefix):
    # Catch verifier faults only: callback failures must propagate unchanged.
    try:
        verified = verifier(candidate)
    except Exception:
        return _result(prefix + "_VERIFICATION_ERROR", "BLOCKED")
    if verified is not True and verified is not False:
        return _result(prefix + "_VERIFICATION_ERROR", "BLOCKED")
    if verified is False:
        return _result(prefix + "_ORIGIN_UNVERIFIED", "BLOCKED")

    state = _state(candidate)
    binding = _ORIGIN_BINDINGS[state.origin_token]
    on_verified(deepcopy(binding.payload_snapshot))
    return _result(prefix + "_ORIGIN_VERIFIED", "NOT_DETERMINED")


def consume_decision(*, candidate, on_verified):
    return _consume(
        candidate=candidate, on_verified=on_verified,
        verifier=verify_decision_origin, prefix="DECISION",
    )


def consume_audit_receipt(*, candidate, on_verified):
    return _consume(
        candidate=candidate, on_verified=on_verified,
        verifier=verify_audit_receipt_origin, prefix="AUDIT",
    )


def _issued_state_and_binding(artifact):
    state = _state(artifact)
    if state is None:
        raise TypeError("test hook requires an issued artifact")
    binding = _ORIGIN_BINDINGS.get(state.origin_token)
    if binding is None:
        raise TypeError("test hook requires an issued artifact")
    return state, binding


def _issuance_provenance_for_test(artifact):
    _, binding = _issued_state_and_binding(artifact)
    return {"artifact_kind": binding.kind}


def _issuance_matches_evidence_for_test(artifact, candidate):
    state = _state(artifact)
    if state is None or type(candidate) is not dict:
        return False
    return candidate.get(producer._TRUST_MARKER_KEY) is state.evidence_origin_token


def _tamper(kind, artifact, payload):
    state, binding = _issued_state_and_binding(artifact)
    if binding.kind != kind:
        raise TypeError("test hook requires the matching artifact kind")
    state.payload = deepcopy(payload)


def _tamper_decision_for_test(artifact, *, payload):
    _tamper("decision", artifact, payload)


def _tamper_audit_receipt_for_test(artifact, *, payload):
    _tamper("audit_receipt", artifact, payload)
