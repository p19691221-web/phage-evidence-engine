from phage_authority_engine_v0_1 import AuthorityStatus

from phage_authority_execution_binding_v0_1 import (
    BindingStatus,
    EffectDisposition,
)

from phage_authority_execution_integration_v0_1 import IntegrationResult

from phage_authority_tool_adapter_effect_boundary_v0_1 import (
    BoundOperation,
    EffectBoundaryHarness,
)


class SyntheticToolAdapter:
    def __init__(self, state, mode):
        self.state = state
        self.mode = mode
        self.invocation_count = 0

    def invoke(self, operation):
        self.invocation_count += 1

        if self.mode == "not_attempted":
            return False

        if self.mode == "effect":
            self.state["value"] = 1
            return True

        if self.mode == "no_effect":
            return True

        raise ValueError(f"unknown mode: {self.mode}")


def eligible_result():
    return IntegrationResult(
        binding_status=BindingStatus.CLEAN,
        authority_status=AuthorityStatus.CLEAN,
        tool_adapter_permitted=True,
        effect_disposition=EffectDisposition.EFFECT_PATH_ELIGIBLE,
    )


def ineligible_result():
    return IntegrationResult(
        binding_status=None,
        authority_status=None,
        tool_adapter_permitted=False,
        effect_disposition=EffectDisposition.NOT_EXECUTED,
    )


def bound_operation(action="READ"):
    return BoundOperation(
        subject_id="agent-A",
        action=action,
        target="record-123",
        grant_id="G-001",
    )


def test_a_eligible_invocation_produces_observed_effect():
    state = {"value": 0}
    adapter = SyntheticToolAdapter(state, mode="effect")
    harness = EffectBoundaryHarness()

    result = harness.evaluate(
        integration_result=eligible_result(),
        bound_operation=bound_operation(),
        presented_operation=bound_operation(),
        adapter=adapter,
        observe_state=lambda: state["value"],
        invoke_adapter=True,
    )

    assert adapter.invocation_count == 1
    assert result.binding_status == BindingStatus.CLEAN
    assert result.tool_adapter_invoked is True
    assert result.effect_attempted is True
    assert result.effect_occurred is True
    assert state["value"] == 1

    print("PASS: test_a_eligible_invocation_produces_observed_effect")


def test_b_ineligible_upstream_path_never_invokes_adapter():
    state = {"value": 0}
    adapter = SyntheticToolAdapter(state, mode="effect")
    harness = EffectBoundaryHarness()

    before_state = state["value"]

    result = harness.evaluate(
        integration_result=ineligible_result(),
        bound_operation=bound_operation(),
        presented_operation=bound_operation(),
        adapter=adapter,
        observe_state=lambda: state["value"],
        invoke_adapter=True,
    )

    after_state = state["value"]

    assert adapter.invocation_count == 0
    assert result.tool_adapter_invoked is False
    assert result.effect_attempted is False
    assert result.effect_occurred is False
    assert before_state == after_state

    print("PASS: test_b_ineligible_upstream_path_never_invokes_adapter")


def test_c_bound_operation_changes_before_adapter_invocation():
    state = {"value": 0}
    adapter = SyntheticToolAdapter(state, mode="effect")
    harness = EffectBoundaryHarness()

    before_state = state["value"]

    result = harness.evaluate(
        integration_result=eligible_result(),
        bound_operation=bound_operation(action="READ"),
        presented_operation=bound_operation(action="DELETE"),
        adapter=adapter,
        observe_state=lambda: state["value"],
        invoke_adapter=True,
    )

    after_state = state["value"]

    assert result.binding_status == BindingStatus.BOUND_OPERATION_MISMATCH
    assert adapter.invocation_count == 0
    assert result.tool_adapter_invoked is False
    assert result.effect_attempted is False
    assert result.effect_occurred is False
    assert before_state == after_state

    print("PASS: test_c_bound_operation_changes_before_adapter_invocation")


def test_d_eligible_path_but_adapter_invocation_does_not_occur():
    state = {"value": 0}
    adapter = SyntheticToolAdapter(state, mode="effect")
    harness = EffectBoundaryHarness()

    before_state = state["value"]

    result = harness.evaluate(
        integration_result=eligible_result(),
        bound_operation=bound_operation(),
        presented_operation=bound_operation(),
        adapter=adapter,
        observe_state=lambda: state["value"],
        invoke_adapter=False,
    )

    after_state = state["value"]

    assert adapter.invocation_count == 0
    assert result.tool_adapter_invoked is False
    assert result.effect_attempted is False
    assert result.effect_occurred is False
    assert before_state == after_state

    print("PASS: test_d_eligible_path_but_adapter_invocation_does_not_occur")


def test_e_adapter_invoked_but_no_effect_attempt_occurs():
    state = {"value": 0}
    adapter = SyntheticToolAdapter(state, mode="not_attempted")
    harness = EffectBoundaryHarness()

    before_state = state["value"]

    result = harness.evaluate(
        integration_result=eligible_result(),
        bound_operation=bound_operation(),
        presented_operation=bound_operation(),
        adapter=adapter,
        observe_state=lambda: state["value"],
        invoke_adapter=True,
    )

    after_state = state["value"]

    assert adapter.invocation_count == 1
    assert result.tool_adapter_invoked is True
    assert result.effect_attempted is False
    assert result.effect_occurred is False
    assert before_state == after_state

    print("PASS: test_e_adapter_invoked_but_no_effect_attempt_occurs")


def test_f_effect_attempted_but_no_effect_is_observed():
    state = {"value": 0}
    adapter = SyntheticToolAdapter(state, mode="no_effect")
    harness = EffectBoundaryHarness()

    before_state = state["value"]

    result = harness.evaluate(
        integration_result=eligible_result(),
        bound_operation=bound_operation(),
        presented_operation=bound_operation(),
        adapter=adapter,
        observe_state=lambda: state["value"],
        invoke_adapter=True,
    )

    after_state = state["value"]

    assert adapter.invocation_count == 1
    assert result.tool_adapter_invoked is True
    assert result.effect_attempted is True
    assert result.effect_occurred is False
    assert before_state == after_state

    print("PASS: test_f_effect_attempted_but_no_effect_is_observed")


if __name__ == "__main__":
    tests = [
        test_a_eligible_invocation_produces_observed_effect,
        test_b_ineligible_upstream_path_never_invokes_adapter,
        test_c_bound_operation_changes_before_adapter_invocation,
        test_d_eligible_path_but_adapter_invocation_does_not_occur,
        test_e_adapter_invoked_but_no_effect_attempt_occurs,
        test_f_effect_attempted_but_no_effect_is_observed,
    ]

    for test in tests:
        test()

    print(
        "Authority-to-Tool-Adapter Effect Boundary regression PASS: 6 / 6"
    )
