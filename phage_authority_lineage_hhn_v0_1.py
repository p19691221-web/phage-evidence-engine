"""Isolated fixture authority resolution under the PR #92 frozen contract.

Trusted seams model authentication, coherent state and record acceptance.
AUTHORIZED is an inspection result, never an operational application permit.
"""
from copy import deepcopy

_FIELDS = ('requester_id', 'policy_id', 'expected_revision', 'expected_digest',
           'proposed_revision', 'proposed_digest', 'operation', 'leaf_grant_id')
_GRANT = ('id', 'revision', 'digest', 'subject', 'issuer', 'parent_id',
          'operations', 'targets', 'not_before', 'expires_at', 'revoked', 'can_delegate')


def _string(value):
    return type(value) is str and bool(value)


def _target(value):
    return _string(value) and '*' not in value and '?' not in value


def _strings(value, predicate):
    return (type(value) is list and all(predicate(item) for item in value)
            and len(set(value)) == len(value))


def _result(reason):
    return dict(authorization_status=('VERIFICATION_ERROR' if
                reason == 'AUTHORITY_VERIFICATION_ERROR' else 'UNVERIFIED'),
                reason=reason, effect_path='BLOCKED', request_binding=None,
                snapshot_id=None)


def _preflight(state):
    """Scan all structures; malformed wins over missing, without authority use."""
    malformed = False
    missing = False

    def shape(record, fields, predicates):
        nonlocal malformed, missing
        if type(record) is not dict:
            malformed = True
            return False
        malformed |= bool(set(record) - set(fields))
        missing |= bool(set(fields) - set(record))
        for field, predicate in predicates.items():
            if field in record and not predicate(record[field]):
                malformed = True
        return True

    if not shape(state, ('snapshot_id', 'policy', 'grants', 'roots', 'at', 'max_grants'),
                 dict(snapshot_id=_string, at=lambda x: type(x) is int,
                      max_grants=lambda x: type(x) is int and x > 0)):
        return 'INVALID_AUTHORITY_INPUT'
    if 'policy' in state:
        shape(state['policy'], ('policy_id', 'revision', 'digest', 'mutable_by_policy_change'),
              dict(policy_id=_target, revision=_string, digest=_string,
                   mutable_by_policy_change=lambda x: type(x) is bool))
    if 'roots' in state:
        roots = state['roots']
        if type(roots) is not dict:
            malformed = True
        else:
            for identifier, anchor in roots.items():
                if not _string(identifier):
                    malformed = True
                shape(anchor, ('revision', 'digest'), dict(revision=_string, digest=_string))
    if 'grants' in state:
        records = state['grants']
        if type(records) is not list:
            malformed = True
        else:
            identifiers = set()
            for record in records:
                predicates = {key: _string for key in ('id', 'revision', 'digest', 'subject', 'issuer')}
                predicates.update(parent_id=lambda x: x is None or _string(x),
                    operations=lambda x: _strings(x, lambda op: type(op) is str and op == 'POLICY_CHANGE'),
                    targets=lambda x: _strings(x, _target),
                    not_before=lambda x: type(x) is int,
                    expires_at=lambda x: type(x) is int,
                    revoked=lambda x: x is None or type(x) is bool,
                    can_delegate=lambda x: type(x) is bool)
                if not shape(record, _GRANT, predicates):
                    continue
                identifier = record.get('id')
                if _string(identifier):
                    if identifier in identifiers:
                        malformed = True
                    identifiers.add(identifier)
                start, end = record.get('not_before'), record.get('expires_at')
                if type(start) is int and type(end) is int and start >= end:
                    malformed = True
    if malformed:
        return 'INVALID_AUTHORITY_INPUT'
    if missing:
        return 'AUTHORITY_UNRESOLVED'
    return None


