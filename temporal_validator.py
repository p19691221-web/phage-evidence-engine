"""

Current PHAGE Temporal Validator.

Adopted from temporal_validator_RECOVERED.py after controlled recovery
and fresh DF-014 regression.

This adoption does not assert recovery of the original unlocated
temporal_validator.py.

Recovery provenance:
RECOVERY_PROVENANCE_temporal_validator.md
RECOVERED IMPLEMENTATION — temporal_validator

Original temporal_validator.py was not located in the recovered artifact set.
This module is reconstructed only from surviving original artifacts:
- lineage.py
- phage_validate_temporal_fixture.py
- test_df014_windrelay.py

No historical PASS result is inherited. Any support must come from fresh execution.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Mapping, Sequence

from lineage import (
    Evidence,
    ResolvedAvailability,
    LineageChecker,
    LineageState,
    GovernanceViolation,
)


class TemporalGateState(str, Enum):
    CLEAN = "CLEAN"
    UNRESOLVED = "UNRESOLVED"
    REJECTED = "REJECTED"


class DiagnosticTaxonomy(str, Enum):
    STATE_TRANSITION_UNRESOLVED = "STATE_TRANSITION_UNRESOLVED"
    INTENT_INFERENCE_UNRESOLVED = "INTENT_INFERENCE_UNRESOLVED"
    EVIDENCE_INSUFFICIENT_FOR_STATE = "EVIDENCE_INSUFFICIENT_FOR_STATE"


class InferenceTargetType(str, Enum):
    STATE = "STATE"
    INTENT = "INTENT"


class ConfidenceSource(str, Enum):
    CONTEMPORANEOUS = "CONTEMPORANEOUS"
    HINDSIGHT = "HINDSIGHT"


@dataclass(frozen=True)
class Inference:
    inference_id: str
    target_type: InferenceTargetType
    target_time: datetime
    claim: str
    confidence_source: ConfidenceSource
    crosses_narrowing_boundary: bool = False
    evidence_refs: tuple[str, ...] = ()


@dataclass(frozen=True)
class TemporalDiagnostic:
    inference_id: str
    taxonomy: DiagnosticTaxonomy
    detail: str


@dataclass(frozen=True)
class TemporalValidationResult:
    state: TemporalGateState
    evaluation_started: bool
    diagnostics: tuple[TemporalDiagnostic, ...] = ()
    violation: GovernanceViolation | None = None
    open_dependencies: tuple = ()


def validate(
    *,
    evidence_id: str,
    epistemic_cutoff: datetime,
    evidence_store: Mapping[str, Evidence],
    availability_view: Mapping[str, ResolvedAvailability],
    inferences: Sequence[Inference],
) -> TemporalValidationResult:
    """Recovered temporal evaluation contract.

    1. Lineage gate runs first.
    2. GovernanceViolation -> REJECTED, evaluation_started=False.
    3. Lineage UNRESOLVED -> UNRESOLVED, evaluation_started=False.
    4. CLEAN lineage permits temporal diagnostics.
    5. Any temporal diagnostic -> UNRESOLVED, evaluation_started=False.
    6. No diagnostics -> CLEAN, evaluation_started=True.
    """
    checker = LineageChecker()
    try:
        lineage = checker.check(
            evidence_id=evidence_id,
            epistemic_cutoff=epistemic_cutoff,
            evidence_store=evidence_store,
            availability_view=availability_view,
        )
    except GovernanceViolation as violation:
        return TemporalValidationResult(
            state=TemporalGateState.REJECTED,
            evaluation_started=False,
            violation=violation,
        )

    if lineage.state is LineageState.UNRESOLVED:
        return TemporalValidationResult(
            state=TemporalGateState.UNRESOLVED,
            evaluation_started=False,
            open_dependencies=lineage.open_dependencies,
        )

    diagnostics: list[TemporalDiagnostic] = []

    for inference in inferences:
        # Recovered from DF-014 executable specification:
        # a state attribution crossing a later classification/decision-space
        # boundary must not silently become CLEAN.
        if (
            inference.target_type is InferenceTargetType.STATE
            and inference.crosses_narrowing_boundary
        ):
            diagnostics.append(
                TemporalDiagnostic(
                    inference_id=inference.inference_id,
                    taxonomy=DiagnosticTaxonomy.STATE_TRANSITION_UNRESOLVED,
                    detail=(
                        "State claim crosses a later narrowing/classification boundary; "
                        "the earlier state is not promoted without contemporaneous support."
                    ),
                )
            )

        # Recovered from early temporal CLI + DF-014 executable specification:
        # hindsight confidence used for an intent claim is unresolved.
        if (
            inference.target_type is InferenceTargetType.INTENT
            and inference.confidence_source is ConfidenceSource.HINDSIGHT
        ):
            diagnostics.append(
                TemporalDiagnostic(
                    inference_id=inference.inference_id,
                    taxonomy=DiagnosticTaxonomy.INTENT_INFERENCE_UNRESOLVED,
                    detail=(
                        "Intent claim is supported by hindsight rather than a "
                        "contemporaneous artifact."
                    ),
                )
            )

    if diagnostics:
        return TemporalValidationResult(
            state=TemporalGateState.UNRESOLVED,
            evaluation_started=False,
            diagnostics=tuple(diagnostics),
        )

    return TemporalValidationResult(
        state=TemporalGateState.CLEAN,
        evaluation_started=True,
        diagnostics=(),
    )
