"""
Executable regression contract for PHAGE Authority-to-ActionEnvelope Bridge v0.1.

Frozen semantic fixtures: A-G.

This regression freezes only:
- the bridge module boundary
- the callable evaluate_bridge entry point
- the minimal keyword-only executable contract used by A-G
- the regression observation mapping returned by evaluate_bridge

It does not freeze a BridgeContext class, composed-guard class, callback
ordering, or any production Tool Adapter API.
"""

import importlib
from dataclasses import replace
from datetime import datetime, timedelta, timezone

from phage_gateway import ActionEnvelope
from phage_authority_engine_v0_1 import AuthorityGrant, AuthorityStatus
from phage_authority_execution_binding_v0_1 import (
    BindingStatus,
    EffectDisposition,
    ExecutionBinding,
)


BRIDGE_MODULE = "phage_authority_action_envelope_bridge_v0_1"
BRIDGE_ENTRY_POINT = "evaluate_bridge"

AT = datetime(2026, 9, 7, 0, 0, tzinfo=timezone.utc)


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
        
        
        "expected_effect_disposition": None,
        "expected_session_validation": "REJECT",
        "expected_effect_invocation": "BLOCKED",
    },
)


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


def make_binding() -> ExecutionBinding:
    return ExecutionBinding(
        decision_id="D-001",
        subject_id="agent-A",
        action="READ",
        target="record-123",
        grant_id="G-001",
        decision_time=AT - timedelta(minutes=5),
    )


def make_grant() -> AuthorityGrant:
    return AuthorityGrant(
        grant_id="G-001",
        subject_id="agent-A",
        issuer_id="authority-service",
        authorized_actions=frozenset({"READ"}),
        authorized_targets=frozenset({"record-123"}),
        issued_at=AT - timedelta(hours=1),
        expires_at=AT + timedelta(hours=1),
        revoked=False,
        revoked_at=None,
        source_ref="policy-record-17",
    )


def make_envelope() -> ActionEnvelope:
    return ActionEnvelope(
        principal="user-123",
        agent="agent-A",
        action="READ",
        target="record-123",
        instruction_source="authenticated_user_session",
        instruction_principal="user-123",
        authorized_actions=("READ",),
        authorized_targets=("record-123",),
    )


def fixture_inputs(fixture_id: str):
    binding = make_binding()
    grant = make_grant()
    envelope = make_envelope()
    preserved_grant_id = "G-001"
    session_valid = True

    if fixture_id == "B":
        envelope = replace(envelope, agent="agent-B")

    elif fixture_id == "D":
        envelope = replace(envelope, action="DELETE")

    elif fixture_id == "E":
        preserved_grant_id = "G-002"

    elif fixture_id == "F":
        grant = replace(
            grant,
            revoked=True,
            revoked_at=AT,
        )

    elif fixture_id == "G":
        session_valid = False

    return {
        "binding": binding,
        "grant": grant,
        "preserved_grant_id": preserved_grant_id,
        "envelope": envelope,
        "at": AT,
        "session_valid": session_valid,
    }


def test_frozen_fixture_manifest_is_complete() -> None:
    assert tuple(
        fixture["id"] for fixture in FROZEN_FIXTURES
    ) == tuple("ABCDEFG")


def test_minimal_executable_bridge_contract_exists() -> None:
    load_bridge_entry_point()


def assert_fixture_result(fixture, result) -> None:
    required_keys = {
        "binding_status",
        "authority_status",
        "effect_disposition",
        "session_validation",
        "effect_invocation",
        "principal",
    }

    assert isinstance(result, dict), (
        "evaluate_bridge must return a dict regression observation"
    )

    assert required_keys.issubset(result), (
        f"evaluate_bridge result missing keys: "
        f"{required_keys - set(result)}"
    )

    if "expected_binding_status" in fixture:
        assert (
            result["binding_status"]
            is BindingStatus[fixture["expected_binding_status"]]
        )

    if "expected_authority_status" in fixture:
        expected_authority = fixture["expected_authority_status"]

        if expected_authority is None:
            assert result["authority_status"] is None
        else:
            assert (
                result["authority_status"]
                is AuthorityStatus[expected_authority]
            )

    expected_disposition = fixture["expected_effect_disposition"]

    if expected_disposition is None:
        assert result["effect_disposition"] is None
    else:
        assert (
            result["effect_disposition"]
            is EffectDisposition[expected_disposition]
        )

    if "expected_session_validation" in fixture:
        assert (
            result["session_validation"]
            == fixture["expected_session_validation"]
        )
    else:
        assert result["session_validation"] == "ALLOW"

    if "expected_effect_invocation" in fixture:
        assert (
            result["effect_invocation"]
            == fixture["expected_effect_invocation"]
        )
    else:
        assert result["effect_invocation"] is None

    assert result["principal"] == "user-123"

def test_fixtures_a_through_g() -> None:
    evaluate_bridge = load_bridge_entry_point()

    for fixture in FROZEN_FIXTURES:
        result = evaluate_bridge(
            **fixture_inputs(fixture["id"])
        )

        assert_fixture_result(fixture, result)

        print(
            f"PASS: fixture_{fixture['id']}_"
            f"{fixture['name'].replace(' ', '_')}"
        )


if __name__ == "__main__":
    test_frozen_fixture_manifest_is_complete()
    test_minimal_executable_bridge_contract_exists()
    test_fixtures_a_through_g()

    print(
        "Authority-to-ActionEnvelope Bridge regression PASS: 7 / 7"
    )
