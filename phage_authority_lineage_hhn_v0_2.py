"""H/H'/N inspection entry v0.2 — STUB for semantic RED.

Frozen interface: PHAGE_AUTHORITY_LINEAGE_HHN_EXECUTABLE_INTERFACE_v0_2.md.
This stub fixes signatures and constants only and fails closed on every call.
It is replaced by the implementation in the next commit.
"""

REQUEST_MAX_KEYS = 16
REQUEST_MAX_STRING_CHARS = 256
SNAPSHOT_MAX_GRANTS = 1024
SNAPSHOT_MAX_ROOTS = 64
SNAPSHOT_MAX_RECORD_KEYS = 32
SNAPSHOT_MAX_SCOPE_ITEMS = 64
SNAPSHOT_MAX_STRING_CHARS = 256
SNAPSHOT_MAX_INT_BITS = 64
SNAPSHOT_MAX_VISITS = 65536


def resolve_policy_change(*, request, authenticate, snapshot_provider,
                          current_epoch, verify_grant):
    if type(request) is not dict or not all(callable(seam) for seam in (
            authenticate, snapshot_provider, current_epoch, verify_grant)):
        raise TypeError('plain request dict and callable seams required')
    return dict(authorization_status='VERIFICATION_ERROR',
                reason='AUTHORITY_VERIFICATION_ERROR', effect_path='BLOCKED',
                request_binding=None, snapshot_id=None, state_epoch=None,
                snapshot_at=None, valid_until=None)
