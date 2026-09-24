"""
Executable regression harness for PHAGE Applicable Evidence Reuse G6 v0.1.

Phase 1 freezes only:
- module loader behavior;
- public entry-point name;
- reuse-result shape;
- allowed reuse status vocabulary;
- the meaningful RED baseline.

G6A is the first executable semantic fixture added after the
contract-surface baseline was reviewed.

G6C-G6H3 remain outside this phase.
No reuse enforcement implementation belongs here.
"""

import importlib
from datetime import datetime, timedelta, timezone
AT = datetime(2026, 9, 16, 8, 0, tzinfo=timezone.utc)

MODULE = "phage_applicable_evidence_reuse_v0_1"
ENTRY_POINT = "evaluate_applicable_evidence_reuse"

REUSE_ALLOWED = "REUSE_ALLOWED"
REUSE_UNRESOLVED = "REUSE_UNRESOLVED"
REUSE_INVALIDATED = "REUSE_INVALIDATED"

ALLOWED_REUSE_STATUSES = {
    REUSE_ALLOWED,
    REUSE_UNRESOLVED,
    REUSE_INVALIDATED,
}

REQUIRED_RESULT_KEYS = {"reuse_status", "reason_code"}

FORBIDDEN_RESULT_KEYS = {
    "authorized",
    "authorization_status",
    "decision",
    "effect_path",
    "applicable",
}


def _load_module():
    try:
        return importlib.import_module(MODULE)
    except ModuleNotFoundError as exc:
        if exc.name == MODULE:
            return None
        raise


def _assert_result_shape(result):
    assert isinstance(result, dict), (
        "G6 reuse evaluation must return a dict regression observation"
    )

    assert REQUIRED_RESULT_KEYS.issubset(result), (
        "G6 reuse result missing keys: "
        f"{REQUIRED_RESULT_KEYS - set(result)}"
    )

    forbidden_present = FORBIDDEN_RESULT_KEYS.intersection(result)
    assert not forbidden_present, (
        "G6 reuse result must not expose authorization/effect semantics: "
        f"{forbidden_present}"
    )

    assert result["reuse_status"] in ALLOWED_REUSE_STATUSES, (
        "G6 reuse_status must be one of "
        f"{sorted(ALLOWED_REUSE_STATUSES)}"
    )

    assert isinstance(result["reason_code"], str), (
        "G6 reason_code must use a canonical string representation"
    )

    assert result["reason_code"], (
        "G6 reason_code must not be empty"
    )
def _g6a_verified_facts():
    original_context = {
        "subject": "agent-A",
        "action": "READ",
        "target": "record-123",
        "scope": "TIME",
    }

    dependency_closure = (
        "policy:v17",
        "schedule:v8",
        "grant:g1",
    )

    return {
        "prior_result": "APPLICABLE",
        "original_evidence_bundle_id": "bundle-A",
        "candidate_evidence_bundle_id": "bundle-A",
        "original_context": original_context,
        "current_context": dict(original_context),
        "original_dependency_closure": dependency_closure,
        "current_dependency_closure": dependency_closure,
        "dependency_closure_complete": True,
        "original_authority_derivation_id": "authority-path-A",
        "current_authority_derivation_id": "authority-path-A",
        "origin_integrity_reverified": True,
        "authoritative_current_state_resolved": True,
        "all_relevant_dependencies_unchanged": True,
        "original_observed_at": AT,
        "original_evidence_valid_until": AT + timedelta(minutes=10),
        "trusted_current_time": AT + timedelta(minutes=1),
        "max_evidence_reuse_window": timedelta(minutes=5),
    }


def run_fixture_g6a(module):
    assert module is not None, (
        "G6A contract RED: phage_applicable_evidence_reuse_v0_1 "
        "is not implemented"
    )

    evaluate_verified = getattr(
        module,
        "_evaluate_applicable_evidence_reuse_from_verified_facts",
        None,
    )

    assert callable(evaluate_verified), (
        "G6A contract RED: verified-facts reuse seam is not implemented"
    )

    result = evaluate_verified(
        verified_facts=_g6a_verified_facts(),
    )

    _assert_result_shape(result)

    assert result["reuse_status"] == REUSE_ALLOWED
    assert result["reason_code"] == "ALL_REUSE_CONDITIONS_VERIFIED"    

def _g6b_verified_facts():
    facts = _g6a_verified_facts()
    facts["candidate_evidence_bundle_id"] = "bundle-B"
    return facts


def run_fixture_g6b(module):
    assert module is not None, (
        "G6B contract RED: phage_applicable_evidence_reuse_v0_1 "
        "is not implemented"
    )

    evaluate_verified = getattr(
        module,
        "_evaluate_applicable_evidence_reuse_from_verified_facts",
        None,
    )

    assert callable(evaluate_verified), (
        "G6B contract RED: verified-facts reuse seam is not implemented"
    )

    result = evaluate_verified(
        verified_facts=_g6b_verified_facts(),
    )

    _assert_result_shape(result)

    assert result["reuse_status"] == REUSE_INVALIDATED
    assert result["reason_code"] == "EVIDENCE_BUNDLE_SUBSTITUTION"

def run_contract_surface(module):
    assert module is not None, (
        "G6 contract RED: phage_applicable_evidence_reuse_v0_1 "
        "is not implemented"
    )

    entry_point = getattr(module, ENTRY_POINT, None)

    assert callable(entry_point), (
        "G6 contract RED: evaluate_applicable_evidence_reuse "
        "is not implemented"
    )


