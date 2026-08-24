"""
DF-018 downstream evaluator adapter.

Purpose
-------
Provide a thin adapter between PHAGE governance gate.py and the
DF-018 validator logic.

Confirmed repository contract:
- gate.py only invokes a downstream evaluator after LineageState.CLEAN.
- downstream evaluator entry point is:

    evaluate(
        *,
        evidence_id: str,
        lineage_result: LineageCheckResult,
    ) -> object

- lineage.py does not resolve authority.
- DF-018 authority/classification conclusions therefore remain the
  responsibility of this downstream evaluator layer.

Important
---------
This module does NOT:
- modify gate semantics;
- treat CLEAN lineage as substantive PASS;
- resolve S5;
- convert CLAIM_1 or CLAIM_2 to SATISFIED;
- invent a PHAGE diagnostic taxonomy value;
- treat lineage open_dependencies as DF-018 evaluation dependencies.

The actual DF-018 core validator is injected into DF018Evaluator.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Iterable

from lineage import LineageCheckResult, LineageState


UNMAPPED_TAXONOMY = "UNMAPPED_PENDING_PHAGE_DIAGNOSTIC_TAXONOMY"


@dataclass(frozen=True)
class Diagnostic:
    """
    One DF-018 downstream diagnostic.

    failure_condition preserves the fixture-level DF-018 condition name.
    taxonomy remains deliberately unmapped until the repository's real
    diagnostic taxonomy is identified.

    evaluation_open_dependencies is intentionally distinct from
    LineageCheckResult.open_dependencies.
    """

    taxonomy: str
    claim_id: str
    failure_condition: str
    detail: str
    evidence_refs: tuple[str, ...] = field(default_factory=tuple)
    evaluation_open_dependencies: tuple[str, ...] = field(
        default_factory=tuple
    )
    triggered: bool = False


@dataclass(frozen=True)
class DF018EvaluationResult:
    """
    Result returned by the DF-018 downstream evaluator.

    This is NOT an AssessmentGateResult.
    The gate has already completed its responsibility before this object
    exists.
    """

    evidence_id: str
    lineage_state: LineageState
    diagnostics: tuple[Diagnostic, ...]

    @property
    def triggered_count(self) -> int:
        return sum(1 for item in self.diagnostics if item.triggered)

    @property
    def silent_count(self) -> int:
        return sum(1 for item in self.diagnostics if not item.triggered)

    @property
    def triggered_failure_conditions(self) -> tuple[str, ...]:
        return tuple(
            item.failure_condition
            for item in self.diagnostics
            if item.triggered
        )


CoreValidator = Callable[
    [str, LineageCheckResult],
    Iterable[Diagnostic],
]


class DF018Evaluator:
    """
    Thin adapter satisfying gate.py's downstream evaluator protocol.

    core_validator is injected rather than imported here so that this
    adapter does not guess:
    - the eventual validator module path;
    - fixture filename/location;
    - PHAGE diagnostic taxonomy;
    - repository-wide evaluator registry conventions.
    """

    def __init__(self, core_validator: CoreValidator) -> None:
        self._core_validator = core_validator

    def evaluate(
        self,
        *,
        evidence_id: str,
        lineage_result: LineageCheckResult,
    ) -> DF018EvaluationResult:
        """
        Evaluate DF-018 only after CLEAN lineage.

        gate.py is expected to enforce this boundary already.
        The explicit check below is defensive: direct callers must not
        accidentally bypass the governance gate.
        """

        if lineage_result.state is not LineageState.CLEAN:
            raise ValueError(
                "DF018Evaluator requires LineageState.CLEAN; "
                f"received {lineage_result.state.value!r} "
                f"for evidence_id={evidence_id!r}."
            )

        if lineage_result.evidence_id != evidence_id:
            raise ValueError(
                "evidence_id mismatch between gate invocation and "
                "LineageCheckResult: "
                f"{evidence_id!r} != "
                f"{lineage_result.evidence_id!r}."
            )

        diagnostics = tuple(
            self._core_validator(
                evidence_id,
                lineage_result,
            )
        )

        return DF018EvaluationResult(
            evidence_id=evidence_id,
            lineage_state=lineage_result.state,
            diagnostics=diagnostics,
        )
