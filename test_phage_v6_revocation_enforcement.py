"""
PHAGE v6 mid-flight revocation enforcement regression.

This test exercises the TOCTOU boundary:

valid session
-> Gateway ALLOW
-> session revoked
-> downstream effect attempt

The expected invariant is that revocation before effect execution
must prevent the adapter effect.
"""

from security.pqc.engine import PQCEngine
from security.pqc.schemas import AgentIdentityClaim

from phage_gateway import (
    ActionEnvelope,
    Decision,
    evaluate_action,
)

from phage_tool_adapter import SandboxToolAdapter


ACTION = "刪除記錄"
TARGET = "record_456"


def establish_session():
    engine = PQCEngine(
        phage_secret="phage-v6-revocation-enforcement"
    )

    identity = AgentIdentityClaim(
        agent_id="revocation-enforcement-agent",
        principal_id="user_123",
        name="PHAGE v6 revocation enforcement agent",
        authorized_actions=[ACTION],
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


def test_revocation_after_allow_blocks_effect():
    engine, identity = establish_session()

    valid, detail = engine.validate_session(
        identity.agent_id,
        ACTION,
    )

    assert valid is True, detail

    envelope = ActionEnvelope(
        principal=identity.principal_id,
        agent=identity.agent_id,
        action=ACTION,
        target=TARGET,
        instruction_source="authenticated_user_session",
        instruction_principal=identity.principal_id,
        authorized_actions=tuple(identity.authorized_actions),
        authorized_targets=(TARGET,),
    )

    result = evaluate_action(envelope)

    assert result.decision is Decision.ALLOW

    revoked = engine.revoke_session(
        identity.agent_id
    )

    assert revoked is True

    adapter = SandboxToolAdapter(
    pre_effect_guard=lambda envelope: engine.validate_session(
        envelope.agent,
        envelope.action,
    )
    )
    # This represents an already-authorized action reaching the
    # downstream execution boundary after its session was revoked.
    adapter.invoke(envelope)

    # Required invariant:
    # revocation before effect execution must prevent the effect.
    assert adapter.effect.invoked is False


def main():
    test_revocation_after_allow_blocks_effect()

    print(
        "PASS: revoked session cannot execute "
        "a previously allowed downstream effect"
    )
    print(
        "PHAGE v6 revocation enforcement regression PASS: 1 / 1"
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
