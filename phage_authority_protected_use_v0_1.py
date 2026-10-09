"""Protected-use entry v0.1 — STUB for semantic RED.

Frozen interface: PHAGE_AUTHORITY_LINEAGE_HHN_EXECUTABLE_INTERFACE_v0_2.md §1, §2.1, §5.2.
This stub fixes the signature only and fails closed without calling any seam.
It is replaced by the implementation in the next commit.
"""


def commit_policy_change(*, request, authenticate, snapshot_provider,
                         current_epoch, verify_grant, commit_if_epoch):
    if type(request) is not dict or not all(callable(seam) for seam in (
            authenticate, snapshot_provider, current_epoch, verify_grant,
            commit_if_epoch)):
        raise TypeError('plain request dict and callable seams required')
    return dict(commit_status='COMMIT_ERROR', reason='AUTHORITY_VERIFICATION_ERROR',
                effect_path='BLOCKED', request_binding=None, committed_epoch=None)
