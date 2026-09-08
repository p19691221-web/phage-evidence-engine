"""
Minimal PHAGE Principle 0 Emergency Override implementation v0.1.

This module implements only the frozen executable regression boundary A-F,
including F1 revocation and F2 expiration.

It does not implement a production emergency declaration system, production
policy engine, Gateway, Tool Adapter, root Authority model, or production
execution system.
"""

from phage_authority_engine_v0_1 import AuthorityStatus


OVERRIDE_APPLICABLE = "OVERRIDE_APPLICABLE"
OVERRIDE_NOT_APPLICABLE = "OVERRIDE_NOT_APPLICABLE"
OVERRIDE_UNRESOLVED = "OVERRIDE_UNRESOLVED"

BLOCKED = "BLOCKED"
NOT_DETERMINED = "NOT_DETERMINED"


def _status_name(value) -> str:
    if value is None:
        return "NONE"

    if hasattr(value, "name"):
        return value.name

    return str(value)


def _result(
    *,
    schedule_status,
    override_status,
    authority_status,
    effect_path,
) -> dict:
    return {
        "schedule_status": schedule_status,
        "override_status": override_status,
        "authority_status": authority_status,
        "effect_path": effect_path,
    }
def evaluate_override(
    *,
    request: dict,
    override_grant: dict | None,
) -> dict:
    schedule_status = request.get("schedule_status")
    ordinary_authority_status = request.get(
        "ordinary_authority_status"
    )
    at = request.get("at")

    if schedule_status == "SCHEDULE_UNRESOLVED":
        return _result(
            schedule_status=schedule_status,
            override_status=OVERRIDE_UNRESOLVED,
            authority_status=ordinary_authority_status,
            effect_path=BLOCKED,
        )

    if schedule_status != "SCHEDULE_NO_MATCH":
        return _result(
            schedule_status=schedule_status,
            override_status=OVERRIDE_NOT_APPLICABLE,
            authority_status=ordinary_authority_status,
            effect_path=NOT_DETERMINED,
        )

    if override_grant is None:
        return _result(
            schedule_status=schedule_status,
            override_status=OVERRIDE_UNRESOLVED,
            authority_status=AuthorityStatus.AUTHORITY_UNRESOLVED,
            effect_path=BLOCKED,
        )

    if (
        not override_grant.get("issuer_id")
        or not override_grant.get("source_ref")
    ):
        return _result(
            schedule_status=schedule_status,
            override_status=OVERRIDE_UNRESOLVED,
            authority_status=AuthorityStatus.AUTHORITY_UNRESOLVED,
            effect_path=BLOCKED,
        )
    ordinary_authority_name = _status_name(
        ordinary_authority_status
        )            

    if ordinary_authority_name != "CLEAN":
        return _result(
            schedule_status=schedule_status,
            override_status=OVERRIDE_NOT_APPLICABLE,
            authority_status=ordinary_authority_status,
            effect_path=BLOCKED,
        )

    if override_grant.get("revoked") is True:
        return _result(
            schedule_status=schedule_status,
            override_status=OVERRIDE_NOT_APPLICABLE,
            authority_status=AuthorityStatus.AUTHORITY_REVOKED,
            effect_path=BLOCKED,
        )

    expires_at = override_grant.get("expires_at")

    if at is None or expires_at is None:
        return _result(
            schedule_status=schedule_status,
            override_status=OVERRIDE_UNRESOLVED,
            authority_status=AuthorityStatus.AUTHORITY_UNRESOLVED,
            effect_path=BLOCKED,
        )

    if at >= expires_at:
        return _result(
            schedule_status=schedule_status,
            override_status=OVERRIDE_NOT_APPLICABLE,
            authority_status=AuthorityStatus.AUTHORITY_EXPIRED,
            effect_path=BLOCKED,
  )
    required_scope_fields = (
        "subject_id",
        "authorized_action",
        "authorized_target",
    )

    if any(
        override_grant.get(field) is None
        for field in required_scope_fields
    ):
        return _result(
            schedule_status=schedule_status,
            override_status=OVERRIDE_UNRESOLVED,
            authority_status=AuthorityStatus.AUTHORITY_UNRESOLVED,
            effect_path=BLOCKED,
        )

    if (
        request.get("subject_id") != override_grant.get("subject_id")
        or request.get("action") != override_grant.get("authorized_action")
        or request.get("target") != override_grant.get("authorized_target")
    ):
        return _result(
            schedule_status=schedule_status,
            override_status=OVERRIDE_NOT_APPLICABLE,
            authority_status=AuthorityStatus.AUTHORITY_SCOPE_VIOLATION,
            effect_path=BLOCKED,
        )

    schedule_ref = override_grant.get("schedule_ref")
    request_schedule_ref = request.get("schedule_ref")

    if (
        not schedule_ref
        or not request_schedule_ref
        or not override_grant.get("emergency_ref")
    ):
        return _result(
            schedule_status=schedule_status,
            override_status=OVERRIDE_UNRESOLVED,
            authority_status=ordinary_authority_status,
            effect_path=BLOCKED,
        )

    if schedule_ref != request_schedule_ref:
        return _result(
            schedule_status=schedule_status,
            override_status=OVERRIDE_NOT_APPLICABLE,
            authority_status=ordinary_authority_status,
            effect_path=BLOCKED,
        )

    mismatch_dimension = request.get("mismatch_dimension")
    override_dimensions = override_grant.get("override_dimensions")

    if mismatch_dimension is None or not override_dimensions:
        return _result(
            schedule_status=schedule_status,
            override_status=OVERRIDE_UNRESOLVED,
            authority_status=ordinary_authority_status,
            effect_path=BLOCKED,
        )

    if mismatch_dimension not in override_dimensions:
        return _result(
            schedule_status=schedule_status,
            override_status=OVERRIDE_NOT_APPLICABLE,
            authority_status=ordinary_authority_status,
            effect_path=BLOCKED,
        )

        return _result(
            schedule_status=schedule_status,
            override_status=OVERRIDE_APPLICABLE,
            authority_status=ordinary_authority_status,
            effect_path=NOT_DETERMINED,
        )
