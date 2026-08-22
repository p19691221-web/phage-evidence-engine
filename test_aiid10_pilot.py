"""
test_aiid10_pilot.py — AIID-10 Pilot-01 case-shaped regression fixture.

This is NOT a factual adjudication of AIID #10 or any company/system.
It converts the reviewed case shape into a machine-readable governance probe.

Expected pilot verdict: B — REPRESENTATION GAP
Reason: the incident-level representation probe collapses a multi-parent,
mixed-strength causal structure into an ESTABLISHED sole technology cause.
"""

from __future__ import annotations

import json
from pathlib import Path

from causal_validator import (
    CausalCase,
    CausalEdgeAssessment,
    EdgeStatus,
    RepresentedEdge,
    DiagnosticTaxonomy,
    CausalEvaluationState,
    validate_case,
)

HERE = Path(__file__).resolve().parent
FIXTURE = HERE / "aiid10_pilot_fixture.json"


def load_case() -> tuple[dict, CausalCase]:
    raw = json.loads(FIXTURE.read_text(encoding="utf-8"))

    assessments = tuple(
        CausalEdgeAssessment(
            parent=item["parent"],
            child=item["child"],
            status=EdgeStatus(item["status"]),
            support_refs=tuple(item.get("support_refs", ())),
            counterevidence_refs=tuple(item.get("counterevidence_refs", ())),
        )
        for item in raw["assessments"]
    )

    representation = tuple(
        RepresentedEdge(
            parent=item["parent"],
            child=item["child"],
            asserted_status=EdgeStatus(item["asserted_status"]),
            sole_cause=bool(item.get("sole_cause", False)),
        )
        for item in raw["incident_level_representation_probe"]
    )

    return raw, CausalCase(
        case_id=raw["case_id"],
        assessments=assessments,
        representation=representation,
    )


def test_aiid10_pilot_yields_representation_gap():
    raw, case = load_case()
    result = validate_case(case)

    assert result.state is CausalEvaluationState.UNRESOLVED
    assert raw["verdict"] == "B_REPRESENTATION_GAP"

    diagnostics = {d.taxonomy for d in result.diagnostics}
    assert DiagnosticTaxonomy.CAUSAL_OVERLINK in diagnostics

    # Critical restraint: employee hardship can be established while
    # technology-specific causation remains only attributed.
    preserved = {
        (parent, child): status
        for parent, child, status in result.preserved_edge_statuses
    }
    assert preserved[("unstable_schedule", "employee_hardship")] is EdgeStatus.ESTABLISHED
    assert preserved[("workforce_software", "unstable_schedule")] is EdgeStatus.ATTRIBUTED
    assert preserved[("optimization_configuration", "unstable_schedule")] is EdgeStatus.UNRESOLVED
    assert preserved[("intentional_harm", "employee_hardship")] is EdgeStatus.NOT_ESTABLISHED

    print("PASS: AIID-10 Pilot-01 -> B_REPRESENTATION_GAP")
    for diagnostic in result.diagnostics:
        print(f"[{diagnostic.taxonomy.value}] {diagnostic.parent} -> {diagnostic.child}")
        print(f"  {diagnostic.detail}")

    print("NON-CLAIMS:")
    for item in raw["non_claims"]:
        print(f"  - {item}")

    return result


if __name__ == "__main__":
    test_aiid10_pilot_yields_representation_gap()