def run():
    module = _load_module()

    fixtures = (
    (
        "G6_CONTRACT_SURFACE",
        "loader_and_entrypoint",
        lambda: run_contract_surface(module),
    ),
    (
        "G6A",
        "valid_exact_bundle_reuse",
        lambda: run_fixture_g6a(module),
    ),
    (
        "G6B",
        "evidence_bundle_substitution",
        lambda: run_fixture_g6b(module),
    ),
    (
        "G6C",
        "dependency_closure_incomplete",
        lambda: run_fixture_g6c(module),
    ),
    (
        "G6D",
        "relevant_authoritative_dependency_changed",
        lambda: run_fixture_g6d(module),
    ),   
    
    (
         "G6E",
         "authoritative_current_state_unavailable",
         lambda: run_fixture_g6e(module),
    ),
    (
         "G6F",
         "reuse_freshness_deadline_reached_or_exceeded",
         lambda: run_fixture_g6f(module),
    ),    
    (
         "G6G",
         "authority_derivation_replaced",
         lambda: run_fixture_g6g(module),
    ),    
    )
    failures = []

    for fixture_id, name, fixture in fixtures:
        try:
            fixture()
        except Exception as exc:
            failures.append((fixture_id, name, exc))
            print(
                f"FAIL: fixture_{fixture_id}_{name}: "
                f"{type(exc).__name__}: {exc}"
            )
        else:
            print(f"PASS: fixture_{fixture_id}_{name}")

    if failures:
        raise AssertionError(
            "PHAGE Applicable Evidence Reuse G6 regression RED: "
            f"{len(failures)} / {len(fixtures)} failing"
        )

    print(
        "PHAGE Applicable Evidence Reuse G6 regression harness PASS: "
        f"{len(fixtures)} / {len(fixtures)}"
    )
def _g6c_verified_facts():
    facts = _g6a_verified_facts()
    facts["dependency_closure_complete"] = False
    return facts


def run_fixture_g6c(module):
    evaluate_verified = getattr(
        module,
        "_evaluate_applicable_evidence_reuse_from_verified_facts",
        None,
    )

    assert callable(evaluate_verified), (
        "G6C contract RED: verified-facts reuse seam is not implemented"
    )

    result = evaluate_verified(
        verified_facts=_g6c_verified_facts(),
    )

    _assert_result_shape(result)

    assert result["reuse_status"] == REUSE_UNRESOLVED
    assert result["reason_code"] == "DEPENDENCY_CLOSURE_INCOMPLETE"
def _g6d_verified_facts():
    facts = _g6a_verified_facts()
    facts["all_relevant_dependencies_unchanged"] = False
    return facts


def run_fixture_g6d(module):
    evaluate_verified = getattr(
        module,
        "_evaluate_applicable_evidence_reuse_from_verified_facts",
        None,
    )

    assert callable(evaluate_verified), (
        "G6D contract RED: verified-facts reuse seam is not implemented"
    )

    result = evaluate_verified(
        verified_facts=_g6d_verified_facts(),
    )

    _assert_result_shape(result)

    assert result["reuse_status"] == REUSE_INVALIDATED
    assert result["reason_code"] == "RELEVANT_DEPENDENCY_CHANGED"
def _g6e_verified_facts():
    facts = _g6a_verified_facts()
    facts["authoritative_current_state_resolved"] = False
    return facts


def run_fixture_g6e(module):
    evaluate_verified = getattr(
        module,
        "_evaluate_applicable_evidence_reuse_from_verified_facts",
        None,
    )

    assert callable(evaluate_verified), (
        "G6E contract RED: verified-facts reuse seam is not implemented"
    )

    result = evaluate_verified(
        verified_facts=_g6e_verified_facts(),
    )

    _assert_result_shape(result)

    assert result["reuse_status"] == REUSE_UNRESOLVED
    assert result["reason_code"] == "AUTHORITATIVE_CURRENT_STATE_UNAVAILABLE"   
def _g6f_verified_facts():
    facts = _g6a_verified_facts()
    facts["trusted_current_time"] = AT + timedelta(minutes=5)
    return facts


def run_fixture_g6f(module):
    evaluate_verified = getattr(
        module,
        "_evaluate_applicable_evidence_reuse_from_verified_facts",
        None,
    )

    assert callable(evaluate_verified), (
        "G6F contract RED: verified-facts reuse seam is not implemented"
    )

    result = evaluate_verified(
        verified_facts=_g6f_verified_facts(),
    )

    _assert_result_shape(result)

    assert result["reuse_status"] == REUSE_INVALIDATED    
    assert result["reason_code"] == "FRESHNESS_DEADLINE_REACHED_OR_EXCEEDED"
def _g6g_verified_facts():
    facts = _g6a_verified_facts()
    facts["current_authority_derivation_id"] = "authority-path-B"
    return facts


def run_fixture_g6g(module):
    evaluate_verified = getattr(
        module,
        "_evaluate_applicable_evidence_reuse_from_verified_facts",
        None,
    )

    assert callable(evaluate_verified), (
        "G6G contract RED: verified-facts reuse seam is not implemented"
    )

    result = evaluate_verified(
        verified_facts=_g6g_verified_facts(),
    )

    _assert_result_shape(result)

    assert result["reuse_status"] == REUSE_INVALIDATED    
if __name__ == "__main__":
    run()
