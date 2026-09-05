from dataclasses import dataclass
from datetime import datetime
from typing import Optional

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


@dataclass(frozen=True)
class IntegrationResult:
    binding_status: Optional[BindingStatus]
    authority_status: Optional[AuthorityStatus]
    tool_adapter_permitted: bool
    effect_disposition: EffectDisposition


class AuthorityExecutionIntegrator:
    def __init__(self):
        self.binding_validator = BindingValidator()
        self.authority_validator = AuthorityValidator()

    def evaluate(
        self,
        *,
        gateway_decision: str,
        binding: Optional[ExecutionBinding],
        grant: Optional[AuthorityGrant],
        subject_id: str,
        action: str,
        target: str,
        grant_id: Optional[str],
        at: datetime,
    ) -> IntegrationResult:
        if gateway_decision != "ALLOW":
            return IntegrationResult(
                binding_status=None,
                authority_status=None,
                tool_adapter_permitted=False,
                effect_disposition=EffectDisposition.NOT_EXECUTED,
            )

        binding_result = self.binding_validator.check(
            binding=binding,
            subject_id=subject_id,
            action=action,
            target=target,
            grant_id=grant_id,
        )

        if binding_result.status != BindingStatus.CLEAN:
            return IntegrationResult(
                binding_status=binding_result.status,
                authority_status=None,
                tool_adapter_permitted=False,
                effect_disposition=EffectDisposition.NOT_EXECUTED,
            )

        authority_result = self.authority_validator.check(
            grant=grant,
            subject_id=subject_id,
            action=action,
            target=target,
            at=at,
        )

        if authority_result.status != AuthorityStatus.CLEAN:
            return IntegrationResult(
                binding_status=BindingStatus.CLEAN,
                authority_status=authority_result.status,
                tool_adapter_permitted=False,
                effect_disposition=EffectDisposition.NOT_EXECUTED,
            )

        return IntegrationResult(
            binding_status=BindingStatus.CLEAN,
            authority_status=AuthorityStatus.CLEAN,
            tool_adapter_permitted=True,
            effect_disposition=EffectDisposition.EFFECT_PATH_ELIGIBLE,
        )
