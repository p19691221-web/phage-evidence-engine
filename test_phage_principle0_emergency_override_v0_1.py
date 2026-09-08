"""
Executable regression contract for PHAGE Principle 0 Emergency Override v0.1.

Frozen semantic fixtures: A-F, including F1/F2.

This regression freezes only:
- the Emergency Override implementation module boundary
- the callable evaluate_override entry point
- the minimal dict-based test representation required by A-F / F1-F2
- the regression observation mapping returned by evaluate_override

It does not freeze a production EmergencyOverrideGrant class, persistence model,
emergency declaration system, institutional policy language, root Authority
model, Gateway API, Tool Adapter API, or production execution API.
"""

import importlib
from copy import deepcopy
from datetime import datetime, timedelta, timezone

from phage_authority_engine_v0_1 import AuthorityStatus


OVERRIDE_MODULE = "phage_principle0_emergency_override_v0_1"
OVERRIDE_ENTRY_POINT = "evaluate_override"

AT = datetime(2026, 9, 8, 10, 0, tzinfo=timezone.utc)


FROZEN_FIXTURES = (
    {
        "id": "A",
        "name": "resolved time mismatch with valid narrow override",
        "schedule_status": "SCHEDULE_NO_MATCH",
        "expected_override_status": "OVERRIDE_APPLICABLE",
    },
    {
        "id": "B",
        "name": "resolved mismatch outside override dimensions",
        "schedule_status": "SCHEDULE_NO_MATCH",
        "expected_override_status": "OVERRIDE_NOT_APPLICABLE",
    },
    {
        "id": "C",
        "name": "unresolved schedule cannot be overridden",
        "schedule_status": "SCHEDULE_UNRESOLVED",
        "expected_override_status": "OVERRIDE_UNRESOLVED",
    },
    {
        "id": "D",
               "name": "missing override source remains authority unresolved",
        "schedule_status": "SCHEDULE_NO_MATCH",
        "expected_authority_status": "AUTHORITY_UNRESOLVED",
    },
    {
        "id": "E",
        "name": "valid override does not repair revoked ordinary authority",
        "schedule_status": "SCHEDULE_NO_MATCH",
        "expected_authority_status": "AUTHORITY_REVOKED",
        "expected_effect_path": "BLOCKED",
    },
    {
        "id": "F",
        "name": "earlier override applicability does not survive loss of validity",
        "initial_override_status": "OVERRIDE_APPLICABLE",
        "subcases": {
            "F1": {
                "change": "OVERRIDE_REVOKED",
                "expected_authority_status": "AUTHORITY_REVOKED",
                "expected_effect_path": "BLOCKED",
            },
            "F2": {
                "change": "OVERRIDE_EXPIRED",
                "expected_authority_status": "AUTHORITY_EXPIRED",
                "expected_effect_path": "BLOCKED",
            },
        },
    },
)


def status_name(value) -> str:
    if value is None:
        return "NONE"

    if hasattr(value, "name"):
        return value.name

    return str(value)
def load_override_entry_point():
    module = importlib.import_module(OVERRIDE_MODULE)

    assert hasattr(module, OVERRIDE_ENTRY_POINT), (
        f"{OVERRIDE_MODULE} must expose {OVERRIDE_ENTRY_POINT}"
    )

    entry_point = getattr(module, OVERRIDE_ENTRY_POINT)

    assert callable(entry_point), (
        f"{OVERRIDE_MODULE}.{OVERRIDE_ENTRY_POINT} must be callable"
    )

    return entry_point


def make_override_grant(
    *,
    override_dimensions=("TIME",),
    issuer_id="authority-service",
    source_ref="emergency-override-policy-17",
    revoked=False,
    revoked_at=None,
    expires_at=None,
) -> dict:
    if expires_at is None:
        expires_at = AT + timedelta(hours=1)

    return {
        "override_id": "EO-001",
        "subject_id": "agent-A",
        "issuer_id": issuer_id,
        "authorized_action": "READ",
        "authorized_target": "record-123",
        "schedule_ref": {
            "schedule_id": "schedule-OR-7",
            "version": "v17",
        },
        "override_dimensions": tuple(override_dimensions),
        "emergency_ref": "incident-42",
        "issued_at": AT - timedelta(minutes=5),
        "expires_at": expires_at,
        "revoked": revoked,
        "revoked_at": revoked_at,
        "source_ref": source_ref,
    }
    
def make_request(
    *,
    schedule_status="SCHEDULE_NO_MATCH",
    mismatch_dimension="TIME",
    ordinary_authority_status=AuthorityStatus.CLEAN,
) -> dict:
    return {
        "subject_id": "agent-A",
        "action": "READ",
        "target": "record-123",
        "schedule_status": schedule_status,
        "mismatch_dimension": mismatch_dimension,
        "schedule_ref": {
            "schedule_id": "schedule-OR-7",
            "version": "v17",
        },
        "ordinary_authority_status": ordinary_authority_status,
        "at": AT,
    }


def assert_result_shape(result) -> None:
    required_keys = {
        "schedule_status",
        "override_status",
        "authority_status",
        "effect_path",
    }

    assert isinstance(result, dict), (
        "evaluate_override must return a dict regression observation"
    )

    assert required_keys.issubset(result), (
        f"evaluate_override result missing keys: "
        f"{required_keys - set(result)}"
    )
