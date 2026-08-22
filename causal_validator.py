"""
PHAGE Governance — Causal Attribution Validator v0.1

Purpose
=======
A downstream evaluator for CLEAN lineage. This module does not decide whether
evidence is historically admissible; lineage.py + gate.py already own that
boundary. Instead it checks whether a represented causal graph preserves the
strength and multiplicity of causal claims supported by the supplied case.

Core restraint:
- correlation != established causation
- counterevidence != established refutation
- unresolved causation != established non-causation
- multi-parent evidence != permission to select a sole cause

The validator is intentionally representation-oriented. It can flag:
1) CAUSAL_OVERLINK:
   A representation upgrades a weaker/unresolved edge to ESTABLISHED, or
   collapses multiple plausible parents into an unsupported sole cause.
2) CAUSAL_UNDERLINK:
   An ESTABLISHED edge supported by the case is omitted from the representation.
3) UNSUPPORTED_REFUTATION:
   A representation marks an edge NOT_ESTABLISHED where the case only supports
   UNRESOLVED / ATTRIBUTED / SUPPORTED status.

This module does not infer malicious intent and does not convert absence of
proof into proof of absence.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Iterable, Optional

from lineage import LineageCheckResult, LineageState


class EdgeStatus(str, Enum):
    ESTABLISHED = "ESTABLISHED"
    SUPPORTED = "SUPPORTED"
    ATTRIBUTED = "ATTRIBUTED"
    UNRESOLVED = "UNRESOLVED"
    NOT_ESTABLISHED = "NOT_ESTABLISHED"


class DiagnosticTaxonomy(str, Enum):
    CAUSAL_OVERLINK = "CAUSAL_OVERLINK"
    CAUSAL_UNDERLINK = "CAUSAL_UNDERLINK"
    UNSUPPORTED_REFUTATION = "UNSUPPORTED_REFUTATION"


class CausalEvaluationState(str, Enum):
    CLEAN = "CLEAN"
    UNRESOLVED = "UNRESOLVED"


@dataclass(frozen=True)
class CausalEdgeAssessment:
    parent: str
    child: str
    status: EdgeStatus
    support_refs: tuple[str, ...] = field(default_factory=tuple)
    counterevidence_refs: tuple[str, ...] = field(default_factory=tuple)
    detail: str = ""

    @property
    def key(self) -> tuple[str, str]:
        return (self.parent, self.child)


@dataclass(frozen=True)
class RepresentedEdge:
    parent: str
    child: str
    asserted_status: EdgeStatus
    sole_cause: bool = False

    @property
    def key(self) -> tuple[str, str]:
        return (self.parent, self.child)


@dataclass(frozen=True)
class CausalCase:
    case_id: str
    assessments: tuple[CausalEdgeAssessment, ...]
    representation: tuple[RepresentedEdge, ...]


@dataclass(frozen=True)
class CausalDiagnostic:
    taxonomy: DiagnosticTaxonomy
    parent: str
    child: str
    detail: str
    evidence_refs: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class CausalEvaluationResult:
    state: CausalEvaluationState
    case_id: str
    diagnostics: tuple[CausalDiagnostic, ...]
    preserved_edge_statuses: tuple[tuple[str, str, EdgeStatus], ...]


def _plausible_parent(status: EdgeStatus) -> bool:
    return status in {
        EdgeStatus.ESTABLISHED,
        EdgeStatus.SUPPORTED,
        EdgeStatus.ATTRIBUTED,
        EdgeStatus.UNRESOLVED,
    }


def _assessment_map(
    assessments: Iterable[CausalEdgeAssessment],
) -> dict[tuple[str, str], CausalEdgeAssessment]:
    out: dict[tuple[str, str], CausalEdgeAssessment] = {}
    for a in assessments:
        if a.key in out:
            raise ValueError(f"Duplicate causal assessment for edge {a.key!r}")
        out[a.key] = a
    return out


def validate_case(case: CausalCase) -> CausalEvaluationResult:
    assessments = _assessment_map(case.assessments)
    represented = {edge.key: edge for edge in case.representation}
    diagnostics: list[CausalDiagnostic] = []

    # A) Over-link / unsupported upgrade / unsupported refutation.
    for edge in case.representation:
        assessment = assessments.get(edge.key)

        if assessment is None:
            diagnostics.append(
                CausalDiagnostic(
                    taxonomy=DiagnosticTaxonomy.CAUSAL_OVERLINK,
                    parent=edge.parent,
                    child=edge.child,
                    detail=(
                        "Representation asserts a causal edge for which the case "
                        "contains no edge assessment."
                    ),
                )
            )
            continue

        if (
            edge.asserted_status is EdgeStatus.ESTABLISHED
            and assessment.status is not EdgeStatus.ESTABLISHED
        ):
            diagnostics.append(
                CausalDiagnostic(
                    taxonomy=DiagnosticTaxonomy.CAUSAL_OVERLINK,
                    parent=edge.parent,
                    child=edge.child,
                    detail=(
                        f"Representation upgrades {assessment.status.value} evidence "
                        "to ESTABLISHED causation."
                    ),
                    evidence_refs=assessment.support_refs + assessment.counterevidence_refs,
                )
            )

        if (
            edge.asserted_status is EdgeStatus.NOT_ESTABLISHED
            and assessment.status
            in {
                EdgeStatus.ESTABLISHED,
                EdgeStatus.SUPPORTED,
                EdgeStatus.ATTRIBUTED,
                EdgeStatus.UNRESOLVED,
            }
        ):
            diagnostics.append(
                CausalDiagnostic(
                    taxonomy=DiagnosticTaxonomy.UNSUPPORTED_REFUTATION,
                    parent=edge.parent,
                    child=edge.child,
                    detail=(
                        f"Representation converts {assessment.status.value} causation "
                        "into NOT_ESTABLISHED. Counterevidence or uncertainty does not "
                        "by itself establish refutation."
                    ),
                    evidence_refs=assessment.support_refs + assessment.counterevidence_refs,
                )
            )

        if edge.sole_cause:
            other_plausible = [
                a
                for a in case.assessments
                if a.child == edge.child
                and a.parent != edge.parent
                and _plausible_parent(a.status)
            ]
            if other_plausible:
                diagnostics.append(
                    CausalDiagnostic(
                        taxonomy=DiagnosticTaxonomy.CAUSAL_OVERLINK,
                        parent=edge.parent,
                        child=edge.child,
                        detail=(
                            "Representation marks this edge as a sole cause while "
                            "other plausible causal parents remain in the case: "
                            + ", ".join(
                                f"{a.parent}({a.status.value})" for a in other_plausible
                            )
                        ),
                        evidence_refs=tuple(
                            ref
                            for a in other_plausible
                            for ref in (a.support_refs + a.counterevidence_refs)
                        ),
                    )
                )

    # B) Under-link: an established relation disappears from the representation.
    for assessment in case.assessments:
        if (
            assessment.status is EdgeStatus.ESTABLISHED
            and assessment.key not in represented
        ):
            diagnostics.append(
                CausalDiagnostic(
                    taxonomy=DiagnosticTaxonomy.CAUSAL_UNDERLINK,
                    parent=assessment.parent,
                    child=assessment.child,
                    detail=(
                        "Case establishes this causal relation, but the representation "
                        "omits the edge."
                    ),
                    evidence_refs=assessment.support_refs,
                )
            )

    preserved = tuple(
        (a.parent, a.child, a.status)
        for a in case.assessments
    )

    return CausalEvaluationResult(
        state=(
            CausalEvaluationState.UNRESOLVED
            if diagnostics
            else CausalEvaluationState.CLEAN
        ),
        case_id=case.case_id,
        diagnostics=tuple(diagnostics),
        preserved_edge_statuses=preserved,
    )


class CausalEvaluator:
    """
    Adapter for gate.DownstreamEvaluator.

    The gate invokes evaluate() only after lineage is CLEAN. The gate deliberately
    ignores the evaluator's return value, so this adapter stores last_result for
    callers/tests that need the causal diagnostic output.
    """

    def __init__(self, case: CausalCase) -> None:
        self.case = case
        self.called = False
        self.last_evidence_id: Optional[str] = None
        self.last_result: Optional[CausalEvaluationResult] = None

    def evaluate(
        self,
        *,
        evidence_id: str,
        lineage_result: LineageCheckResult,
    ) -> CausalEvaluationResult:
        if lineage_result.state is not LineageState.CLEAN:
            raise RuntimeError(
                "CausalEvaluator must only run after CLEAN lineage."
            )

        self.called = True
        self.last_evidence_id = evidence_id
        self.last_result = validate_case(self.case)
        return self.last_result
