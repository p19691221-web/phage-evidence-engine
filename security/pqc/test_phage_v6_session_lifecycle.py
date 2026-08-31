"""
PHAGE v6 session lifecycle regression.

Validates explicit session revocation without directly mutating
PQCEngine private session state.
"""

from .engine import PQCEngine
from .schemas import AgentIdentityClaim


def establish_session():
    engine = PQCEngine(
        phage_secret="phage-v6-session-lifecycle-test"
    )

    identity = AgentIdentityClaim(
        agent_id="session-lifecycle-agent",
        principal_id="session-lifecycle-principal",
        name="PHAGE v6 session lifecycle agent",
        authorized_actions=["read_evidence"],
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


def test_revoke_active_session():
    engine, identity = establish_session()

    valid, detail = engine.validate_session(
        identity.agent_id,
        "read_evidence",
    )

    assert valid is True, detail

    revoked = engine.revoke_session(
        identity.agent_id
    )

    assert revoked is True

    valid, detail = engine.validate_session(
        identity.agent_id,
        "read_evidence",
    )

    assert valid is False
    assert "inactive" in detail.lower()


def test_revoke_unknown_session():
    engine = PQCEngine(
        phage_secret="phage-v6-session-lifecycle-test"
    )

    revoked = engine.revoke_session(
        "unknown-agent"
    )

    assert revoked is False


def main():
    tests = (
        (
            "active session can be explicitly revoked",
            test_revoke_active_session,
        ),
        (
            "unknown session cannot be revoked",
            test_revoke_unknown_session,
        ),
    )

    for name, test in tests:
        test()
        print(f"PASS: {name}")

    print("PHAGE v6 session lifecycle regression PASS: 2 / 2")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
