"""Protected-use entry v0.1: the only entry that can cause a policy effect.

Frozen interface: PHAGE_AUTHORITY_LINEAGE_HHN_EXECUTABLE_INTERFACE_v0_2.md
§1, §2.1, §5.2, §6 (frozen by #97; errata #98). Rationale: #96 §3.

The entry re-resolves on every call and never accepts a prior result. The
consistency check happens inside the source's atomic `commit_if_epoch` step;
this module only supplies the bound arguments and classifies the outcome.
"""
import phage_authority_lineage_hhn_v0_2 as _resolver

_RETURN_KEYS = frozenset({'outcome', 'committed_epoch'})
_OUTCOMES = frozenset({'COMMITTED', 'EPOCH_MISMATCH', 'NOT_CURRENT', 'TIME_REGRESSION'})


def _result(status, reason, effect_path, binding=None, epoch=None):
    return dict(commit_status=status, reason=reason, effect_path=effect_path,
                request_binding=binding, committed_epoch=epoch)


def _commit_error():
    return _result('COMMIT_ERROR', 'AUTHORITY_VERIFICATION_ERROR', 'BLOCKED')


def _unknown():
    return _result('COMMIT_OUTCOME_UNKNOWN', 'COMMIT_OUTCOME_UNKNOWN', 'NOT_DETERMINED')


def _classify(raw, expected_epoch):
    """Validate a seam return under §2.1 / §7.2 S-4. None means malformed."""
    if type(raw) is not dict or len(raw) != 2:
        return None
    for key in dict.keys(raw):            # whole-dict key gate before keyed access
        if type(key) is not str:
            return None
    if set(raw) != _RETURN_KEYS:
        return None
    outcome, epoch = raw['outcome'], raw['committed_epoch']
    if type(outcome) is not str or outcome not in _OUTCOMES:
        return None
    if outcome == 'COMMITTED':
        if type(epoch) is not int or epoch <= expected_epoch:
            return None
    elif epoch is not None:
        return None
    return outcome, epoch


def commit_policy_change(*, request, authenticate, snapshot_provider,
                         current_epoch, verify_grant, commit_if_epoch):
    """Use-time entry (§1, §5.2)."""
    _resolver._check_api(request, (authenticate, snapshot_provider, current_epoch,
                                   verify_grant, commit_if_epoch))
    resolved = _resolver._resolve(request, authenticate, snapshot_provider,
                                  current_epoch, verify_grant)
    status = resolved['authorization_status']
    if status == 'VERIFICATION_ERROR':
        return _commit_error()
    if status != 'AUTHORIZED':
        return _result('NOT_COMMITTED', resolved['reason'], 'BLOCKED')
    expected_epoch = resolved['state_epoch']
    snapshot_at = resolved['snapshot_at']
    valid_until = resolved['valid_until']
    binding = resolved['request_binding']
    if not snapshot_at < valid_until:      # pre-seam guard; unreachable (§5.2)
        return _commit_error()
    try:
        raw = commit_if_epoch(expected_epoch=expected_epoch, snapshot_at=snapshot_at,
                              valid_until=valid_until, binding=binding)
    except Exception:
        return _unknown()
    try:
        classified = _classify(raw, expected_epoch)
    except Exception:
        return _unknown()
    if classified is None:
        return _unknown()
    outcome, epoch = classified
    if outcome == 'COMMITTED':
        return _result('COMMITTED', 'POLICY_CHANGE_COMMITTED', 'EFFECT_APPLIED',
                       binding, epoch)
    if outcome == 'EPOCH_MISMATCH':
        return _result('NOT_COMMITTED', 'AUTHORITY_STATE_CHANGED', 'BLOCKED')
    if outcome == 'NOT_CURRENT':
        return _result('NOT_COMMITTED', 'AUTHORITY_NOT_CURRENT', 'BLOCKED')
    return _commit_error()                 # TIME_REGRESSION
