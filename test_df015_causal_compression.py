"""
test_df015_causal_compression.py — DF-015 CAUSAL CHAIN COMPRESSION /
ATTRIBUTION RESTRAINT

fixture_basis: CASE_SHAPED_SYNTHETIC

The fixture borrows a governance STRUCTURE seen in the AIID #10 pilot review:
software, configuration/policy, managerial action, implementation, scheduling,
and employee outcomes can form a multi-parent socio-technical causal graph.

IMPORTANT NON-CLAIMS
====================
This fixture does NOT claim:
- AIID incident #10 is false;
- Kronos caused or did not cause any specific Starbucks employee harm;
- Starbucks or Kronos intentionally caused employee harm;
- the secondary reports reviewed are sufficient to establish technical
  causation.

The real-world review only motivates the SHAPE of the regression. DF-015 tests
general representation restraint.

A) OVER-LINK:
   weaker/multi-parent evidence is compressed into an ESTABLISHED sole cause.

B) UNDER-LINK:
   an ESTABLISHED relation is omitted even though the case supports it.

C) CONTROL:
   multiple plausible parents remain represented at their own evidence strength;
   no sole cause is invented and no counterevidence is treated as refutation.
"""

from datetime import datetime

from lineage import Evidence, ResolvedAvailability, AvailabilityStatus
from gate import run_gate, GateState
from causal_validator import (
    CausalCase,
    CausalEdgeAssessment,
    CausalEvaluator,
    CausalEvaluationState,
    DiagnosticTaxonomy,
    EdgeStatus,
    RepresentedEdge,
)


OBSERVED = datetime(2026, 1, 1)
CUTOFF = datetime(2026, 1, 2)


def resolved(evidence_id: str) -> ResolvedAvailability:
    return ResolvedAvailability(
        evidence_id=evidence_id,
        status=AvailabilityStatus.RESOLVED,
        resolved_available_at=OBSERVED,
        supporting_claim_refs=(f"availability-{evidence_id}",),
    )


def clean_gate_run(case: CausalCase):
    root = "AIID10-SYNTHETIC-ROOT"
    store = {
        root: Evidence(
            evidence_id=root,
            observed_at=OBSERVED,
            available_at=OBSERVED,
            derived_from=(),
            source_refs=("fixture:DF-015",),
        )
    }
    availability = {root: resolved(root)}
    evaluator = CausalEvaluator(case)

    gate_result = run_gate(
        evidence_id=root,
        epistemic_cutoff=CUTOFF,
        evidence_store=store,
        availability_view=availability,
        downstream_evaluator=evaluator,
    )

    assert gate_result.state is GateState.CLEAN
    assert gate_result.evaluation_started is True
    assert evaluator.called is True
    assert evaluator.last_result is not None
    return evaluator.last_result


def test_df015_a_overlink_flags_single_parent_causal_compression():
    case = CausalCase(
        case_id="DF-015-A",
        assessments=(
            CausalEdgeAssessment(
                "unstable_schedule",
                "employee_hardship",
                EdgeStatus.ESTABLISHED,
                support_refs=("NYT-2014", "CBS-2015"),
            ),
            CausalEdgeAssessment(
                "workforce_software",
                "unstable_schedule",
                EdgeStatus.ATTRIBUTED,
                support_refs=("TECHTARGET-2015",),
                counterevidence_refs=("KRONOS-RESPONSE",),
            ),
            CausalEdgeAssessment(
                "management_policy",
                "unstable_schedule",
                EdgeStatus.SUPPORTED,
                support_refs=("CNN-2015", "CBS-2014"),
            ),
            CausalEdgeAssessment(
                "store_implementation",
                "unstable_schedule",
                EdgeStatus.SUPPORTED,
                support_refs=("SEATTLE-TIMES-2016",),
            ),
        ),
        representation=(
            # Defect: weaker technology attribution is promoted to an
            # ESTABLISHED sole cause of unstable scheduling.
            RepresentedEdge(
                "workforce_software",
                "unstable_schedule",
                EdgeStatus.ESTABLISHED,
                sole_cause=True,
            ),
            RepresentedEdge(
                "unstable_schedule",
                "employee_hardship",
                EdgeStatus.ESTABLISHED,
            ),
        ),
    )

    result = clean_gate_run(case)

    assert result.state is CausalEvaluationState.UNRESOLVED
    taxonomies = [d.taxonomy for d in result.diagnostics]
    assert DiagnosticTaxonomy.CAUSAL_OVERLINK in taxonomies
    assert any("upgrades ATTRIBUTED evidence" in d.detail for d in result.diagnostics)
    assert any("sole cause" in d.detail for d in result.diagnostics)
    print("PASS: DF-015-A over-linking detected")
    return result


