from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Iterable


class CustodyStatus(str, Enum):
    CLEAN = "CLEAN"
    CUSTODY_UNRESOLVED = "CUSTODY_UNRESOLVED"
    CUSTODY_CONTINUITY_VIOLATION = "CUSTODY_CONTINUITY_VIOLATION"
    CUSTODY_INTEGRITY_VIOLATION = "CUSTODY_INTEGRITY_VIOLATION"


class CustodyEventType(str, Enum):
    ACQUIRED = "ACQUIRED"
    RECEIVED = "RECEIVED"
    TRANSFERRED = "TRANSFERRED"
    COPIED = "COPIED"
    TRANSFORMED = "TRANSFORMED"
    VERIFIED = "VERIFIED"
    RELEASED = "RELEASED"
    DELETED = "DELETED"


@dataclass(frozen=True)
class CustodyEvent:
    event_id: str
    artifact_id: str
    event_type: CustodyEventType
    actor_id: str
    timestamp: datetime
    from_custodian: str | None = None
    to_custodian: str | None = None
    artifact_fingerprint: str | None = None
    previous_event_id: str | None = None
    transformation_authorized: bool = False
    details: str = ""


@dataclass(frozen=True)
class CustodyResult:
    status: CustodyStatus
    artifact_id: str
    offending_event_id: str | None = None
    detail: str = ""


class CustodyValidator:
    def __init__(self, events: Iterable[CustodyEvent]) -> None:
        self._events = tuple(events)
        self._by_id = {event.event_id: event for event in self._events}

    def check(self, artifact_id: str) -> CustodyResult:
        events = sorted(
            (event for event in self._events if event.artifact_id == artifact_id),
            key=lambda event: event.timestamp,
        )

        if not events:
            return CustodyResult(
                status=CustodyStatus.CUSTODY_UNRESOLVED,
                artifact_id=artifact_id,
                detail="No custody events supplied for artifact.",
            )

        if len({event.event_id for event in events}) != len(events):
            return CustodyResult(
                status=CustodyStatus.CUSTODY_UNRESOLVED,
                artifact_id=artifact_id,
                detail="Duplicate custody event identifiers.",
            )

        for event in events:
            if (
                not event.event_id
                or not event.artifact_id
                or not event.actor_id
                or event.timestamp is None
            ):
                return CustodyResult(
                    status=CustodyStatus.CUSTODY_UNRESOLVED,
                    artifact_id=artifact_id,
                    offending_event_id=event.event_id or None,
                    detail="Custody event lacks required traceability fields.",
                )

            if not event.artifact_fingerprint:
                return CustodyResult(
                    status=CustodyStatus.CUSTODY_UNRESOLVED,
                    artifact_id=artifact_id,
                    offending_event_id=event.event_id,
                    detail="Artifact fingerprint is unavailable.",
                )

            if event.previous_event_id is None:
                if event.event_type is not CustodyEventType.ACQUIRED:
                    return CustodyResult(
                        status=CustodyStatus.CUSTODY_UNRESOLVED,
                        artifact_id=artifact_id,
                        offending_event_id=event.event_id,
                        detail="Non-acquisition event has no predecessor.",
                    )

                if not event.to_custodian:
                    return CustodyResult(
                        status=CustodyStatus.CUSTODY_UNRESOLVED,
                        artifact_id=artifact_id,
                        offending_event_id=event.event_id,
                        detail="Acquisition does not establish a custodian.",
                    )

                continue

            previous = self._by_id.get(event.previous_event_id)

            if previous is None:
                return CustodyResult(
                    status=CustodyStatus.CUSTODY_UNRESOLVED,
                    artifact_id=artifact_id,
                    offending_event_id=event.event_id,
                    detail=(
                        f"Previous custody event "
                        f"{event.previous_event_id!r} is missing."
                    ),
                )

            if previous.artifact_id != artifact_id:
                return CustodyResult(
                    status=CustodyStatus.CUSTODY_UNRESOLVED,
                    artifact_id=artifact_id,
                    offending_event_id=event.event_id,
                    detail="Predecessor references a different artifact.",
                )

            fingerprint_changed = (
                previous.artifact_fingerprint != event.artifact_fingerprint
            )

            authorized_transformation = (
                event.event_type is CustodyEventType.TRANSFORMED
                and event.transformation_authorized
            )

            if fingerprint_changed and not authorized_transformation:
                return CustodyResult(
                    status=CustodyStatus.CUSTODY_INTEGRITY_VIOLATION,
                    artifact_id=artifact_id,
                    offending_event_id=event.event_id,
                    detail="Artifact fingerprint changed without an authorized transformation.",
                )

            if event.event_type is CustodyEventType.TRANSFERRED:
                previous_custodian = previous.to_custodian

                if (
                    not previous_custodian
                    or not event.from_custodian
                    or event.from_custodian != previous_custodian
                ):
                    return CustodyResult(
                        status=CustodyStatus.CUSTODY_CONTINUITY_VIOLATION,
                        artifact_id=artifact_id,
                        offending_event_id=event.event_id,
                        detail=(
                            "Transfer source does not match the previously "
                            "established custodian."
                        ),
                    )

                if not event.to_custodian:
                    return CustodyResult(
                        status=CustodyStatus.CUSTODY_UNRESOLVED,
                        artifact_id=artifact_id,
                        offending_event_id=event.event_id,
                        detail="Transfer does not identify the receiving custodian.",
                    )

        return CustodyResult(
            status=CustodyStatus.CLEAN,
            artifact_id=artifact_id,
            detail="Custody chain satisfies Digital Custody v0.1 invariants.",
        )
