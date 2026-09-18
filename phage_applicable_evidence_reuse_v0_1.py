"""
PHAGE Applicable Evidence Reuse v0.1.

Minimal G6A/G6B/G6C enforcement only.
"""

REUSE_ALLOWED = "REUSE_ALLOWED"


def evaluate_applicable_evidence_reuse(*args, **kwargs):
    raise NotImplementedError(
        "public applicable-evidence-reuse orchestration is not implemented"
    )


def _evaluate_applicable_evidence_reuse_from_verified_facts(
    *,
    verified_facts,
):
        original_bundle_id = verified_facts.get(
        "original_evidence_bundle_id"
    )

    candidate_bundle_id = verified_facts.get(
        "candidate_evidence_bundle_id"
    )

    if (
        original_bundle_id is not None
        and candidate_bundle_id is not None
        and original_bundle_id != candidate_bundle_id
    ):
        return {
            "reuse_status": "REUSE_INVALIDATED",
            "reason_code": "EVIDENCE_BUNDLE_SUBSTITUTION",
        }

    dependency_closure_complete = verified_facts.get(
        "dependency_closure_complete"
    )

    if dependency_closure_complete is False:
        return {
            "reuse_status": "REUSE_UNRESOLVED",
            "reason_code": "DEPENDENCY_CLOSURE_INCOMPLETE",
        }

    required_g6a_conditions = (
        verified_facts.get("prior_result") == "APPLICABLE",
        verified_facts.get("original_evidence_bundle_id")
        == verified_facts.get("candidate_evidence_bundle_id"),
        verified_facts.get("original_context")
        == verified_facts.get("current_context"),
        verified_facts.get("original_dependency_closure")
        == verified_facts.get("current_dependency_closure"),
        verified_facts.get("dependency_closure_complete") is True,
        verified_facts.get("original_authority_derivation_id")
        == verified_facts.get("current_authority_derivation_id"),
        verified_facts.get("origin_integrity_reverified") is True,
        verified_facts.get("authoritative_current_state_resolved") is True,
        verified_facts.get("all_relevant_dependencies_unchanged") is True,
    )

    original_observed_at = verified_facts.get("original_observed_at")
    original_evidence_valid_until = verified_facts.get(
        "original_evidence_valid_until"
    )
    trusted_current_time = verified_facts.get("trusted_current_time")
    max_evidence_reuse_window = verified_facts.get(
        "max_evidence_reuse_window"
    )

    temporal_inputs_present = all(
        value is not None
        for value in (
            original_observed_at,
            original_evidence_valid_until,
            trusted_current_time,
            max_evidence_reuse_window,
        )
    )

    if temporal_inputs_present:
        governed_reuse_deadline = (
            original_observed_at + max_evidence_reuse_window
        )
        effective_reuse_deadline = min(
            original_evidence_valid_until,
            governed_reuse_deadline,
        )
        freshness_holds = (
            trusted_current_time < effective_reuse_deadline
        )
    else:
        freshness_holds = False
    
    if all(required_g6a_conditions) and freshness_holds:
        return {
            "reuse_status": REUSE_ALLOWED,
            "reason_code": "ALL_REUSE_CONDITIONS_VERIFIED",
        }

    raise NotImplementedError(
        "non-G6A applicable-evidence-reuse classification "
        "is not implemented"
    )
