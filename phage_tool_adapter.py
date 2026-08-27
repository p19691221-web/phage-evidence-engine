#!/usr/bin/env python3
"""
PHAGE low-risk observable tool adapter.

The adapter creates an observable effect only when it is
actually invoked through the governed execution boundary.
"""

from dataclasses import dataclass
from phage_gateway import ActionEnvelope


@dataclass
class SandboxEffect:
    invoked: bool = False
    action: str | None = None
    target: str | None = None


class SandboxToolAdapter:
    def __init__(self) -> None:
        self.effect = SandboxEffect()

    def invoke(self, envelope: ActionEnvelope) -> str:
        self.effect.invoked = True
        self.effect.action = envelope.action
        self.effect.target = envelope.target

        return f"effect:{envelope.action}:{envelope.target}"
