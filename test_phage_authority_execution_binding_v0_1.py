from datetime import datetime, timezone

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


def utc(hour, minute=0):
    return datetime(2026, 9, 4, hour, minute, tzinfo=timezone.utc)


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


def test_a_matching_binding_and_valid_authority():
    binding_validator = BindingValidator()
    authority_validator = AuthorityValidator()

    binding = make_binding()
    grant = make_grant()

    binding_result = binding_validator.check(
        binding=binding,
        subject_id="agent-A",
        action="READ",
        target="record-123",
        grant_id="G-001",
    )

    authority_result = authority_validator.check(
        grant=grant,
        subject_id="agent-A",
        action="READ",
        target="record-123",
        at=utc(10, 1),
    )

    assert binding_result.status == BindingStatus.CLEAN
    assert binding_result.effect_disposition == EffectDisposition.EFFECT_PATH_ELIGIBLE
    assert authority_result.status == AuthorityStatus.CLEAN

    print("PASS: test_a_matching_binding_and_valid_authority")


def test_b_missing_binding_context():
    validator = BindingValidator()

    binding = make_binding(grant_id=None)

    result = validator.check(
        binding=binding,
        subject_id="agent-A",
        action="READ",
        target="record-123",
        grant_id=None,
    )

    assert result.status == BindingStatus.BINDING_UNRESOLVED
    assert result.effect_disposition == EffectDisposition.NOT_EXECUTED

    print("PASS: test_b_missing_binding_context")


def test_c_bound_operation_mismatch():
    validator = BindingValidator()

    binding = make_binding()

    result = validator.check(
        binding=binding,
        subject_id="agent-A",
        action="DELETE",
        target="record-123",
        grant_id="G-001",
    )

    assert result.status == BindingStatus.BOUND_OPERATION_MISMATCH
    assert result.effect_disposition == EffectDisposition.NOT_EXECUTED

    print("PASS: test_c_bound_operation_mismatch")


def test_d_substitute_grant_with_equivalent_scope():
    validator = BindingValidator()

    binding = make_binding(grant_id="G-001")

    result = validator.check(
        binding=binding,
        subject_id="agent-A",
        action="READ",
        target="record-123",
        grant_id="G-002",
    )

    assert result.status == BindingStatus.BOUND_GRANT_MISMATCH
    assert result.effect_disposition == EffectDisposition.NOT_EXECUTED

    print("PASS: test_d_substitute_grant_with_equivalent_scope")


def test_e_bound_grant_revoked_after_gateway_allow():
    binding_validator = BindingValidator()
    authority_validator = AuthorityValidator()

    binding = make_binding()

    active_grant = make_grant()

    decision_time_authority = authority_validator.check(
        grant=active_grant,
        subject_id="agent-A",
        action="READ",
        target="record-123",
        at=utc(10, 0),
    )

    assert decision_time_authority.status == AuthorityStatus.CLEAN

    revoked_grant = make_grant(
        revoked=True,
        revoked_at=utc(10, 1),
    )

    binding_result = binding_validator.check(
        binding=binding,
        subject_id="agent-A",
        action="READ",
        target="record-123",
        grant_id="G-001",
    )

    effect_time_authority = authority_validator.check(
        grant=revoked_grant,
        subject_id="agent-A",
        action="READ",
        target="record-123",
        at=utc(10, 2),
    )

    effect_executed = (
        binding_result.status == BindingStatus.CLEAN
        and effect_time_authority.status == AuthorityStatus.CLEAN
    )

    assert binding_result.status == BindingStatus.CLEAN
    assert effect_time_authority.status == AuthorityStatus.AUTHORITY_REVOKED
    assert effect_executed is False

    print("PASS: test_e_bound_grant_revoked_after_gateway_allow")


if __name__ == "__main__":
    tests = [
        test_a_matching_binding_and_valid_authority,
        test_b_missing_binding_context,
        test_c_bound_operation_mismatch,
        test_d_substitute_grant_with_equivalent_scope,
        test_e_bound_grant_revoked_after_gateway_allow,
    ]

    for test in tests:
        test()

    print("Authority-to-Execution Binding regression PASS: 5 / 5")
