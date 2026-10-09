"""H/H'/N inspection entry v0.2.

Frozen interface: PHAGE_AUTHORITY_LINEAGE_HHN_EXECUTABLE_INTERFACE_v0_2.md
(frozen by #97; errata #98). Rationale: #96. Traversal semantics: #92/#93.

AUTHORIZED is an inspection record, never a consumable approval. Nothing here
writes to any state source. Section references are to the frozen interface.
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

FIELDS = ('requester_id', 'policy_id', 'expected_revision', 'expected_digest',
          'proposed_revision', 'proposed_digest', 'operation', 'leaf_grant_id')
_FIELD_SET = frozenset(FIELDS)
_SNAPSHOT = ('snapshot_id', 'policy', 'grants', 'roots', 'at', 'max_grants',
             'state_epoch')
_POLICY = ('policy_id', 'revision', 'digest', 'mutable_by_policy_change')
_ANCHOR = ('revision', 'digest')
_GRANT = ('id', 'revision', 'digest', 'subject', 'issuer', 'parent_id',
          'operations', 'targets', 'not_before', 'expires_at', 'revoked',
          'can_delegate')
_OPERATIONS = frozenset({'POLICY_CHANGE'})


# --- results (§5.1) ----------------------------------------------------------

def _denial(reason):
    status = ('VERIFICATION_ERROR' if reason == 'AUTHORITY_VERIFICATION_ERROR'
              else 'UNVERIFIED')
    return dict(authorization_status=status, reason=reason, effect_path='BLOCKED',
                request_binding=None, snapshot_id=None, state_epoch=None,
                snapshot_at=None, valid_until=None)


# --- scalar predicates (exact types only, §7.2 S-1/S-2) -------------------

def _string(value):
    return type(value) is str and bool(value)


def _target(value):
    return _string(value) and '*' not in value and '?' not in value


def _int(value):
    return type(value) is int


# --- stage 0-1: API and request scan (§6, §7.5) -----------------------------

def _check_api(request, seams):
    if type(request) is not dict or not all(callable(seam) for seam in seams):
        raise TypeError('plain request dict and callable seams required')


def _scan_request(request):
    """Return (reason, bound) with exactly one of them None."""
    if len(request) > REQUEST_MAX_KEYS:
        return 'REQUEST_LIMIT_EXCEEDED', None
    oversize = malformed = False
    for key, value in dict.items(request):
        if type(key) is str:
            oversize |= len(key) > REQUEST_MAX_STRING_CHARS
        else:
            malformed = True
        if type(value) is str:
            oversize |= len(value) > REQUEST_MAX_STRING_CHARS
        else:
            malformed = True
    if oversize:
        return 'REQUEST_LIMIT_EXCEEDED', None
    if malformed:
        return 'INVALID_AUTHORITY_INPUT', None
    # Every key and value is an exact str; keyed access is now safe (S-4).
    if set(request) != _FIELD_SET or not all(request[key] for key in FIELDS):
        return 'INVALID_AUTHORITY_INPUT', None
    if (request['proposed_revision'] == request['expected_revision'] and
            request['proposed_digest'] == request['expected_digest']):
        return 'INVALID_AUTHORITY_INPUT', None
    return None, {key: request[key] for key in FIELDS}


# --- stage 4: snapshot preflight (§7.2-7.4) ---------------------------------

class _SizeExceeded(Exception):
    """Internal: a reachable size cap was exceeded; scan stops (§7.4)."""


class _Preflight:
    def __init__(self):
        self.visits = 0
        self.malformed = False
        self.missing = False

    def charge(self):
        if self.visits >= SNAPSHOT_MAX_VISITS:
            raise _SizeExceeded()
        self.visits += 1

    def scalar_size(self, value):
        if type(value) is str:
            if len(value) > SNAPSHOT_MAX_STRING_CHARS:
                raise _SizeExceeded()
        elif type(value) is int:
            if value.bit_length() > SNAPSHOT_MAX_INT_BITS:
                raise _SizeExceeded()

    def enter_dict(self, record, cap):
        """Charge and gate an exact dict. Return True if keyed access is safe."""
        self.charge()
        if len(record) > cap:
            raise _SizeExceeded()
        gated = True
        for key in dict.keys(record):
            if type(key) is str:
                if len(key) > SNAPSHOT_MAX_STRING_CHARS:
                    raise _SizeExceeded()
            else:
                gated = False
        for _key, value in dict.items(record):
            self.charge()
            self.scalar_size(value)
        if not gated:
            self.malformed = True
        return gated

    def enter_list(self, values, cap):
        self.charge()
        if len(values) > cap:
            raise _SizeExceeded()
        for value in values:
            self.charge()
            self.scalar_size(value)

    def fields(self, record, names, scalars):
        """Field-set and scalar predicate checks on a gated dict."""
        present = set(record)
        if present - set(names):
            self.malformed = True
        if set(names) - present:
            self.missing = True
        for name, predicate in scalars.items():
            if name in present and not predicate(record[name]):
                self.malformed = True

    def scope(self, record, name, element):
        if name not in record:
            return
        values = record[name]
        if type(values) is not list:
            self.malformed = True
            return
        self.enter_list(values, SNAPSHOT_MAX_SCOPE_ITEMS)
        if not all(element(item) for item in values) or len(set(values)) != len(values):
            self.malformed = True

    def snapshot(self, state):
        if type(state) is not dict:
            self.malformed = True
            return
        if not self.enter_dict(state, SNAPSHOT_MAX_RECORD_KEYS):
            return
        self.fields(state, _SNAPSHOT, dict(
            snapshot_id=_string, at=_int,
            max_grants=lambda x: _int(x) and x > 0,
            state_epoch=lambda x: _int(x) and x >= 0))
        if 'policy' in state:
            self.policy(state['policy'])
        if 'grants' in state:
            self.grants(state['grants'])
        if 'roots' in state:
            self.roots(state['roots'])

    def policy(self, policy):
        if type(policy) is not dict:
            self.malformed = True
            return
        if self.enter_dict(policy, SNAPSHOT_MAX_RECORD_KEYS):
            self.fields(policy, _POLICY, dict(
                policy_id=_target, revision=_string, digest=_string,
                mutable_by_policy_change=lambda x: type(x) is bool))

    def roots(self, roots):
        if type(roots) is not dict:
            self.malformed = True
            return
        if not self.enter_dict(roots, SNAPSHOT_MAX_ROOTS):
            return
        for identifier, anchor in dict.items(roots):
            if not _string(identifier):
                self.malformed = True
            if type(anchor) is not dict:
                self.malformed = True
                continue
            if self.enter_dict(anchor, SNAPSHOT_MAX_RECORD_KEYS):
                self.fields(anchor, _ANCHOR, dict(revision=_string, digest=_string))

    def grants(self, records):
        if type(records) is not list:
            self.malformed = True
            return
        self.charge()
        if len(records) > SNAPSHOT_MAX_GRANTS:
            raise _SizeExceeded()
        identifiers = set()
        for record in records:
            self.charge()
            self.scalar_size(record)
            if type(record) is not dict:
                self.malformed = True
                continue
            if not self.enter_dict(record, SNAPSHOT_MAX_RECORD_KEYS):
                continue
            scalars = {name: _string for name in ('id', 'revision', 'digest',
                                                  'subject', 'issuer')}
            scalars.update(
                parent_id=lambda x: x is None or _string(x),
                not_before=_int, expires_at=_int,
                revoked=lambda x: x is None or type(x) is bool,
                can_delegate=lambda x: type(x) is bool)
            self.fields(record, _GRANT, scalars)
            self.scope(record, 'operations',
                       lambda op: type(op) is str and op in _OPERATIONS)
            self.scope(record, 'targets', _target)
            identifier = record.get('id')
            if _string(identifier):
                if identifier in identifiers:
                    self.malformed = True
                identifiers.add(identifier)
            start, end = record.get('not_before'), record.get('expires_at')
            if _int(start) and _int(end) and start >= end:
                self.malformed = True


def _preflight(state):
    """Classify a provider result: SNAPSHOT_LIMIT > INVALID > UNRESOLVED (§7.4)."""
    scan = _Preflight()
    try:
        scan.snapshot(state)
    except _SizeExceeded:
        return 'SNAPSHOT_LIMIT_EXCEEDED'
    if scan.malformed:
        return 'INVALID_AUTHORITY_INPUT'
    if scan.missing:
        return 'AUTHORITY_UNRESOLVED'
    return None


# --- stage 5: private copy (S-6, S-7) ----------------------------------------

def _copy_grant(record):
    out = {key: record[key] for key in _GRANT}
    out['operations'] = list(record['operations'])
    out['targets'] = list(record['targets'])
    return out


def _copy_snapshot(state):
    return dict(snapshot_id=state['snapshot_id'],
                policy={key: state['policy'][key] for key in _POLICY},
                grants=[_copy_grant(record) for record in state['grants']],
                roots={identifier: {key: anchor[key] for key in _ANCHOR}
                       for identifier, anchor in state['roots'].items()},
                at=state['at'], max_grants=state['max_grants'],
                state_epoch=state['state_epoch'])


# --- stage 6-8: traversal, epoch check, result ------------------------------

def _traverse(request, state, verify_grant):
    """#93 traversal. Return (reason, None) or (None, valid_until)."""
    policy = state['policy']
    if (request['policy_id'], request['expected_revision'], request['expected_digest']) != (
            policy['policy_id'], policy['revision'], policy['digest']):
        return 'POLICY_STATE_MISMATCH', None
    if not policy['mutable_by_policy_change'] or request['operation'] != 'POLICY_CHANGE':
        return 'AUTHORITY_SCOPE_VIOLATION', None
    records = {record['id']: record for record in state['grants']}
    seen = set()
    identifier = request['leaf_grant_id']
    child = None
    valid_until = None
    while True:
        if identifier in seen:
            return 'AUTHORITY_CYCLE_DETECTED', None
        if len(seen) >= state['max_grants']:
            return 'AUTHORITY_LIMIT_EXCEEDED', None
        seen.add(identifier)
        record = records.get(identifier)
        if record is None:
            return 'AUTHORITY_UNRESOLVED', None
        verification = verify_grant(_copy_grant(record), state['at'])
        if type(verification) is not str:
            return 'AUTHORITY_VERIFICATION_ERROR', None
        if verification == 'UNVERIFIED':
            return 'AUTHORITY_UNRESOLVED', None
        if verification != 'VERIFIED':
            return 'AUTHORITY_VERIFICATION_ERROR', None
        if (child is None and record['subject'] != request['requester_id']) or (
                child is not None and child['issuer'] != record['subject']):
            return 'AUTHORITY_SCOPE_VIOLATION', None
        if (request['operation'] not in record['operations'] or
                request['policy_id'] not in record['targets']):
            return 'AUTHORITY_SCOPE_VIOLATION', None
        if record['revoked'] is None:
            return 'AUTHORITY_UNRESOLVED', None
        if record['revoked']:
            return 'AUTHORITY_REVOKED', None
        if not record['not_before'] <= state['at'] < record['expires_at']:
            return 'AUTHORITY_NOT_CURRENT', None
        if child is not None:
            if (not record['can_delegate'] or
                    not set(child['operations']).issubset(record['operations']) or
                    not set(child['targets']).issubset(record['targets']) or
                    child['not_before'] < record['not_before'] or
                    child['expires_at'] > record['expires_at']):
                return 'AUTHORITY_SCOPE_VIOLATION', None
        expiry = record['expires_at']
        valid_until = expiry if valid_until is None else min(valid_until, expiry)
        if record['parent_id'] is None:
            anchor = state['roots'].get(identifier)
            if anchor is None or (anchor['revision'], anchor['digest']) != (
                    record['revision'], record['digest']):
                return 'AUTHORITY_UNRESOLVED', None
            return None, valid_until
        child = record
        identifier = record['parent_id']


