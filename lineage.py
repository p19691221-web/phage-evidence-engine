"""
PHAGE Governance Lineage — Reference Implementation v0.1

Epistemic Constitution
======================

This module preserves a strict distinction between:

1. GovernanceViolation
   The supplied evidence/lineage is invalid for the requested epistemic
   context. Evaluation MUST NOT continue. The caller should represent
   this as REJECTED with evaluation_started=False.

2. OpenDependency
   The input is structurally valid, but required knowledge is missing
   or unresolved. This is NOT a rejection. The caller should represent
   this as UNRESOLVED with evaluation_started=False.

3. LineageCheckResult(CLEAN)
   The supplied lineage is structurally traversable and its resolved
   availability is within the requested epistemic cutoff. Only then may
   a downstream evaluator begin.

Core invariants:
- Historical Evidence is immutable.
- observed_at != available_at.
- Availability claims do not destructively mutate Evidence.
- Missing lineage never implies clean lineage.
- Boundary violations do not imply malicious intent.
- LineageChecker does not resolve authority or choose among conflicting
  availability claims.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Mapping, Optional


# ---------------------------------------------------------------------------
# Hard violations: evaluation must not continue.
# ---------------------------------------------------------------------------

class GovernanceViolation(Exception):
    """Base class for hard governance-boundary violations."""


class EpistemicBoundaryViolation(GovernanceViolation):
    def __init__(
        self,
        evidence_id: str,
        available_at: datetime,
        cutoff: datetime,
    ) -> None:
        self.evidence_id = evidence_id
        self.available_at = available_at
        self.cutoff = cutoff
        super().__init__(
            f"Evidence '{evidence_id}' became available at "
            f"{available_at.isoformat()}, after cutoff {cutoff.isoformat()}."
        )


class DerivationBoundaryViolation(GovernanceViolation):
    def __init__(
        self,
        evidence_id: str,
        offending_ancestor_id: str,
        ancestor_available_at: datetime,
        cutoff: datetime,
    ) -> None:
        self.evidence_id = evidence_id
        self.offending_ancestor_id = offending_ancestor_id
        self.ancestor_available_at = ancestor_available_at
        self.cutoff = cutoff
        super().__init__(
            f"Evidence '{evidence_id}' depends on ancestor "
            f"'{offending_ancestor_id}' available at "
            f"{ancestor_available_at.isoformat()}, after cutoff "
            f"{cutoff.isoformat()}."
        )


class LineageCycleDetected(GovernanceViolation):
    def __init__(self, cycle_path: tuple[str, ...]) -> None:
        self.cycle_path = cycle_path
        super().__init__(
            "Cycle detected in supplied evidence lineage: "
            + " -> ".join(cycle_path)
        )


class LineageMaxDepthExceeded(GovernanceViolation):
    def __init__(self, evidence_id: str, max_depth: int) -> None:
        self.evidence_id = evidence_id
        self.max_depth = max_depth
        super().__init__(
            f"Lineage for '{evidence_id}' exceeds max_depth={max_depth}."
        )


# ---------------------------------------------------------------------------
# Open dependencies: valid input, insufficient knowledge.
# ---------------------------------------------------------------------------

class DependencyType(str, Enum):
    LINEAGE_UNRESOLVED = "LINEAGE_UNRESOLVED"
    AVAILABILITY_UNRESOLVED = "AVAILABILITY_UNRESOLVED"


@dataclass(frozen=True)
class OpenDependency:
    dependency_type: DependencyType
    evidence_id: str
    detail: str
    evidence_refs: tuple[str, ...] = field(default_factory=tuple)


def lineage_unresolved(
    evidence_id: str,
    missing_ancestor_id: str,
) -> OpenDependency:
    return OpenDependency(
        dependency_type=DependencyType.LINEAGE_UNRESOLVED,
        evidence_id=evidence_id,
        detail=(
            f"Referenced ancestor '{missing_ancestor_id}' is not available "
            "in the supplied evidence store."
        ),
        evidence_refs=(missing_ancestor_id,),
    )


def availability_unresolved(
    evidence_id: str,
    conflicting_claim_refs: tuple[str, ...] = (),
) -> OpenDependency:
    return OpenDependency(
        dependency_type=DependencyType.AVAILABILITY_UNRESOLVED,
        evidence_id=evidence_id,
        detail="Availability could not be resolved from supplied claims.",
        evidence_refs=conflicting_claim_refs,
    )


# ---------------------------------------------------------------------------
# Immutable evidence and separately sourced availability assertions.
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Evidence:
    evidence_id: str
    observed_at: datetime
    available_at: datetime
    derived_from: tuple[str, ...] = field(default_factory=tuple)
    source_refs: tuple[str, ...] = field(default_factory=tuple)


class AvailabilityClaimStatus(str, Enum):
    SUPPORTED = "SUPPORTED"
    UNRESOLVED = "UNRESOLVED"
    CONFLICTING = "CONFLICTING"


@dataclass(frozen=True)
class AvailabilityClaim:
    claim_id: str
    evidence_id: str
    claimed_available_at: datetime
    authority_source_refs: tuple[str, ...]
    status: AvailabilityClaimStatus


class AvailabilityStatus(str, Enum):
    RESOLVED = "RESOLVED"
    UNRESOLVED = "UNRESOLVED"


@dataclass(frozen=True)
class ResolvedAvailability:
    evidence_id: str
    status: AvailabilityStatus
    resolved_available_at: Optional[datetime]
    supporting_claim_refs: tuple[str, ...] = field(default_factory=tuple)
    conflicting_claim_refs: tuple[str, ...] = field(default_factory=tuple)


# ---------------------------------------------------------------------------
# Lineage result.
# ---------------------------------------------------------------------------

class LineageState(str, Enum):
    CLEAN = "CLEAN"
    UNRESOLVED = "UNRESOLVED"


@dataclass(frozen=True)
class LineageCheckResult:
    state: LineageState
    evidence_id: str
    visited_evidence_ids: tuple[str, ...]
    open_dependencies: tuple[OpenDependency, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class LineagePolicy:
    max_depth: int = 64


# ---------------------------------------------------------------------------
# Single lineage implementation.
# ---------------------------------------------------------------------------

class LineageChecker:
    """
    Traverse a flat Evidence-ID graph.

    This checker:
    - consumes an already-resolved availability view;
    - does not resolve authority;
    - does not choose between conflicting availability claims;
    - does not infer malicious intent;
    - never treats missing ancestors as clean lineage.
    """

    def __init__(self, policy: Optional[LineagePolicy] = None) -> None:
        self.policy = policy or LineagePolicy()

    def check(
        self,
        *,
        evidence_id: str,
        epistemic_cutoff: datetime,
        evidence_store: Mapping[str, Evidence],
        availability_view: Mapping[str, ResolvedAvailability],
    ) -> LineageCheckResult:

        visited: set[str] = set()
        active_stack: list[str] = []
        dependencies: list[OpenDependency] = []

        def resolved_time(
            current_id: str,
            *,
            root: bool,
        ) -> Optional[datetime]:
            evidence = evidence_store.get(current_id)
            if evidence is None:
                return None

            resolved = availability_view.get(current_id)

            # No resolver entry means we cannot silently substitute raw time.
            if resolved is None:
                dependencies.append(
                    availability_unresolved(current_id)
                )
                return None

            if (
                resolved.status == AvailabilityStatus.UNRESOLVED
                or resolved.resolved_available_at is None
            ):
                dependencies.append(
                    availability_unresolved(
                        current_id,
                        resolved.conflicting_claim_refs,
                    )
                )
                return None

            available_at = resolved.resolved_available_at

            if available_at > epistemic_cutoff:
                if root:
                    raise EpistemicBoundaryViolation(
                        current_id,
                        available_at,
                        epistemic_cutoff,
                    )
                raise DerivationBoundaryViolation(
                    evidence_id,
                    current_id,
                    available_at,
                    epistemic_cutoff,
                )

            return available_at

        def dfs(current_id: str, depth: int) -> None:
            if depth > self.policy.max_depth:
                raise LineageMaxDepthExceeded(
                    evidence_id=evidence_id,
                    max_depth=self.policy.max_depth,
                )

            if current_id in active_stack:
                start = active_stack.index(current_id)
                cycle = tuple(active_stack[start:] + [current_id])
                raise LineageCycleDetected(cycle)

            if current_id in visited:
                return

            evidence = evidence_store.get(current_id)
            if evidence is None:
                dependencies.append(
                    lineage_unresolved(evidence_id, current_id)
                )
                return

            active_stack.append(current_id)

            # Boundary is governed by resolved availability, not observed_at.
            resolved_time(current_id, root=(current_id == evidence_id))

            for parent_id in evidence.derived_from:
                dfs(parent_id, depth + 1)

            active_stack.pop()
            visited.add(current_id)

        dfs(evidence_id, 0)

        if dependencies:
            # Deduplicate while preserving first occurrence.
            unique: list[OpenDependency] = []
            seen: set[tuple[DependencyType, str, tuple[str, ...]]] = set()
            for dep in dependencies:
                key = (
                    dep.dependency_type,
                    dep.evidence_id,
                    dep.evidence_refs,
                )
                if key not in seen:
                    seen.add(key)
                    unique.append(dep)

            return LineageCheckResult(
                state=LineageState.UNRESOLVED,
                evidence_id=evidence_id,
                visited_evidence_ids=tuple(sorted(visited)),
                open_dependencies=tuple(unique),
            )

        return LineageCheckResult(
            state=LineageState.CLEAN,
            evidence_id=evidence_id,
            visited_evidence_ids=tuple(sorted(visited)),
            open_dependencies=(),
        )
