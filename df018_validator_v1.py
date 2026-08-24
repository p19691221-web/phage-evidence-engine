#!/usr/bin/env python3
"""
DF-018 validator v1.

Reads:
    DF018_UBER_BEITOU_FIXTURE.json

Produces:
    Diagnostic objects defined by df018_evaluator.py.

Scope
-----
This validator tests four governance leakage conditions:

1. CURRENT_LAW_LEAKAGE
2. SECTION_IDENTITY_COLLISION
3. ENTITY_IDENTITY_COLLISION
4. AUTHORITY_CHAIN_PREMATURE_CLOSURE

Each condition has:
- one deliberately invalid leakage case that MUST trigger;
- one control case that MUST remain silent.

This module does not determine the final legality of DF-018 and does not
close CLAIM_1 while S5 remains open.
"""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any, Iterable

from df018_evaluator import Diagnostic, UNMAPPED_TAXONOMY
from lineage import LineageCheckResult


FIXTURE_FILE = "DF018_UBER_BEITOU_FIXTURE.json"

CLAIM_1 = "CLAIM_1_CLASSIFICATION_AUTHORITY"

FAILURE_CONDITIONS = (
    "CURRENT_LAW_LEAKAGE",
    "SECTION_IDENTITY_COLLISION",
    "ENTITY_IDENTITY_COLLISION",
    "AUTHORITY_CHAIN_PREMATURE_CLOSURE",
)


def load_fixture(path: Path | None = None) -> dict[str, Any]:
    fixture_path = path or Path(__file__).resolve().parent / FIXTURE_FILE

    with fixture_path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)

    if not isinstance(value, dict):
        raise ValueError("DF-018 fixture root must be a JSON object.")

    return value


def make_diagnostic(
    *,
    failure_condition: str,
    triggered: bool,
    detail: str,
    evidence_refs: tuple[str, ...] = (),
    evaluation_open_dependencies: tuple[str, ...] = (),
) -> Diagnostic:
    return Diagnostic(
        taxonomy=UNMAPPED_TAXONOMY,
        claim_id=CLAIM_1,
        failure_condition=failure_condition,
        detail=detail,
        evidence_refs=evidence_refs,
        evaluation_open_dependencies=evaluation_open_dependencies,
        triggered=triggered,
    )


def current_law_leakage(
    fixture: dict[str, Any],
    *,
    use_unverified_current_text: bool,
) -> Diagnostic:
    node = fixture["evidence_nodes"]["PROMULGATION_2026_08_17"]

    triggered = (
        use_unverified_current_text
        and node["status"] == "REVALIDATION_REQUIRED"
    )

    detail = (
        "Unverified or temporally unestablished statutory text was used "
        "as governing law."
        if triggered
        else
        "Temporal applicability remains explicit; unverified current "
        "text was not silently imported."
    )

    return make_diagnostic(
        failure_condition="CURRENT_LAW_LEAKAGE",
        triggered=triggered,
        detail=detail,
        evidence_refs=("PROMULGATION_2026_08_17",),
        evaluation_open_dependencies=(
            "PROMULGATION_2026_08_17_PRIMARY_REVALIDATION",
        ),
    )


def section_identity_collision(
    fixture: dict[str, Any],
    *,
    collapse_versions: bool,
) -> Diagnostic:
    version_sensitive_nodes = (
        "STATUTORY_TRANSPORT_CLASSIFICATION",
        "COMPETENT_AUTHORITY_ASSIGNMENT",
        "ENFORCEMENT_AUTHORITY_ASSIGNMENT",
    )

    requires_revalidation = any(
        fixture["evidence_nodes"][node_id]["status"]
        == "FOUND_VERSION_REVALIDATION_REQUIRED"
        for node_id in version_sensitive_nodes
    )

    triggered = collapse_versions and requires_revalidation

    detail = (
        "Section identity was collapsed across statutory versions while "
        "version revalidation remains required."
        if triggered
        else
        "Section identity remains version-sensitive; unresolved versions "
        "were not treated as legally identical."
    )

    return make_diagnostic(
        failure_condition="SECTION_IDENTITY_COLLISION",
        triggered=triggered,
        detail=detail,
        evidence_refs=version_sensitive_nodes,
        evaluation_open_dependencies=(
            "APPLICABLE_STATUTORY_VERSION_AS_NEEDED",
        ),
    )


def entity_identity_collision(
    fixture: dict[str, Any],
    *,
    collapse_entities: bool,
) -> Diagnostic:
    entity_node = fixture["entity_distinction"]

    distinct_required = bool(entity_node["distinct_entity_flag"])
    triggered = collapse_entities and distinct_required

    entity_refs = tuple(
        f'{item["name"]}:{item["company_id"]}'
        for item in entity_node["entities"]
    )

    detail = (
        "Distinct legal entities were collapsed into one actor."
        if triggered
        else
        "The two legal entities remain separately identified by name "
        "and company ID."
    )

    return make_diagnostic(
        failure_condition="ENTITY_IDENTITY_COLLISION",
        triggered=triggered,
        detail=detail,
        evidence_refs=entity_refs,
    )


