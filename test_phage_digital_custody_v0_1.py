"""
DF-016 Digital Custody v0.1 regression.

Design-frozen fixtures:

A — clean custody transfer
    -> CLEAN

B — custody gap
    -> CUSTODY_UNRESOLVED

C — integrity break
    -> CUSTODY_INTEGRITY_VIOLATION

D — discontinuous custodian
    -> CUSTODY_CONTINUITY_VIOLATION

This regression intentionally precedes implementation.
"""

from datetime import datetime, timezone

from phage_digital_custody_v0_1 import (
    CustodyEvent,
    CustodyEventType,
    CustodyStatus,
    CustodyValidator,
)


UTC = timezone.utc


def ts(hour: int) -> datetime:
    return datetime(2026, 9, 1, hour, 0, 0, tzinfo=UTC)


def test_a_clean_custody_transfer():
    events = (
        CustodyEvent(
            event_id="A1",
            artifact_id="artifact-H1",
            event_type=CustodyEventType.ACQUIRED,
            actor_id="alice",
            timestamp=ts(9),
            to_custodian="alice",
            artifact_fingerprint="H1",
        ),
        CustodyEvent(
            event_id="A2",
            artifact_id="artifact-H1",
            event_type=CustodyEventType.TRANSFERRED,
            actor_id="alice",
            timestamp=ts(10),
            from_custodian="alice",
            to_custodian="bob",
            artifact_fingerprint="H1",
            previous_event_id="A1",
        ),
        CustodyEvent(
            event_id="A3",
            artifact_id="artifact-H1",
            event_type=CustodyEventType.TRANSFERRED,
            actor_id="bob",
            timestamp=ts(11),
            from_custodian="bob",
            to_custodian="carol",
            artifact_fingerprint="H1",
            previous_event_id="A2",
        ),
    )

    result = CustodyValidator(events).check("artifact-H1")
    assert result.status is CustodyStatus.CLEAN


def test_b_custody_gap_is_unresolved():
    events = (
        CustodyEvent(
            event_id="B1",
            artifact_id="artifact-H1",
            event_type=CustodyEventType.ACQUIRED,
            actor_id="alice",
            timestamp=ts(9),
            to_custodian="alice",
            artifact_fingerprint="H1",
        ),
        CustodyEvent(
            event_id="B3",
            artifact_id="artifact-H1",
            event_type=CustodyEventType.RECEIVED,
            actor_id="carol",
            timestamp=ts(11),
            to_custodian="carol",
            artifact_fingerprint="H1",
            previous_event_id="B2-MISSING",
        ),
    )

    result = CustodyValidator(events).check("artifact-H1")
    assert result.status is CustodyStatus.CUSTODY_UNRESOLVED


def test_c_integrity_break_is_rejected():
    events = (
        CustodyEvent(
            event_id="C1",
            artifact_id="artifact-H1",
            event_type=CustodyEventType.ACQUIRED,
            actor_id="alice",
            timestamp=ts(9),
            to_custodian="alice",
            artifact_fingerprint="H1",
        ),
        CustodyEvent(
            event_id="C2",
            artifact_id="artifact-H1",
            event_type=CustodyEventType.TRANSFERRED,
            actor_id="alice",
            timestamp=ts(10),
            from_custodian="alice",
            to_custodian="bob",
            artifact_fingerprint="H2",
            previous_event_id="C1",
            transformation_authorized=False,
        ),
    )

    result = CustodyValidator(events).check("artifact-H1")
    assert result.status is CustodyStatus.CUSTODY_INTEGRITY_VIOLATION


def test_d_discontinuous_custodian_is_rejected():
    events = (
        CustodyEvent(
            event_id="D1",
            artifact_id="artifact-H1",
            event_type=CustodyEventType.ACQUIRED,
            actor_id="alice",
            timestamp=ts(9),
            to_custodian="alice",
            artifact_fingerprint="H1",
        ),
        CustodyEvent(
            event_id="D2",
            artifact_id="artifact-H1",
            event_type=CustodyEventType.TRANSFERRED,
            actor_id="bob",
            timestamp=ts(10),
            from_custodian="bob",
            to_custodian="carol",
            artifact_fingerprint="H1",
            previous_event_id="D1",
        ),
    )

    result = CustodyValidator(events).check("artifact-H1")
    assert result.status is CustodyStatus.CUSTODY_CONTINUITY_VIOLATION


def main():
    tests = (
        test_a_clean_custody_transfer,
        test_b_custody_gap_is_unresolved,
        test_c_integrity_break_is_rejected,
        test_d_discontinuous_custodian_is_rejected,
    )

    for test in tests:
        test()
        print(f"PASS: {test.__name__}")

    print("DF-016 Digital Custody regression PASS: 4 / 4")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