def resolve_policy_change(*, request, authenticate, snapshot_provider, verify_grant):
    """Resolve once against private state; never call an application effect."""
    if type(request) is not dict or not all(callable(seam) for seam in
                                           (authenticate, snapshot_provider, verify_grant)):
        raise TypeError('plain request dict and callable seams required')
    if set(request) != set(_FIELDS) or not all(_string(request[key]) for key in _FIELDS):
        return _result('INVALID_AUTHORITY_INPUT')
    # Freeze request before external seams can change caller-owned references.
    bound = dict(request)
    try:
        authentication = authenticate(bound['requester_id'])
    except Exception:
        return _result('AUTHORITY_VERIFICATION_ERROR')
    if type(authentication) is not str:
        return _result('AUTHORITY_VERIFICATION_ERROR')
    if authentication == 'NOT_ESTABLISHED':
        return _result('AUTHENTICATION_NOT_ESTABLISHED')
    if authentication != 'ESTABLISHED':
        return _result('AUTHORITY_VERIFICATION_ERROR')
    try:
        supplied = snapshot_provider()
        if supplied is None:
            return _result('AUTHORITY_UNRESOLVED')
        state = deepcopy(supplied)
        error = _preflight(state)
        if error:
            return _result(error)
        return _resolve(bound, state, verify_grant)
    except Exception:
        # Provider, copy, verifier and internal faults are contained without details.
        return _result('AUTHORITY_VERIFICATION_ERROR')


def _resolve(request, state, verify_grant):
    policy = state['policy']
    if (request['policy_id'], request['expected_revision'], request['expected_digest']) != (
            policy['policy_id'], policy['revision'], policy['digest']):
        return _result('POLICY_STATE_MISMATCH')
    if not policy['mutable_by_policy_change'] or request['operation'] != 'POLICY_CHANGE':
        return _result('AUTHORITY_SCOPE_VIOLATION')
    records = {record['id']: record for record in state['grants']}
    seen = set()
    identifier = request['leaf_grant_id']
    child = None
    while True:
        if identifier in seen:
            return _result('AUTHORITY_CYCLE_DETECTED')
        if len(seen) >= state['max_grants']:
            return _result('AUTHORITY_LIMIT_EXCEEDED')
        seen.add(identifier)
        record = records.get(identifier)
        if record is None:
            return _result('AUTHORITY_UNRESOLVED')
        # A verifier receives another copy; mutations cannot rewrite resolution state.
        verification = verify_grant(deepcopy(record), state['at'])
        if type(verification) is not str:
            return _result('AUTHORITY_VERIFICATION_ERROR')
        if verification == 'UNVERIFIED':
            return _result('AUTHORITY_UNRESOLVED')
        if verification != 'VERIFIED':
            return _result('AUTHORITY_VERIFICATION_ERROR')
        if (child is None and record['subject'] != request['requester_id']) or (
                child is not None and child['issuer'] != record['subject']):
            return _result('AUTHORITY_SCOPE_VIOLATION')
        if request['operation'] not in record['operations'] or request['policy_id'] not in record['targets']:
            return _result('AUTHORITY_SCOPE_VIOLATION')
        if record['revoked'] is None:
            return _result('AUTHORITY_UNRESOLVED')
        if record['revoked']:
            return _result('AUTHORITY_REVOKED')
        if not record['not_before'] <= state['at'] < record['expires_at']:
            return _result('AUTHORITY_NOT_CURRENT')
        if child is not None:
            if (not record['can_delegate'] or
                    not set(child['operations']).issubset(record['operations']) or
                    not set(child['targets']).issubset(record['targets']) or
                    child['not_before'] < record['not_before'] or
                    child['expires_at'] > record['expires_at']):
                return _result('AUTHORITY_SCOPE_VIOLATION')
        if record['parent_id'] is None:
            anchor = state['roots'].get(identifier)
            if anchor is None or (anchor['revision'], anchor['digest']) != (record['revision'], record['digest']):
                return _result('AUTHORITY_UNRESOLVED')
            return dict(authorization_status='AUTHORIZED', reason='POLICY_CHANGE_AUTHORIZED',
                        effect_path='NOT_DETERMINED',
                        request_binding=tuple(request[key] for key in _FIELDS),
                        snapshot_id=state['snapshot_id'])
        child = record
        identifier = record['parent_id']
