#!/usr/bin/env python3
"""
Regression tests for the PHAGE governed execution boundary.

These tests independently observe whether the downstream tool
was actually invoked.

Core invariant:

    BLOCK => TOOL_NOT_INVOKED
"""

from phage_gateway import ActionEnvelope, Decision, FailureCondition
from phage_executor import execute_governed


class InvocationCounter:
    def __init__(self) -> None:
        self.count = 0

    def tool(self, envelope: ActionEnvelope) -> str:
        self.count += 1
        return f"executed:{envelope.action}:{envelope.target}"


def test_allowed_action_invokes_tool() -> None:
    counter = InvocationCounter()

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

    result = execute_governed(envelope, counter.tool)

    assert result.receipt.decision is Decision.ALLOW
    assert result.tool_invoked is True
    assert counter.count == 1
    assert result.tool_result == "executed:delete_record:record_456"


def test_unverified_instruction_does_not_invoke_tool() -> None:
    counter = InvocationCounter()

    envelope = ActionEnvelope(
        principal="user_123",
        agent="agent_17",
        action="delete_record",
        target="record_456",
        instruction_source="external_content",
        instruction_principal="external_content",
        authorized_actions=("delete_record",),
        authorized_targets=("record_456",),
    )

    result = execute_governed(envelope, counter.tool)

    assert result.receipt.decision is Decision.BLOCK
    assert (
        result.receipt.failure_condition
        is FailureCondition.UNVERIFIED_INSTRUCTION_PROVENANCE
    )
    assert result.tool_invoked is False
    assert counter.count == 0
    assert result.tool_result is None


def test_scope_mismatch_does_not_invoke_tool() -> None:
    counter = InvocationCounter()

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

    result = execute_governed(envelope, counter.tool)

    assert result.receipt.decision is Decision.BLOCK
    assert (
        result.receipt.failure_condition
        is FailureCondition.AUTHORITY_SCOPE_MISMATCH
    )
    assert result.tool_invoked is False
    assert counter.count == 0
    assert result.tool_result is None


def main() -> int:
    tests = (
        (
            "ALLOW invokes downstream tool",
            test_allowed_action_invokes_tool,
        ),
        (
            "provenance BLOCK prevents tool invocation",
            test_unverified_instruction_does_not_invoke_tool,
        ),
                (
            "scope BLOCK prevents tool invocation",
            test_scope_mismatch_does_not_invoke_tool,
        ),
    )

    for name, test in tests:
        test()
        print(f"PASS: {name}")

    print("PHAGE execution-boundary regression PASS: 3 / 3.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
