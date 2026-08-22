"""
phage/governance/gate.py — Assessment Gate Reference Implementation v0.1

Wraps LineageChecker.check() into exactly three outcomes, using raise
for hard boundaries so evaluation_started=False is guaranteed by
control flow, not by caller discipline:

    GovernanceViolation (raised)     -> REJECTED,   evaluation_started=False
    LineageState.UNRESOLVED (returned) -> UNRESOLVED, evaluation_started=False
    LineageState.CLEAN (returned)      -> CLEAN,      evaluation_started=True

This module does not decide what a downstream evaluator does with a
CLEAN result -- it only decides whether the downstream evaluator is
PERMITTED to run at all. See lineage.py's Epistemic Constitution for
the underlying invariants this gate enforces.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Mapping, Optional, Protocol

from lineage import (
    Evidence,
    ResolvedAvailability,
    LineageChecker,
    LineageCheckResult,
    LineageState,
    LineagePolicy,
    OpenDependency,
    GovernanceViolation,
)


class GateState(str, Enum):
    REJECTED = "REJECTED"
    UNRESOLVED = "UNRESOLVED"
    CLEAN = "CLEAN"


@dataclass(frozen=True)
class AssessmentGateResult:
    state: GateState
    evaluation_started: bool
    evidence_id: str
    violation: Optional[GovernanceViolation] = None
    open_dependencies: tuple[OpenDependency, ...] = field(default_factory=tuple)
    visited_evidence_ids: tuple[str, ...] = field(default_factory=tuple)


class DownstreamEvaluator(Protocol):
    """
    Anything the gate hands control to after a CLEAN result. This module
    does not implement one -- it only defines the contract so the gate
    can be tested in isolation from whatever evaluator eventually runs
    (e.g. the G1/G2/G3 Gap engine from the DF-001~011 line of work).
    """

    def evaluate(self, *, evidence_id: str, lineage_result: LineageCheckResult) -> object:
        ...


def run_gate(
    *,
    evidence_id: str,
    epistemic_cutoff: datetime,
    evidence_store: Mapping[str, Evidence],
    availability_view: Mapping[str, ResolvedAvailability],
    checker: Optional[LineageChecker] = None,
    downstream_evaluator: Optional[DownstreamEvaluator] = None,
) -> AssessmentGateResult:
    """
    The single entry point. Exactly one of REJECTED / UNRESOLVED / CLEAN
    is returned. If CLEAN and a downstream_evaluator is supplied, it is
    invoked -- but its return value is NOT part of AssessmentGateResult;
    this gate's job ends at "evaluation may begin," not at what the
    evaluation concludes.
    """
    checker = checker or LineageChecker(policy=LineagePolicy())

    try:
        result = checker.check(
            evidence_id=evidence_id,
            epistemic_cutoff=epistemic_cutoff,
            evidence_store=evidence_store,
            availability_view=availability_view,
        )
    except GovernanceViolation as violation:
        # Hard boundary. Control flow guarantees evaluation_started=False --
        # there is no code path from here that reaches downstream_evaluator.
        return AssessmentGateResult(
            state=GateState.REJECTED,
            evaluation_started=False,
            evidence_id=evidence_id,
            violation=violation,
        )

    if result.state is LineageState.UNRESOLVED:
        return AssessmentGateResult(
            state=GateState.UNRESOLVED,
            evaluation_started=False,
            evidence_id=evidence_id,
            open_dependencies=result.open_dependencies,
            visited_evidence_ids=result.visited_evidence_ids,
        )

    # LineageState.CLEAN -- the only state permitted to reach the evaluator.
    if downstream_evaluator is not None:
        downstream_evaluator.evaluate(evidence_id=evidence_id, lineage_result=result)

    return AssessmentGateResult(
        state=GateState.CLEAN,
        evaluation_started=True,
        evidence_id=evidence_id,
        visited_evidence_ids=result.visited_evidence_ids,
    )