def _resolve(request, authenticate, snapshot_provider, current_epoch, verify_grant):
    """Stages 1-8 after API checks. Returns the §5.1 inspection result."""
    reason, bound = _scan_request(request)
    if reason:
        return _denial(reason)
    try:
        authentication = authenticate(bound['requester_id'])
    except Exception:
        return _denial('AUTHORITY_VERIFICATION_ERROR')
    if type(authentication) is not str:
        return _denial('AUTHORITY_VERIFICATION_ERROR')
    if authentication == 'NOT_ESTABLISHED':
        return _denial('AUTHENTICATION_NOT_ESTABLISHED')
    if authentication != 'ESTABLISHED':
        return _denial('AUTHORITY_VERIFICATION_ERROR')
    try:
        supplied = snapshot_provider()
        if supplied is None:
            return _denial('AUTHORITY_UNRESOLVED')
        reason = _preflight(supplied)
        if reason:
            return _denial(reason)
        state = _copy_snapshot(supplied)
        reason = _preflight(state)
        if reason:
            return _denial(reason)
        reason, valid_until = _traverse(bound, state, verify_grant)
        if reason:
            return _denial(reason)
        observed = current_epoch()
        if type(observed) is not int:
            return _denial('AUTHORITY_VERIFICATION_ERROR')
        if observed > state['state_epoch']:
            return _denial('AUTHORITY_STATE_CHANGED')
        if observed < state['state_epoch']:
            return _denial('AUTHORITY_VERIFICATION_ERROR')
        return dict(authorization_status='AUTHORIZED', reason='POLICY_CHANGE_AUTHORIZED',
                    effect_path='NOT_DETERMINED',
                    request_binding=tuple(bound[key] for key in FIELDS),
                    snapshot_id=state['snapshot_id'], state_epoch=state['state_epoch'],
                    snapshot_at=state['at'], valid_until=valid_until)
    except Exception:
        return _denial('AUTHORITY_VERIFICATION_ERROR')


def resolve_policy_change(*, request, authenticate, snapshot_provider,
                          current_epoch, verify_grant):
    """Inspection entry (§1). Never consumable; never causes an effect."""
    _check_api(request, (authenticate, snapshot_provider, current_epoch, verify_grant))
    return _resolve(request, authenticate, snapshot_provider, current_epoch, verify_grant)
