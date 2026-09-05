from dataclasses import dataclass
from typing import Any, Callable, Optional

from phage_authority_execution_binding_v0_1 import (
    BindingStatus,
    EffectDisposition,
)

from phage_authority_execution_integration_v0_1 import IntegrationResult


@dataclass(frozen=True)
class BoundOperation:
    subject_id: str
    action: str
    target: str
    grant_id: str


@dataclass(frozen=True)
class EffectBoundaryResult:
    binding_status: Optional[BindingStatus]
    tool_adapter_invoked: bool
    effect_attempted: bool
    effect_occurred: bool


class EffectBoundaryHarness:
    def evaluate(
        self,
        *,
        integration_result: IntegrationResult,
        bound_operation: BoundOperation,
        presented_operation: BoundOperation,
        adapter: Any,
        observe_state: Callable[[], Any],
        invoke_adapter: bool,
    ) -> EffectBoundaryResult:
        eligible = (
            integration_result.tool_adapter_permitted is True
            and integration_result.effect_disposition
            == EffectDisposition.EFFECT_PATH_ELIGIBLE
        )

        if not eligible:
            return EffectBoundaryResult(
                binding_status=integration_result.binding_status,
                tool_adapter_invoked=False,
                effect_attempted=False,
                effect_occurred=False,
            )

        if (
            bound_operation.subject_id != presented_operation.subject_id
            or bound_operation.action != presented_operation.action
            or bound_operation.target != presented_operation.target
        ):
            return EffectBoundaryResult(
                binding_status=BindingStatus.BOUND_OPERATION_MISMATCH,
                tool_adapter_invoked=False,
                effect_attempted=False,
                effect_occurred=False,
            )

        if bound_operation.grant_id != presented_operation.grant_id:
            return EffectBoundaryResult(
                binding_status=BindingStatus.BOUND_GRANT_MISMATCH,
                tool_adapter_invoked=False,
                effect_attempted=False,
                effect_occurred=False,
            )

        if not invoke_adapter:
            return EffectBoundaryResult(
                binding_status=BindingStatus.CLEAN,
                tool_adapter_invoked=False,
                effect_attempted=False,
                effect_occurred=False,
            )

        before_state = observe_state()

        effect_attempted = bool(
            adapter.invoke(presented_operation)
        )

        after_state = observe_state()

        effect_occurred = (
            effect_attempted
            and before_state != after_state
        )

        return EffectBoundaryResult(
            binding_status=BindingStatus.CLEAN,
            tool_adapter_invoked=True,
            effect_attempted=effect_attempted,
            effect_occurred=effect_occurred,
        )
