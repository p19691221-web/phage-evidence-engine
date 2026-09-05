from datetime import datetime, timezone

from phage_authority_engine_v0_1 import (
    AuthorityGrant,
    AuthorityStatus,
)

from phage_authority_execution_binding_v0_1 import (
    BindingStatus,
    EffectDisposition,
    ExecutionBinding,
)

from phage_authority_execution_integration_v0_1 import (
    AuthorityExecutionIntegrator,
)


def utc(hour, minute=0):
    return datetime(2026, 9, 5, hour, minute, tzinfo=timezone.utc)


def make_binding(
    *,
    decision_id="D-001",
    subject_id="agent-A",
    action="READ",
    target="record-123",
    grant_id="G-001",
):
    return ExecutionBinding(
        decision_id=decision_id,
        subject_id=subject_id,
        action=action,
        target=target,
        grant_id=grant_id,
        decision_time=utc(10, 0),
    )


def make_grant(
    *,
    grant_id="G-001",
    subject_id="agent-A",
    authorized_actions=frozenset({"READ"}),
    authorized_targets=frozenset({"record-123"}),
    revoked=False,
    revoked_at=None,
):
    return AuthorityGrant(
        grant_id=grant_id,
        subject_id=subject_id,
        issuer_id="authority-service",
        authorized_actions=authorized_actions,
        authorized_targets=authorized_targets,
        issued_at=utc(9, 0),
        expires_at=utc(12, 0),
        revoked=revoked,
        revoked_at=revoked_at,
        source_ref="policy-record-17",
    )


def test_a_clean_integrated_path():
    integrator = AuthorityExecutionIntegrator()

    result = integrator.evaluate(
        gateway_decision="ALLOW",
        binding=make_binding(),
        grant=make_grant(),
        subject_id="agent-A",
        action="READ",
        target="record-123",
        grant_id="G-001",
        at=utc(10, 1),
    )

    assert result.binding_status == BindingStatus.CLEAN
    assert result.authority_status == AuthorityStatus.CLEAN
    assert result.tool_adapter_permitted is True
    assert result.effect_disposition == EffectDisposition.EFFECT_PATH_ELIGIBLE

    print("PASS: test_a_clean_integrated_path")


def test_b_gateway_block_stops_chain():
    integrator = AuthorityExecutionIntegrator()

    result = integrator.evaluate(
        gateway_decision="BLOCK",
        binding=make_binding(),
        grant=make_grant(),
        subject_id="agent-A",
        action="READ",
        target="record-123",
        grant_id="G-001",
        at=utc(10, 1),
    )

    assert result.tool_adapter_permitted is False
    assert result.effect_disposition == EffectDisposition.NOT_EXECUTED
    assert result.binding_status is None
    assert result.authority_status is None

    print("PASS: test_b_gateway_block_stops_chain")


def test_c_gateway_allow_with_missing_binding():
    integrator = AuthorityExecutionIntegrator()

    result = integrator.evaluate(
        gateway_decision="ALLOW",
        binding=None,
        grant=make_grant(),
        subject_id="agent-A",
        action="READ",
        target="record-123",
        grant_id="G-001",
        at=utc(10, 1),
    )

    assert result.binding_status == BindingStatus.BINDING_UNRESOLVED
    assert result.authority_status is None
    assert result.tool_adapter_permitted is False
    assert result.effect_disposition == EffectDisposition.NOT_EXECUTED

    print("PASS: test_c_gateway_allow_with_missing_binding")


def test_d_gateway_allow_with_changed_bound_operation():
    integrator = AuthorityExecutionIntegrator()

    result = integrator.evaluate(
        gateway_decision="ALLOW",
        binding=make_binding(
            action="READ",
        ),
        grant=make_grant(),
        subject_id="agent-A",
        action="DELETE",
        target="record-123",
        grant_id="G-001",
        at=utc(10, 1),
    )

    assert result.binding_status == BindingStatus.BOUND_OPERATION_MISMATCH
    assert result.authority_status is None
    assert result.tool_adapter_permitted is False
    assert result.effect_disposition == EffectDisposition.NOT_EXECUTED

    print("PASS: test_d_gateway_allow_with_changed_bound_operation")


def test_e_authority_revoked_after_clean_gateway_and_binding():
    integrator = AuthorityExecutionIntegrator()

    revoked_grant = make_grant(
        revoked=True,
        revoked_at=utc(10, 1),
    )

    result = integrator.evaluate(
        gateway_decision="ALLOW",
        binding=make_binding(),
        grant=revoked_grant,
        subject_id="agent-A",
        action="READ",
        target="record-123",
        grant_id="G-001",
        at=utc(10, 2),
    )

    assert result.binding_status == BindingStatus.CLEAN
    assert result.authority_status == AuthorityStatus.AUTHORITY_REVOKED
    assert result.tool_adapter_permitted is False
    assert result.effect_disposition == EffectDisposition.NOT_EXECUTED

    print(
        "PASS: test_e_authority_revoked_after_clean_gateway_and_binding"
    )


if __name__ == "__main__":
    tests = [
        test_a_clean_integrated_path,
        test_b_gateway_block_stops_chain,
        test_c_gateway_allow_with_missing_binding,
        test_d_gateway_allow_with_changed_bound_operation,
        test_e_authority_revoked_after_clean_gateway_and_binding,
    ]

    for test in tests:
        test()

    print("Authority-to-Execution Integration regression PASS: 5 / 5")
