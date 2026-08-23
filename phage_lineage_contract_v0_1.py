from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Mapping


class LineageStatus(str, Enum):
    CLEAN = "CLEAN"
    EPISTEMIC_BOUNDARY_VIOLATION = "EPISTEMIC_BOUNDARY_VIOLATION"
    DERIVATION_BOUNDARY_VIOLATION = "DERIVATION_BOUNDARY_VIOLATION"
    LINEAGE_UNRESOLVED = "LINEAGE_UNRESOLVED"
    LINEAGE_CYCLE_DETECTED = "LINEAGE_CYCLE_DETECTED"
    LINEAGE_MAX_DEPTH_EXCEEDED = "LINEAGE_MAX_DEPTH_EXCEEDED"


@dataclass(frozen=True)
class Evidence:
    evidence_id: str
    observed_at: datetime
    available_at: datetime
    derived_from: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class LineageResult:
    status: LineageStatus
    evidence_id: str
    offending_ref: str | None = None
    detail: str = ""


@dataclass(frozen=True)
class LineagePolicy:
    max_depth: int = 64


class LineageChecker:
    """
    PHAGE Lineage Contract v0.1 reference implementation.

    Boundary semantics:
      - available_at controls epistemic admissibility at cutoff.
      - observed_at is semantic metadata only.
      - missing ancestors never imply clean lineage.
      - descendant-looking-clean can still fail if any ancestor is post-cutoff.
    """

    def __init__(
        self,
        evidence_store: Mapping[str, Evidence],
        policy: LineagePolicy | None = None,
    ) -> None:
        self._store = dict(evidence_store)
        self._policy = policy or LineagePolicy()

    def check(self, evidence_id: str, cutoff: datetime) -> LineageResult:
        if evidence_id not in self._store:
            return LineageResult(
                status=LineageStatus.LINEAGE_UNRESOLVED,
                evidence_id=evidence_id,
                offending_ref=evidence_id,
                detail="Root evidence is missing from the supplied evidence store.",
            )

        root = self._store[evidence_id]

        # Root/direct boundary violation gets its own class.
        if root.available_at > cutoff:
            return LineageResult(
                status=LineageStatus.EPISTEMIC_BOUNDARY_VIOLATION,
                evidence_id=evidence_id,
                offending_ref=evidence_id,
                detail=(
                    f"Direct evidence available_at={root.available_at.isoformat()} "
                    f"exceeds cutoff={cutoff.isoformat()}."
                ),
            )

        visited: set[str] = set()
        active_path: set[str] = set()

        def dfs(current_id: str, depth: int) -> LineageResult | None:
            if depth > self._policy.max_depth:
                return LineageResult(
                    status=LineageStatus.LINEAGE_MAX_DEPTH_EXCEEDED,
                    evidence_id=evidence_id,
                    offending_ref=current_id,
                    detail=f"Lineage traversal exceeded max_depth={self._policy.max_depth}.",
                )

            if current_id in active_path:
                return LineageResult(
                    status=LineageStatus.LINEAGE_CYCLE_DETECTED,
                    evidence_id=evidence_id,
                    offending_ref=current_id,
                    detail="Cycle detected in derived_from lineage.",
                )

            if current_id in visited:
                return None

            current = self._store.get(current_id)
            if current is None:
                return LineageResult(
                    status=LineageStatus.LINEAGE_UNRESOLVED,
                    evidence_id=evidence_id,
                    offending_ref=current_id,
                    detail="Referenced ancestor is missing from the supplied evidence store.",
                )

            active_path.add(current_id)

            # Root direct cutoff was checked above. Any post-cutoff ancestor
            # contaminates derivation lineage.
            if current_id != evidence_id and current.available_at > cutoff:
                active_path.remove(current_id)
                return LineageResult(
                    status=LineageStatus.DERIVATION_BOUNDARY_VIOLATION,
                    evidence_id=evidence_id,
                    offending_ref=current_id,
                    detail=(
                        f"Ancestor available_at={current.available_at.isoformat()} "
                        f"exceeds cutoff={cutoff.isoformat()}."
                    ),
                )

            for parent_id in current.derived_from:
                result = dfs(parent_id, depth + 1)
                if result is not None:
                    active_path.remove(current_id)
                    return result

            active_path.remove(current_id)
            visited.add(current_id)
            return None

        failure = dfs(evidence_id, 0)
        if failure is not None:
            return failure

        return LineageResult(
            status=LineageStatus.CLEAN,
            evidence_id=evidence_id,
            detail="All supplied lineage nodes are available at or before cutoff.",
        )
