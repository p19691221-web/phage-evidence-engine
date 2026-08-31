#!/usr/bin/env python3
"""
PHAGE low-risk observable tool adapter.

The adapter creates an observable effect only when it is
actually invoked through the governed execution boundary.
"""

from dataclasses import dataclass
from typing import Callable

from phage_gateway import ActionEnvelope


@dataclass
class SandboxEffect:
    invoked: bool = False
    action: str | None = None
    target: str | None = None


PreEffectGuard = Callable[[ActionEnvelope], tuple[bool, str]]


class SandboxToolAdapter:
    def __init__(
        self,
        pre_effect_guard: PreEffectGuard | None = None,
    ) -> None:
        self.effect = SandboxEffect()
        self._pre_effect_guard = pre_effect_guard

    def invoke(self, envelope: ActionEnvelope) -> str:
        if self._pre_effect_guard is not None:
            allowed, detail = self._pre_effect_guard(envelope)

            if not allowed:
                return f"BLOCKED: {detail}"

        self.effect.invoked = True
        self.effect.action = envelope.action
        self.effect.target = envelope.target

        return f"effect:{envelope.action}:{envelope.target}"
