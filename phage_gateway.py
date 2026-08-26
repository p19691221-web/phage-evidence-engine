#!/usr/bin/env python3
"""
PHAGE Gateway MVP.

A minimal governance enforcement layer between an AI agent
and a tool capable of producing real-world effects.

Core rule:

    OBSERVED_INSTRUCTION != AUTHORIZED_INSTRUCTION

An agent may propose an action.
PHAGE decides whether that action may cross the execution boundary.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Decision(str, Enum):
    ALLOW = "ALLOW"
    BLOCK = "BLOCK"
    ESCALATE = "ESCALATE"


class FailureCondition(str, Enum):
    UNVERIFIED_INSTRUCTION_PROVENANCE = (
        "UNVERIFIED_INSTRUCTION_PROVENANCE"
    )
    AUTHORITY_SCOPE_MISMATCH = "AUTHORITY_SCOPE_MISMATCH"


@dataclass(frozen=True)
class ActionEnvelope:
    principal: str
    agent: str
    action: str
    target: str

    instruction_source: str
    instruction_principal: str

    authorized_actions: tuple[str, ...]
    authorized_targets: tuple[str, ...]


@dataclass(frozen=True)
class ExecutionReceipt:
    decision: Decision
    action: str
    target: str
    principal: str

    failure_condition: FailureCondition | None
    detail: str


def check_instruction_provenance(
    envelope: ActionEnvelope,
) -> FailureCondition | None:
    """
    Verify that the instruction is attributable to the principal
    whose authority is being invoked.

    Merely observing an instruction is not sufficient.
    """
    if envelope.instruction_principal != envelope.principal:
        return FailureCondition.UNVERIFIED_INSTRUCTION_PROVENANCE

    return None


def check_scope(
    envelope: ActionEnvelope,
) -> FailureCondition | None:
    """
    Verify that the requested action and target remain inside
    the principal's delegated scope.
    """
    if envelope.action not in envelope.authorized_actions:
        return FailureCondition.AUTHORITY_SCOPE_MISMATCH

    if envelope.target not in envelope.authorized_targets:
        return FailureCondition.AUTHORITY_SCOPE_MISMATCH

    return None


def evaluate_action(envelope: ActionEnvelope) -> ExecutionReceipt:
    """
    PHAGE enforcement point.

    Checks are deliberately ordered:

        provenance
            ->
        authority / scope
            ->
        execution decision

    A later check cannot repair failure of an earlier transition.
    """

    provenance_failure = check_instruction_provenance(envelope)

    if provenance_failure is not None:
        return ExecutionReceipt(
            decision=Decision.BLOCK,
            action=envelope.action,
            target=envelope.target,
            principal=envelope.principal,
            failure_condition=provenance_failure,
            detail=(
                "Observed instruction was not established as an "
                "authorized instruction from the invoked principal."
            ),
        )

    scope_failure = check_scope(envelope)

    if scope_failure is not None:
        return ExecutionReceipt(
            decision=Decision.BLOCK,
            action=envelope.action,
            target=envelope.target,
            principal=envelope.principal,
            failure_condition=scope_failure,
            detail=(
                "Instruction provenance was valid, but the requested "
                "action exceeded the delegated authority scope."
            ),
        )

    return ExecutionReceipt(
        decision=Decision.ALLOW,
        action=envelope.action,
        target=envelope.target,
        principal=envelope.principal,
        failure_condition=None,
        detail=(
            "Instruction provenance and delegated authority scope "
            "were established."
        ),
    )