def test_df015_b_underlink_flags_missing_established_edge():
    case = CausalCase(
        case_id="DF-015-B",
        assessments=(
            CausalEdgeAssessment(
                "short_notice_schedule",
                "planning_constraint",
                EdgeStatus.ESTABLISHED,
                support_refs=("EMPLOYEE-TESTIMONY", "SURVEY-RESULT"),
            ),
            CausalEdgeAssessment(
                "planning_constraint",
                "employee_hardship",
                EdgeStatus.ESTABLISHED,
                support_refs=("EMPLOYEE-TESTIMONY",),
            ),
        ),
        representation=(
            # Defect: the first established relation is dropped, leaving the
            # evidence fragments disconnected.
            RepresentedEdge(
                "planning_constraint",
                "employee_hardship",
                EdgeStatus.ESTABLISHED,
            ),
        ),
    )

    result = clean_gate_run(case)

    assert result.state is CausalEvaluationState.UNRESOLVED
    assert any(
        d.taxonomy is DiagnosticTaxonomy.CAUSAL_UNDERLINK
        and d.parent == "short_notice_schedule"
        and d.child == "planning_constraint"
        for d in result.diagnostics
    )
    print("PASS: DF-015-B under-linking detected")
    return result


def test_df015_c_multi_parent_restraint_control_is_clean():
    case = CausalCase(
        case_id="DF-015-C",
        assessments=(
            CausalEdgeAssessment(
                "unstable_schedule",
                "employee_hardship",
                EdgeStatus.ESTABLISHED,
                support_refs=("NYT-2014", "CBS-2015"),
            ),
            CausalEdgeAssessment(
                "workforce_software",
                "unstable_schedule",
                EdgeStatus.ATTRIBUTED,
                support_refs=("TECHTARGET-2015",),
                counterevidence_refs=("KRONOS-RESPONSE",),
            ),
            CausalEdgeAssessment(
                "management_policy",
                "unstable_schedule",
                EdgeStatus.SUPPORTED,
                support_refs=("CNN-2015",),
            ),
            CausalEdgeAssessment(
                "store_implementation",
                "unstable_schedule",
                EdgeStatus.SUPPORTED,
                support_refs=("SEATTLE-TIMES-2016",),
            ),
        ),
        representation=(
            RepresentedEdge(
                "unstable_schedule",
                "employee_hardship",
                EdgeStatus.ESTABLISHED,
            ),
            RepresentedEdge(
                "workforce_software",
                "unstable_schedule",
                EdgeStatus.ATTRIBUTED,
            ),
            RepresentedEdge(
                "management_policy",
                "unstable_schedule",
                EdgeStatus.SUPPORTED,
            ),
            RepresentedEdge(
                "store_implementation",
                "unstable_schedule",
                EdgeStatus.SUPPORTED,
            ),
        ),
    )

    result = clean_gate_run(case)

    assert result.state is CausalEvaluationState.CLEAN
    assert result.diagnostics == ()

    preserved = {
        (parent, child): status
        for parent, child, status in result.preserved_edge_statuses
    }
    assert preserved[("workforce_software", "unstable_schedule")] is EdgeStatus.ATTRIBUTED
    assert preserved[("management_policy", "unstable_schedule")] is EdgeStatus.SUPPORTED
    assert preserved[("store_implementation", "unstable_schedule")] is EdgeStatus.SUPPORTED
    assert preserved[("unstable_schedule", "employee_hardship")] is EdgeStatus.ESTABLISHED

    print("PASS: DF-015-C multi-parent restraint preserved")
    return result


if __name__ == "__main__":
    tests = [
        test_df015_a_overlink_flags_single_parent_causal_compression,
        test_df015_b_underlink_flags_missing_established_edge,
        test_df015_c_multi_parent_restraint_control_is_clean,
    ]

    results = {}
    failures = 0

    for test in tests:
        try:
            results[test.__name__] = test()
        except AssertionError as exc:
            failures += 1
            print(f"FAIL: {test.__name__} -- {exc}")

    print()
    if failures:
        print(f"{failures}/{len(tests)} DF-015 tests FAILED")
    else:
        print(f"{len(tests)}/{len(tests)} DF-015 tests PASSED")

    print()
    print("=== DF-015 actual diagnostics ===")
    for name, result in results.items():
        print(f"\n{name}: {result.state.value}")
        if not result.diagnostics:
            print("  diagnostics: none")
        for diagnostic in result.diagnostics:
            print(f"  [{diagnostic.taxonomy.value}]")
            print(f"    edge: {diagnostic.parent} -> {diagnostic.child}")
            print(f"    {diagnostic.detail}")
            if diagnostic.evidence_refs:
                print(f"    refs: {', '.join(diagnostic.evidence_refs)}")

    print()
    print("=== Explicit non-claims ===")
    print("DF-015 does NOT claim AIID #10 is false.")
    print("DF-015 does NOT establish or refute Kronos-specific causation.")
    print("DF-015 tests only the general representation shape:")
    print("over-linking, under-linking, and multi-parent causal restraint.")