def test_frozen_fixture_manifest_is_complete() -> None:
    assert tuple(
        fixture["id"] for fixture in FROZEN_FIXTURES
    ) == tuple("ABCDEF")

    fixture_f = next(
        fixture for fixture in FROZEN_FIXTURES
        if fixture["id"] == "F"
    )

    assert tuple(fixture_f["subcases"]) == ("F1", "F2")


def test_minimal_executable_override_contract_exists() -> None:
    load_override_entry_point()


def run_fixture_a(evaluate_override) -> None:
    result = evaluate_override(
        request=make_request(),
        override_grant=make_override_grant(
            override_dimensions=("TIME",),
        ),
    )

    assert_result_shape(result)

    assert result["schedule_status"] == "SCHEDULE_NO_MATCH"
    assert status_name(result["override_status"]) == "OVERRIDE_APPLICABLE"
    assert status_name(result["authority_status"]) == "CLEAN"


def run_fixture_b(evaluate_override) -> None:
    result = evaluate_override(
        request=make_request(
            mismatch_dimension="SPACE",
        ),
        override_grant=make_override_grant(
            override_dimensions=("TIME",),
        ),
    )

    assert_result_shape(result)

    assert result["schedule_status"] == "SCHEDULE_NO_MATCH"
    assert status_name(result["override_status"]) == "OVERRIDE_NOT_APPLICABLE"
    def run_fixture_c(evaluate_override) -> None:
    result = evaluate_override(
        request=make_request(
            schedule_status="SCHEDULE_UNRESOLVED",
            mismatch_dimension=None,
        ),
        override_grant=make_override_grant(),
    )

    assert_result_shape(result)

    assert result["schedule_status"] == "SCHEDULE_UNRESOLVED"
    assert status_name(result["override_status"]) == "OVERRIDE_UNRESOLVED"
    assert result["effect_path"] == "BLOCKED"


def run_fixture_d(evaluate_override) -> None:
    for grant in (
        make_override_grant(issuer_id=None),
        make_override_grant(source_ref=None),
    ):
        result = evaluate_override(
            request=make_request(),
            override_grant=grant,
        )

        assert_result_shape(result)

        assert status_name(
            result["authority_status"]
        ) == "AUTHORITY_UNRESOLVED"

        assert status_name(
            result["override_status"]
        ) != "OVERRIDE_APPLICABLE"

        assert result["effect_path"] == "BLOCKED"
        def run_fixture_e(evaluate_override) -> None:
    result = evaluate_override(
        request=make_request(
            ordinary_authority_status=AuthorityStatus.AUTHORITY_REVOKED,
        ),
        override_grant=make_override_grant(),
    )

    assert_result_shape(result)

    assert status_name(
        result["authority_status"]
    ) == "AUTHORITY_REVOKED"

    assert result["effect_path"] == "BLOCKED"


def run_fixture_f(evaluate_override) -> None:
    request = make_request()

    initial_grant = make_override_grant()

    earlier = evaluate_override(
        request=request,
        override_grant=initial_grant,
    )

    assert_result_shape(earlier)

    assert earlier["schedule_status"] == "SCHEDULE_NO_MATCH"

    assert status_name(
        earlier["override_status"]
    ) == "OVERRIDE_APPLICABLE"

    revoked_grant = deepcopy(initial_grant)
    revoked_grant["revoked"] = True
    revoked_grant["revoked_at"] = AT

    f1 = evaluate_override(
        request=request,
        override_grant=revoked_grant,
    )

    assert_result_shape(f1)

    assert status_name(
        f1["authority_status"]
    ) == "AUTHORITY_REVOKED"

    assert f1["effect_path"] == "BLOCKED"

    expired_grant = deepcopy(initial_grant)
    expired_grant["expires_at"] = AT - timedelta(seconds=1)

    f2 = evaluate_override(
        request=request,
        override_grant=expired_grant,
    )

    assert_result_shape(f2)

    assert status_name(
        f2["authority_status"]
    ) == "AUTHORITY_EXPIRED"

    assert f2["effect_path"] == "BLOCKED"
    if __name__ == "__main__":
    test_frozen_fixture_manifest_is_complete()
    test_minimal_executable_override_contract_exists()

    evaluate_override = load_override_entry_point()

    fixtures = (
        (
            "A",
            "resolved_time_mismatch_valid_narrow_override",
            lambda: run_fixture_a(evaluate_override),
        ),
        (
            "B",
            "mismatch_outside_override_dimensions",
            lambda: run_fixture_b(evaluate_override),
        ),
        (
            "C",
            "unresolved_schedule_fail_closed",
            lambda: run_fixture_c(evaluate_override),
        ),
        (
            "D",
            "missing_override_source_authority_unresolved",
            lambda: run_fixture_d(evaluate_override),
        ),
        (
            "E",
            "revoked_ordinary_authority_not_repaired",
            lambda: run_fixture_e(evaluate_override),
        ),
        (
            "F",
            "effect_time_override_revalidation",
            lambda: run_fixture_f(evaluate_override),
        ),
    )

    for fixture_id, name, run in fixtures:
        run()

        print(
            f"PASS: fixture_{fixture_id}_{name}"
        )

    print(
        "Principle 0 Emergency Override regression PASS: 6 / 6 "
        "(F includes F1 revocation + F2 expiration)"
    )
