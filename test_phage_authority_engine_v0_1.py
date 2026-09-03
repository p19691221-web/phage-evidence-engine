from datetime import datetime, timezone

from phage_authority_engine_v0_1 import (
    AuthorityGrant,
    AuthorityStatus,
    AuthorityValidator,
)


def utc(hour, minute=0):
    return datetime(2026, 9, 3, hour, minute, tzinfo=timezone.utc)


def make_grant(
    *,
    grant_id="G-001",
    subject_id="agent-A",
    issuer_id="authority-service",
    authorized_actions=frozenset({"READ"}),
    authorized_targets=frozenset({"record-123"}),
    issued_at=utc(9, 0),
    expires_at=utc(12, 0),
    revoked=False,
    revoked_at=None,
    source_ref="policy-record-17",
):
    return AuthorityGrant(
        grant_id=grant_id,
        subject_id=subject_id,
        issuer_id=issuer_id,
        authorized_actions=authorized_actions,
        authorized_targets=authorized_targets,
        issued_at=issued_at,
        expires_at=expires_at,
        revoked=revoked,
        revoked_at=revoked_at,
        source_ref=source_ref,
    )


def test_a_explicit_valid_authority():
    validator = AuthorityValidator()
    grant = make_grant()

    result = validator.check(
        grant=grant,
        subject_id="agent-A",
        action="READ",
        target="record-123",
        at=utc(10, 0),
    )

    assert result.status == AuthorityStatus.CLEAN
    print("PASS: test_a_explicit_valid_authority")


def test_b_missing_authority_source():
    validator = AuthorityValidator()
    grant = make_grant(source_ref=None)

    result = validator.check(
        grant=grant,
        subject_id="agent-A",
        action="READ",
        target="record-123",
        at=utc(10, 0),
    )

    assert result.status == AuthorityStatus.AUTHORITY_UNRESOLVED
    print("PASS: test_b_missing_authority_source")


def test_c_scope_mismatch():
    validator = AuthorityValidator()
    grant = make_grant()

    result = validator.check(
        grant=grant,
        subject_id="agent-A",
        action="DELETE",
        target="record-123",
        at=utc(10, 0),
    )

    assert result.status == AuthorityStatus.AUTHORITY_SCOPE_VIOLATION
    print("PASS: test_c_scope_mismatch")


def test_d_revoked_authority():
    validator = AuthorityValidator()
    grant = make_grant(
        revoked=True,
        revoked_at=utc(9, 30),
    )

    result = validator.check(
        grant=grant,
        subject_id="agent-A",
        action="READ",
        target="record-123",
        at=utc(10, 0),
    )

    assert result.status == AuthorityStatus.AUTHORITY_REVOKED
    print("PASS: test_d_revoked_authority")


def test_e_expired_authority():
    validator = AuthorityValidator()
    grant = make_grant(expires_at=utc(10, 0))

    result = validator.check(
        grant=grant,
        subject_id="agent-A",
        action="READ",
        target="record-123",
        at=utc(10, 1),
    )

    assert result.status == AuthorityStatus.AUTHORITY_EXPIRED
    print("PASS: test_e_expired_authority")


def test_f_midflight_authority_revocation_blocks_effect():
    validator = AuthorityValidator()

    active_grant = make_grant()

    gateway_result = validator.check(
        grant=active_grant,
        subject_id="agent-A",
        action="READ",
        target="record-123",
        at=utc(10, 0),
    )

    assert gateway_result.status == AuthorityStatus.CLEAN

    revoked_grant = make_grant(
        revoked=True,
        revoked_at=utc(10, 1),
    )

    effect_executed = False

    effect_time_result = validator.check(
        grant=revoked_grant,
        subject_id="agent-A",
        action="READ",
        target="record-123",
        at=utc(10, 2),
    )

    if effect_time_result.status == AuthorityStatus.CLEAN:
        effect_executed = True

    assert effect_time_result.status == AuthorityStatus.AUTHORITY_REVOKED
    assert effect_executed is False

    print("PASS: test_f_midflight_authority_revocation_blocks_effect")


if __name__ == "__main__":
    tests = [
        test_a_explicit_valid_authority,
        test_b_missing_authority_source,
        test_c_scope_mismatch,
        test_d_revoked_authority,
        test_e_expired_authority,
        test_f_midflight_authority_revocation_blocks_effect,
    ]

    for test in tests:
        test()

    print("Authority Engine regression PASS: 6 / 6")