def authority_chain_premature_closure(
    fixture: dict[str, Any],
    *,
    force_claim_1_satisfied: bool,
) -> Diagnostic:
    claim = fixture["claims"][CLAIM_1]
    s5 = fixture["evidence_nodes"]["S5_PRIMARY_DISPOSITION"]

    s5_open = (
        s5["status"] == "OPEN"
        or not s5["regulated_category_established"]
        or not s5["primary_document_obtained"]
    )

    triggered = force_claim_1_satisfied and s5_open

    detail = (
        "CLAIM_1 resolved SATISFIED while regulated_category or the "
        "primary disposition remains unestablished. Other verified "
        "nodes cannot replace the missing case-specific edge."
        if triggered
        else
        "CLAIM_1 remains "
        f'{claim["status"]}/{claim["result"]} while S5 remains open.'
    )

    return make_diagnostic(
        failure_condition="AUTHORITY_CHAIN_PREMATURE_CLOSURE",
        triggered=triggered,
        detail=detail,
        evidence_refs=(
            "SELECTION_AUTHORITY_RULE",
            "S5_PRIMARY_DISPOSITION",
        ),
        evaluation_open_dependencies=tuple(claim["open_dependencies"]),
    )


def run_regression_cases(
    fixture: dict[str, Any],
) -> tuple[Diagnostic, ...]:
    """
    Return eight diagnostics:

    4 leakage attempts -- all must trigger.
    4 control cases    -- all must remain silent.
    """

    leakage_fixture = deepcopy(fixture)
    control_fixture = deepcopy(fixture)

    return (
        current_law_leakage(
            leakage_fixture,
            use_unverified_current_text=True,
        ),
        current_law_leakage(
            control_fixture,
            use_unverified_current_text=False,
        ),
        section_identity_collision(
            leakage_fixture,
            collapse_versions=True,
        ),
        section_identity_collision(
            control_fixture,
            collapse_versions=False,
        ),
        entity_identity_collision(
            leakage_fixture,
            collapse_entities=True,
        ),
        entity_identity_collision(
            control_fixture,
            collapse_entities=False,
        ),
        authority_chain_premature_closure(
            leakage_fixture,
            force_claim_1_satisfied=True,
        ),
        authority_chain_premature_closure(
            control_fixture,
            force_claim_1_satisfied=False,
        ),
    )


def validate_regression_shape(

    fixture: dict[str, Any],
    diagnostics: tuple[Diagnostic, ...],
) -> None:
    expectation = fixture["regression_expectation"]

    if len(diagnostics) != 8:
        raise AssertionError(
            "DF-018 regression failure: expected exactly 8 diagnostics "
            "(4 leakage cases + 4 control cases), "
            f"observed {len(diagnostics)}."
        )

    # run_regression_cases() deliberately returns:
    # leakage, control, leakage, control, ...
    leakage_cases = diagnostics[0::2]
    control_cases = diagnostics[1::2]

    expected_triggered = expectation[
        "leakage_cases_expected_triggered"
    ]
    expected_control_triggered = expectation[
        "control_cases_expected_triggered"
    ]

    triggered_leakage = tuple(
        item for item in leakage_cases if item.triggered
    )
    triggered_controls = tuple(
        item for item in control_cases if item.triggered
    )

    if len(triggered_leakage) != expected_triggered:
        raise AssertionError(
            "DF-018 regression failure: expected "
            f"{expected_triggered} triggered leakage cases, "
            f"observed {len(triggered_leakage)}."
        )

    if len(triggered_controls) != expected_control_triggered:
        raise AssertionError(
            "DF-018 regression failure: expected "
            f"{expected_control_triggered} triggered control cases, "
            f"observed {len(triggered_controls)}."
        )

    if expectation["require_both_sides"]:
        silent_controls = tuple(
            item for item in control_cases if not item.triggered
        )

        if len(silent_controls) != 4:
            raise AssertionError(
                "DF-018 regression failure: all four control cases "
                "must remain silent."
            )

    leakage_conditions = {
        item.failure_condition for item in leakage_cases
    }
    control_conditions = {
        item.failure_condition for item in control_cases
    }
    expected_conditions = set(FAILURE_CONDITIONS)

    if leakage_conditions != expected_conditions:
        raise AssertionError(
            "DF-018 regression failure: leakage cases do not cover "
            "the four locked failure conditions exactly once."
        )

    if control_conditions != expected_conditions:
        raise AssertionError(
            "DF-018 regression failure: control cases do not cover "
            "the four locked failure conditions exactly once."
        )


def validate_df018(
    evidence_id: str,
    lineage_result: LineageCheckResult,
) -> Iterable[Diagnostic]:
    """
    Core-validator entry point for DF018Evaluator.

    The current substantive fixture remains unresolved by design.
    Therefore this function reports the control-side diagnostics rather
    than manufacturing leakage attempts during normal evaluation.
    """

    del evidence_id
    del lineage_result

    fixture = load_fixture()

    return (
        current_law_leakage(
            fixture,
            use_unverified_current_text=False,
        ),
        section_identity_collision(
            fixture,
            collapse_versions=False,
        ),
        entity_identity_collision(
            fixture,
            collapse_entities=False,
        ),
        authority_chain_premature_closure(
            fixture,
            force_claim_1_satisfied=False,
        ),
    )


def main() -> int:
    fixture = load_fixture()
    diagnostics = run_regression_cases(fixture)

    validate_regression_shape(fixture, diagnostics)

    for item in diagnostics:
        state = "TRIGGERED" if item.triggered else "SILENT"
        print(
            f"{state}: "
            f"{item.failure_condition}: "
            f"{item.detail}"
        )

    print("DF-018 regression PASS: 4 triggered / 4 silent.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
