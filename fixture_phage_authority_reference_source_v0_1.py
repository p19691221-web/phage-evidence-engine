"""Reference state source and shared fixtures for H/H'/N v0.2 RED tests.

Test support only; not a product module. Implements the frozen v0.2 interface
(PHAGE_AUTHORITY_LINEAGE_HHN_EXECUTABLE_INTERFACE_v0_2.md) §2.1 atomic commit
step and the §2.2 source obligations E1, O1, O1a, O2, O3 for an in-memory,
single-threaded model. Nothing here validates a production source.
"""
from copy import deepcopy

FIELDS = ('requester_id', 'policy_id', 'expected_revision', 'expected_digest',
          'proposed_revision', 'proposed_digest', 'operation', 'leaf_grant_id')
GRANT_FIELDS = ('id', 'revision', 'digest', 'subject', 'issuer', 'parent_id',
                'operations', 'targets', 'not_before', 'expires_at', 'revoked',
                'can_delegate')


def grant(identifier, subject, issuer, parent, **overrides):
    record = dict(id=identifier, revision='r1', digest='d-' + identifier,
                  subject=subject, issuer=issuer, parent_id=parent,
                  operations=['POLICY_CHANGE'], targets=['policy'],
                  not_before=0, expires_at=100, revoked=False, can_delegate=True)
    record.update(overrides)
    return record


def base_request(**overrides):
    request = dict(zip(FIELDS, ('alice', 'policy', 'p1', 'pd1', 'p2', 'pd2',
                                'POLICY_CHANGE', 'leaf')))
    request.update(overrides)
    return request


def base_snapshot(**overrides):
    """#92 base fixture plus state_epoch (v0.2 §4)."""
    state = dict(snapshot_id='s1',
                 policy=dict(policy_id='policy', revision='p1', digest='pd1',
                             mutable_by_policy_change=True),
                 grants=[grant('leaf', 'alice', 'root-subject', 'root'),
                         grant('root', 'root-subject', 'external', None)],
                 roots={'root': dict(revision='r1', digest='d-root')},
                 at=10, max_grants=2, state_epoch=0)
    state.update(overrides)
    return state


# --- Visit counter: literal implementation of frozen v0.2 §7.2 S-5 / §7.3 ---

_POSITIONS = {
    ('snapshot',): dict,
    ('snapshot', 'policy'): dict,
    ('snapshot', 'grants'): list,
    ('snapshot', 'grants', '*'): dict,
    ('snapshot', 'grants', '*', 'operations'): list,
    ('snapshot', 'grants', '*', 'targets'): list,
    ('snapshot', 'roots'): dict,
    ('snapshot', 'roots', '*'): dict,
}


def _child(path, key):
    if path in (('snapshot', 'grants'), ('snapshot', 'roots')):
        return path + ('*',)
    return path + (key,)


def _entered(value, path):
    return path in _POSITIONS and type(value) is _POSITIONS[path]


def _visits(container, path):
    total = 1
    if type(container) is dict:
        gated = all(type(key) is str for key in dict.keys(container))
        for key, value in dict.items(container):
            total += 1
            if gated:
                child = _child(path, key)
                if _entered(value, child):
                    total += _visits(value, child)
    else:
        for element in container:
            total += 1
            child = _child(path, None)
            if _entered(element, child):
                total += _visits(element, child)
    return total


def count_visits(snapshot):
    """Normative visit count of an exact-typed snapshot (v0.2 §7.3)."""
    if type(snapshot) is not dict:
        raise TypeError('count_visits expects an exact dict snapshot')
    return _visits(snapshot, ('snapshot',))


def visit_boundary_snapshot(last_targets, roots=None):
    """v0.2 §7.3 boundary shape: 1024 grants, one operation each, 1023 with 47
    targets and one with `last_targets` targets."""
    grants = [grant('g%d' % i, 's', 'i', None,
                    targets=['t%d' % j for j in range(47)]) for i in range(1023)]
    grants.append(grant('g1023', 's', 'i', None,
                        targets=['t%d' % j for j in range(last_targets)]))
    state = base_snapshot(grants=grants)
    if roots is not None:
        state['roots'] = roots
    return state


def reference_figures():
    """Return (55, 65536, 65537) as computed; callers assert the values."""
    return (count_visits(base_snapshot()),
            count_visits(visit_boundary_snapshot(28)),
            count_visits(visit_boundary_snapshot(29)))


# --- Reference state source -------------------------------------------------

