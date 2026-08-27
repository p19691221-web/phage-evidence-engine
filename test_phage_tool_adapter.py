#!/usr/bin/env python3
"""
Regression tests for the PHAGE sandbox tool adapter.

Core invariant:

ALLOW => ADAPTER_INVOKED => EFFECT_OBSERVED
BLOCK => ADAPTER_NOT_INVOKED => NO_EFFECT
"""

from phage_gateway import ActionEnvelope, Decision
from phage_executor import execute_governed
from phage_tool_adapter import SandboxToolAdapter


def make_envelope(
    instruction_source: str,
    target: str,
) -> ActionEnvelope:
    return ActionEnvelope(
        principal="user_123",
        agent="agent_17",
        action="delete_record",
        target=target,
        instruction_source=instruction_source,
        instruction_principal="user_123",
        authorized_actions=("delete_record",),
        authorized_targets=("record_456",),
    )


def test_allow_produces_effect() -> None:
    adapter = SandboxToolAdapter()
    envelope = make_envelope(
        "authenticated_user_session",
        "record_456",
    )

    result = execute_governed(envelope, adapter.invoke)

    assert result.receipt.decision is Decision.ALLOW
    assert result.tool_invoked is True
    assert adapter.effect.invoked is True
    assert adapter.effect.action == "delete_record"
    assert adapter.effect.target == "record_456"


def test_unverified_provenance_produces_no_effect() -> None:
    adapter = SandboxToolAdapter()
    envelope = make_envelope(
        "external_content",
        "record_456",
    )

    result = execute_governed(envelope, adapter.invoke)

    assert result.receipt.decision is Decision.BLOCK
    assert result.tool_invoked is False
    assert adapter.effect.invoked is False


def test_scope_mismatch_produces_no_effect() -> None:
    adapter = SandboxToolAdapter()
    envelope = make_envelope(
        "authenticated_user_session",
        "record_999",
    )

    result = execute_governed(envelope, adapter.invoke)

    assert result.receipt.decision is Decision.BLOCK
    assert result.tool_invoked is False
    assert adapter.effect.invoked is False
  def main() -> int:
    tests = (
        (
            "ALLOW produces observable adapter effect",
            test_allow_produces_effect,
        ),
        (
            "provenance BLOCK produces no adapter effect",
            test_unverified_provenance_produces_no_effect,
        ),
        (
            "scope BLOCK produces no adapter effect",
            test_scope_mismatch_produces_no_effect,
        ),
    )

    for name, test in tests:
        test()
        print(f"PASS: {name}")

    print("PHAGE tool-adapter regression PASS: 3 / 3.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
