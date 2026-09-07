"""
Regression-first scaffold for PHAGE Principle 0 Emergency Override v0.1.

Frozen semantic fixtures: A-F.

This regression intentionally depends on an Emergency Override implementation
module that does not exist yet.

The first expected CI result is RED due to the missing implementation module.

This scaffold freezes only:
- the A-F semantic outcome manifest
- the implementation module boundary

It does not yet freeze a Python EmergencyOverrideGrant class, evaluator
signature, execution API, production emergency declaration system, root
authority model, or production policy engine.
"""

import importlib


OVERRIDE_MODULE = "phage_principle0_emergency_override_v0_1"


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


def test_frozen_fixture_manifest_is_complete() -> None:
    assert tuple(
        fixture["id"] for fixture in FROZEN_FIXTURES
    ) == tuple("ABCDEF")

    fixture_f = next(
        fixture for fixture in FROZEN_FIXTURES
        if fixture["id"] == "F"
    )

    assert tuple(fixture_f["subcases"]) == ("F1", "F2")


def test_override_implementation_exists() -> None:
    importlib.import_module(OVERRIDE_MODULE)


if __name__ == "__main__":
    test_frozen_fixture_manifest_is_complete()
    test_override_implementation_exists()
