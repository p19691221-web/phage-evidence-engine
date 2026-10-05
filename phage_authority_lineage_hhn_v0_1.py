"""RED baseline stub; no authority resolution implemented."""

def resolve_policy_change(*, request, authenticate, snapshot_provider, verify_grant):
    return {
        "authorization_status": "UNVERIFIED",
        "reason": "AUTHORITY_UNRESOLVED",
        "effect_path": "BLOCKED",
        "request_binding": None,
        "snapshot_id": None,
    }
