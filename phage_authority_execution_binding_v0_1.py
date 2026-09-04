from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional


class BindingStatus(str, Enum):
    CLEAN = "CLEAN"
    BINDING_UNRESOLVED = "BINDING_UNRESOLVED"
    BOUND_OPERATION_MISMATCH = "BOUND_OPERATION_MISMATCH"
    BOUND_GRANT_MISMATCH = "BOUND_GRANT_MISMATCH"


class EffectDisposition(str, Enum):
    EFFECT_PATH_ELIGIBLE = "EFFECT_PATH_ELIGIBLE"
    NOT_EXECUTED = "NOT_EXECUTED"


@dataclass(frozen=True)
class ExecutionBinding:
    decision_id: str
    subject_id: str
    action: str
    target: str
    grant_id: Optional[str]
    decision_time: datetime


@dataclass(frozen=True)
class BindingResult:
    status: BindingStatus
    effect_disposition: EffectDisposition


class BindingValidator:
    def check(
        self,
        *,
        binding: Optional[ExecutionBinding],
        subject_id: str,
        action: str,
        target: str,
        grant_id: Optional[str],
    ) -> BindingResult:
        if binding is None:
            return BindingResult(
                status=BindingStatus.BINDING_UNRESOLVED,
                effect_disposition=EffectDisposition.NOT_EXECUTED,
            )

        if (
            not binding.decision_id
            or not binding.subject_id
            or not binding.action
            or not binding.target
            or not binding.grant_id
            or not grant_id
        ):
            return BindingResult(
                status=BindingStatus.BINDING_UNRESOLVED,
                effect_disposition=EffectDisposition.NOT_EXECUTED,
            )

        if (
            binding.subject_id != subject_id
            or binding.action != action
            or binding.target != target
        ):
            return BindingResult(
                status=BindingStatus.BOUND_OPERATION_MISMATCH,
                effect_disposition=EffectDisposition.NOT_EXECUTED,
            )

        if binding.grant_id != grant_id:
            return BindingResult(
                status=BindingStatus.BOUND_GRANT_MISMATCH,
                effect_disposition=EffectDisposition.NOT_EXECUTED,
            )

        return BindingResult(
            status=BindingStatus.CLEAN,
            effect_disposition=EffectDisposition.EFFECT_PATH_ELIGIBLE,
        )