class ReferenceSource:
    """In-memory source. Every in-scope mutation advances the epoch (E1, O4);
    snapshots are detached deep copies taken at one epoch (O1, O1a); the three
    source seams share one counter and one clock (O2, O3)."""

    def __init__(self, *, grants=None, roots=None, policy=None, max_grants=2,
                 clock=10, epoch=0):
        self._policy = policy or dict(policy_id='policy', revision='p1',
                                      digest='pd1', mutable_by_policy_change=True)
        self._grants = grants if grants is not None else [
            grant('leaf', 'alice', 'root-subject', 'root'),
            grant('root', 'root-subject', 'external', None),
            grant('other', 'bob', 'external', None)]
        self._roots = roots if roots is not None else {
            'root': dict(revision='r1', digest='d-root')}
        self._max_grants = max_grants
        self.clock = clock
        self.epoch = epoch
        self.writes = 0          # commit writes only
        self.mutations = 0       # direct mutator calls
        self.calls = []          # seam call log
        self.pre_commit_hooks = []

    # seams
    def snapshot_provider(self):
        self.calls.append(('snapshot_provider',))
        return deepcopy(dict(snapshot_id='s-%d' % self.epoch, policy=self._policy,
                             grants=self._grants, roots=self._roots,
                             at=self.clock, max_grants=self._max_grants,
                             state_epoch=self.epoch))

    def current_epoch(self):
        self.calls.append(('current_epoch',))
        return self.epoch

    def commit_if_epoch(self, *, expected_epoch, snapshot_at, valid_until, binding):
        self.calls.append(('commit_if_epoch', dict(
            expected_epoch=expected_epoch, snapshot_at=snapshot_at,
            valid_until=valid_until, binding=binding)))
        while self.pre_commit_hooks:
            self.pre_commit_hooks.pop(0)(self)
        now = self.clock
        if now < snapshot_at:
            return dict(outcome='TIME_REGRESSION', committed_epoch=None)
        if self.epoch != expected_epoch:
            return dict(outcome='EPOCH_MISMATCH', committed_epoch=None)
        if now >= valid_until:
            return dict(outcome='NOT_CURRENT', committed_epoch=None)
        if binding[1] != self._policy['policy_id']:
            raise AssertionError('reference source holds a single policy')
        self._policy['revision'] = binding[4]
        self._policy['digest'] = binding[5]
        self.epoch += 1
        self.writes += 1
        return dict(outcome='COMMITTED', committed_epoch=self.epoch)

    # mutators (each advances the epoch)
    def _mutated(self):
        self.epoch += 1
        self.mutations += 1

    def find(self, identifier):
        for record in self._grants:
            if record['id'] == identifier:
                return record
        raise KeyError(identifier)

    def revoke(self, identifier, value=True):
        self.find(identifier)['revoked'] = value
        self._mutated()

    def set_policy(self, revision, digest):
        self._policy.update(revision=revision, digest=digest)
        self._mutated()

    def touch(self, identifier='other'):
        record = self.find(identifier)
        record['digest'] = record['digest'] + "'"
        self._mutated()

    # inspection
    def dump(self):
        return deepcopy(dict(policy=self._policy, grants=self._grants,
                             roots=self._roots, max_grants=self._max_grants,
                             epoch=self.epoch))

    def live_containers(self):
        """Identities of every live store container (for O1a checks)."""
        ids = {id(self._policy), id(self._grants), id(self._roots)}
        for record in self._grants:
            ids.update({id(record), id(record['operations']), id(record['targets'])})
        for anchor in self._roots.values():
            ids.add(id(anchor))
        return ids


def snapshot_containers(snapshot):
    ids = {id(snapshot), id(snapshot['policy']), id(snapshot['grants']),
           id(snapshot['roots'])}
    for record in snapshot['grants']:
        ids.update({id(record), id(record['operations']), id(record['targets'])})
    for anchor in snapshot['roots'].values():
        ids.add(id(anchor))
    return ids


# --- Hook-recording types for safe-traversal tests (v0.2 §7.2) --------------

RECORDER = []


def _recording(base, names):
    namespace = {}
    for name in names:
        def method(self, *args, _name=name, **kwargs):
            RECORDER.append((base.__name__, _name))
            return getattr(base, _name)(self, *args, **kwargs)
        namespace[name] = method
    return type('Recording' + base.__name__.capitalize(), (base,), namespace)


RecStr = _recording(str, ['__len__', '__iter__', '__getitem__', '__eq__', '__ne__',
                          '__hash__', '__contains__', '__lt__', '__le__',
                          '__gt__', '__ge__'])
RecList = _recording(list, ['__len__', '__iter__', '__getitem__', '__eq__',
                            '__ne__', '__contains__', '__copy__', '__deepcopy__',
                            'copy', 'index', 'count'])
RecDict = _recording(dict, ['__len__', '__iter__', '__getitem__', '__eq__',
                            '__ne__', '__contains__', 'keys', 'items', 'values',
                            'get', 'copy', '__copy__', '__deepcopy__'])
RecInt = _recording(int, ['bit_length', '__eq__', '__ne__', '__hash__', '__lt__',
                          '__le__', '__gt__', '__ge__', '__index__', '__int__',
                          '__bool__', '__add__', '__sub__'])
for _cls in (RecList, RecDict):
    # copy hooks need a fallback because list/dict lack __deepcopy__.
    def _deepcopy(self, memo, _base=_cls.__mro__[1]):
        RECORDER.append((_base.__name__, '__deepcopy__'))
        return _base(self)
    _cls.__deepcopy__ = _deepcopy
    def _copy(self, _base=_cls.__mro__[1]):
        RECORDER.append((_base.__name__, '__copy__'))
        return _base(self)
    _cls.__copy__ = _copy


class Collider:
    """Non-str key whose hash equals hash(field); __eq__ records (v0.2 P§8 T04)."""

    def __init__(self, field):
        self.field = field

    def __hash__(self):
        return hash(self.field)

    def __eq__(self, other):
        RECORDER.append(('Collider', self.field))
        return False


class OpaqueKey:
    """Non-str key with recording __hash__/__eq__, no collision intended."""

    def __hash__(self):
        RECORDER.append(('OpaqueKey', '__hash__'))
        return 0x5EED

    def __eq__(self, other):
        RECORDER.append(('OpaqueKey', '__eq__'))
        return self is other


def replace_key(mapping, field, new_key):
    """Rebuild `mapping` with `new_key` in place of `field`, same order."""
    return {new_key if key == field else key: value for key, value in mapping.items()}
