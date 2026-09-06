"""
Regression-first scaffold for PHAGE Authority-to-ActionEnvelope Bridge v0.1.

Frozen semantic fixtures: A-G.

This regression intentionally depends on a bridge implementation that does not
exist yet. The first expected CI result is RED due to the missing bridge
module.

Only the bridge module boundary and the callable evaluate_bridge entry point
are frozen by this scaffold.

The evaluate_bridge parameter signature and implementation API are not yet
frozen.
"""

import importlib


BRIDGE_MODULE = "phage_authority_action_envelope_bridge_v0_1"
BRIDGE_ENTRY_POINT = "evaluate_bridge"
FROZEN_FIXTURES = (
    {
        "id": "A",
        "name": "clean subject operation and grant bridge",
        "expected_binding_status": "CLEAN",
        "expected_authority_status": "CLEAN",
        "expected_effect_disposition": "EFFECT_PATH_ELIGIBLE",
    },
    {
        "id": "B",
        "name": "subject does not match executing agent",
        "expected_binding_status": "BOUND_OPERATION_MISMATCH",
        "expected_authority_status": None,
        "expected_effect_disposition": "NOT_EXECUTED",
    },
    {
        "id": "C",
        "name": "principal differs from agent but bound agent is preserved",
        "expected_binding_status": "CLEAN",
        "expected_authority_status": "CLEAN",
        "expected_effect_disposition": "EFFECT_PATH_ELIGIBLE",
    },
    {
        "id": "D",
        "name": "bound action or target changes at envelope boundary",
        "expected_binding_status": "BOUND_OPERATION_MISMATCH",
        "expected_authority_status": None,
        "expected_effect_disposition": "NOT_EXECUTED",
    },
    {
        "id": "E",
        "name": "preserved grant context does not match binding",
        "expected_binding_status": "BOUND_GRANT_MISMATCH",
        "expected_authority_status": None,
        "expected_effect_disposition": "NOT_EXECUTED",
    },
    {
        "id": "F",
        "name": "authority revoked after earlier clean decision",
        "expected_binding_status": "CLEAN",
        "expected_authority_status": "AUTHORITY_REVOKED",
        "expected_effect_disposition": "NOT_EXECUTED",
    },
    {
        "id": "G",
        "name": "session revoked while authority remains valid",
        "expected_binding_status": "CLEAN",
        "expected_authority_status": "CLEAN",
        "expected_effect_disposition": None,
        "expected_session_validation": "REJECT",
        "expected_effect_invocation": "BLOCKED",
    },
)


def test_frozen_fixture_manifest_is_complete() -> None:
    assert tuple(fixture["id"] for fixture in FROZEN_FIXTURES) == tuple("ABCDEFG")

def load_bridge_entry_point():
    module = importlib.import_module(BRIDGE_MODULE)

    assert hasattr(module, BRIDGE_ENTRY_POINT), (
        f"{BRIDGE_MODULE} must expose {BRIDGE_ENTRY_POINT}"
    )

    entry_point = getattr(module, BRIDGE_ENTRY_POINT)

    assert callable(entry_point), (
        f"{BRIDGE_MODULE}.{BRIDGE_ENTRY_POINT} must be callable"
    )

    return entry_point


def test_minimal_executable_bridge_contract_exists() -> None:
    load_bridge_entry_point()


if __name__ == "__main__":
    test_frozen_fixture_manifest_is_complete()
    test_minimal_executable_bridge_contract_exists()
