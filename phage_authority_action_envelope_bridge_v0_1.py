"""
Minimal PHAGE Authority-to-ActionEnvelope Bridge v0.1.

This module implements only the frozen executable regression contract A-G.

It does not invoke the Tool Adapter.
It does not establish an operational effect.
It does not establish production execution.
"""

from datetime import datetime
from typing import Optional

from phage_gateway import ActionEnvelope
from phage_authority_engine_v0_1 import (
    AuthorityGrant,
    AuthorityStatus,
    AuthorityValidator,
)
from phage_authority_execution_binding_v0_1 import (
    BindingStatus,
    EffectDisposition,
    ExecutionBinding,
    BindingValidator,
)


def evaluate_bridge(
    *,
    binding: Optional[ExecutionBinding],
    grant: Optional[AuthorityGrant],
    preserved_grant_id: Optional[str],
    envelope: ActionEnvelope,
    at: datetime,
    session_valid: bool,
) -> dict:
    """
    Evaluate the frozen bridge boundary.

    SESSION_VALID
    AND
    AUTHORITY_VALID
    AND
    BOUND_OPERATION_PRESERVED
    -> effect path may remain eligible
    """

    if not session_valid:
        return {
            "binding_status": None,
            "authority_status": None,
            "effect_disposition": None,
            "session_validation": "REJECT",
            "effect_invocation": "BLOCKED",
            "principal": envelope.principal,
        }

    binding_result = BindingValidator().check(
        binding=binding,
        subject_id=envelope.agent,
        action=envelope.action,
        target=envelope.target,
        grant_id=preserved_grant_id,
    )

    if binding_result.status is not BindingStatus.CLEAN:
        return {
            "binding_status": binding_result.status,
            "authority_status": None,
            "effect_disposition": EffectDisposition.NOT_EXECUTED,
            "session_validation": "ALLOW",
            "effect_invocation": None,
            "principal": envelope.principal,
        }

    authority_result = AuthorityValidator().check(
        grant=grant,
        subject_id=envelope.agent,
        action=envelope.action,
        target=envelope.target,
        at=at,
    )

    if authority_result.status is not AuthorityStatus.CLEAN:
        return {
            "binding_status": BindingStatus.CLEAN,
            "authority_status": authority_result.status,
            "effect_disposition": EffectDisposition.NOT_EXECUTED,
            "session_validation": "ALLOW",
            "effect_invocation": None,
            "principal": envelope.principal,
        }

    return {
        "binding_status": BindingStatus.CLEAN,
        "authority_status": AuthorityStatus.CLEAN,
        "effect_disposition": EffectDisposition.EFFECT_PATH_ELIGIBLE,
        "session_validation": "ALLOW",
        "effect_invocation": None,
        "principal": envelope.principal,
    }
