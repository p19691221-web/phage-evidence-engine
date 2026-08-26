#!/usr/bin/env python3
"""
PHAGE governed execution layer.

An action may reach a tool only after the PHAGE Gateway
returns an explicit ALLOW decision.

Core invariant:

    BLOCK => TOOL_NOT_INVOKED
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from phage_gateway import ActionEnvelope, Decision, ExecutionReceipt, evaluate_action


@dataclass(frozen=True)
class GovernedExecutionResult:
    receipt: ExecutionReceipt
    tool_invoked: bool
    tool_result: Any = None


def execute_governed(
    envelope: ActionEnvelope,
    tool: Callable[[ActionEnvelope], Any],
) -> GovernedExecutionResult:
    """
    Evaluate an action through PHAGE before permitting tool execution.
    """

    receipt = evaluate_action(envelope)

    if receipt.decision is not Decision.ALLOW:
        return GovernedExecutionResult(
            receipt=receipt,
            tool_invoked=False,
            tool_result=None,
        )

    result = tool(envelope)

    return GovernedExecutionResult(
        receipt=receipt,
        tool_invoked=True,
        tool_result=result,
    )
