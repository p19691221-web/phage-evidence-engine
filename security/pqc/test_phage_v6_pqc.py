"""
PHAGE v6 PQC prototype smoke test.

Validates the current prototype boundary only.
This does NOT claim production ML-KEM or ML-DSA validation.
"""

from .engine import PQCEngine
from .schemas import AgentIdentityClaim


def main() -> int:
    engine = PQCEngine(phage_secret="phage-v6-test-secret")

    identity = AgentIdentityClaim(
        agent_id="phage-v6-test-agent",
        principal_id="phage-v6-test-principal",
        name="PHAGE v6 test agent",
        authorized_actions=["read_evidence"],
    )

    # 1. Generate prototype key material.
    keypair = engine.generate_agent_keypair(identity.agent_id)

    assert keypair["agent_id"] == identity.agent_id
    assert keypair["key_fingerprint"]

    # 2. PHAGE issues a challenge.
    challenge, challenge_signature = engine.initiate_handshake(
        identity.agent_id
    )

    assert challenge
    assert challenge_signature

    # 3. Agent creates the current prototype challenge response.
    response = engine.create_agent_response(
        challenge,
        identity.agent_id,
    )

    # 4. Complete handshake.
    handshake = engine.complete_handshake(
        identity,
        challenge,
        response,
    )

    assert handshake.verified is True
    assert handshake.failure_reason is None
    assert handshake.shared_secret_hash

    # 5. Verify that a session was established and scope is enforced.
    valid, detail = engine.validate_session(
        identity.agent_id,
        "read_evidence",
    )

    assert valid is True, detail

    blocked, detail = engine.validate_session(
        identity.agent_id,
        "delete_evidence",
    )

    assert blocked is False
    assert "not authorized" in detail

    print("PASS: PHAGE v6 prototype key generation")
    print("PASS: PHAGE v6 prototype handshake")
    print("PASS: PHAGE v6 session establishment")
    print("PASS: PHAGE v6 action scope enforcement")
    print("PHAGE v6 PQC prototype smoke test PASS: 4 / 4")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
