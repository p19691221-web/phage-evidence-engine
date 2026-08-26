#!/usr/bin/env python3
"""
Regression tests for PHAGE Gateway MVP.

The tests lock three distinct governance outcomes:

1. Trusted instruction + valid scope -> ALLOW
2. Untrusted instruction provenance -> BLOCK
3. Trusted instruction + exceeded scope -> BLOCK

The second and third cases MUST remain distinct.
"""

from phage_gateway import (
    ActionEnvelope,
    Decision,
    FailureCondition,
    evaluate_action,
)


def test_trusted_instruction_valid_scope_allows() -> None:
    envelope = ActionEnvelope(
        principal="user_123",
        agent="agent_17",
        action="delete_record",
        target="record_456",
        instruction_source="authenticated_user_session",
        instruction_principal="user_123",
        authorized_actions=("delete_record",),
        authorized_targets=("record_456",),
    )

    receipt = evaluate_action(envelope)

    assert receipt.decision is Decision.ALLOW
    assert receipt.failure_condition is None


def test_external_instruction_cannot_inherit_user_authority() -> None:
    envelope = ActionEnvelope(
        principal="user_123",
        agent="agent_17",
        action="delete_record",
        target="record_456",
        instruction_source="external_email_content",
        instruction_principal="external_sender",
        authorized_actions=("delete_record",),
        authorized_targets=("record_456",),
    )

    receipt = evaluate_action(envelope)

    assert receipt.decision is Decision.BLOCK
    assert (
        receipt.failure_condition
        is FailureCondition.UNVERIFIED_INSTRUCTION_PROVENANCE
    )


def test_valid_principal_cannot_exceed_scope() -> None:
    envelope = ActionEnvelope(
        principal="user_123",
        agent="agent_17",
        action="delete_record",
        target="record_999",
        instruction_source="authenticated_user_session",
        instruction_principal="user_123",
        authorized_actions=("delete_record",),
        authorized_targets=("record_456",),
    )

    receipt = evaluate_action(envelope)

    assert receipt.decision is Decision.BLOCK
    assert (
        receipt.failure_condition
        is FailureCondition.AUTHORITY_SCOPE_MISMATCH
    )


def main() -> int:
    tests = (
        (
            "trusted instruction + valid scope",
            test_trusted_instruction_valid_scope_allows,
        ),
        (
            "external instruction provenance",
            test_external_instruction_cannot_inherit_user_authority,
        ),
        (
            "authority scope mismatch",
            test_valid_principal_cannot_exceed_scope,
        ),
    )

    for name, test in tests:
        test()
        print(f"PASS: {name}")

    print("PHAGE Gateway regression PASS: 3 / 3.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
