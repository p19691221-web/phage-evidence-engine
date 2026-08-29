#!/usr/bin/env python3
"""
PHAGE v6 -> Gateway -> Tool Adapter integration regression.

Validated invariant:

VALID SESSION + AUTHORIZED ACTION + TRUSTED PROVENANCE
    -> Gateway ALLOW
    -> adapter invoked
    -> effect observed

UNAUTHORIZED ACTION
    -> blocked before adapter
    -> adapter not invoked
    -> no effect

INACTIVE SESSION
    -> blocked before adapter
    -> adapter not invoked
    -> no effect

This test validates integration behavior only.
It does not establish production PQC.
"""

from security.pqc.engine import PQCEngine
from security.pqc.schemas import AgentIdentityClaim

from phage_gateway import (
    ActionEnvelope,
    Decision,
    evaluate_action,
)

from phage_tool_adapter import SandboxToolAdapter


def establish_session():
    engine = PQCEngine(
        phage_secret="phage-v6-gateway-integration"
    )

    identity = AgentIdentityClaim(
        agent_id="agent_17",
        principal_id="user_123",
        name="PHAGE v6 integration agent",
        authorized_actions=["刪除記錄"],
    )

    engine.generate_agent_keypair(identity.agent_id)

    challenge, _ = engine.initiate_handshake(
        identity.agent_id
    )

    response = engine.create_agent_response(
        challenge,
        identity.agent_id,
    )

    handshake = engine.complete_handshake(
        identity,
        challenge,
        response,
    )

    assert handshake.verified is True

    return engine, identity


def invoke_through_phage(engine, identity, action):
    valid, detail = engine.validate_session(
        identity.agent_id,
        action,
    )

    adapter = SandboxToolAdapter()

    if not valid:
        return Decision.BLOCK, adapter, detail

    envelope = ActionEnvelope(
        principal=identity.principal_id,
        agent=identity.agent_id,
        action=action,
        target="record_456",
        instruction_source="authenticated_user_session",
        instruction_principal=identity.principal_id,
        authorized_actions=tuple(identity.authorized_actions),
        authorized_targets=("record_456",),
    )

    result = evaluate_action(envelope)

    if result.decision is Decision.ALLOW:
        adapter.invoke(envelope)

    return (
        result.decision,
        adapter,
        result.failure_condition,
    )
def test_valid_v6_session_reaches_effect():
    engine, identity = establish_session()

    decision, adapter, _ = invoke_through_phage(
        engine,
        identity,
        "刪除記錄",
    )

    assert decision is Decision.ALLOW
    assert adapter.effect.invoked is True
    assert adapter.effect.action == "刪除記錄"
    assert adapter.effect.target == "record_456"


def test_v6_authority_blocks_before_effect():
    engine, identity = establish_session()

    decision, adapter, detail = invoke_through_phage(
        engine,
        identity,
        "刪除全部資料",
    )

    assert decision is Decision.BLOCK
    assert adapter.effect.invoked is False
    assert detail


def test_inactive_v6_session_blocks_before_effect():
    engine, identity = establish_session()

    engine._session_store[identity.agent_id].is_active = False

    decision, adapter, detail = invoke_through_phage(
        engine,
        identity,
        "刪除記錄",
    )

    assert decision is Decision.BLOCK
    assert adapter.effect.invoked is False
    assert detail


def main():
    tests = (
        (
            "valid v6 session reaches governed effect",
            test_valid_v6_session_reaches_effect,
        ),
        (
            "v6 authority blocks before effect",
            test_v6_authority_blocks_before_effect,
        ),
        (
            "inactive v6 session blocks before effect",
            test_inactive_v6_session_blocks_before_effect,
        ),
    )

    for name, test in tests:
        test()
        print(f"PASS: {name}")

    print("PHAGE v6 Gateway integration regression PASS: 3 / 3")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
