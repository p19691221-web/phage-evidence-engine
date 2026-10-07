"""Independent contract probes. Run: python -B hhn-independent-checks.py SOURCE_DIR.

Uses only Python stdlib, does not modify implementation or provider stores.
Exit 1 indicates an assertion-level contract mismatch, not a passing review.
"""
import sys
import importlib
from copy import deepcopy

sys.path.insert(0, sys.argv[1])
resolve = importlib.import_module('phage_authority_lineage_hhn_v0_1').resolve_policy_change


def fixture():
    request = dict(requester_id='person', policy_id='target', expected_revision='p0',
        expected_digest='old', proposed_revision='p1', proposed_digest='new',
        operation='POLICY_CHANGE', leaf_grant_id='L')
    def grant(identifier, subject, issuer, parent):
        return dict(id=identifier, revision='g0', digest='digest-'+identifier,
            subject=subject, issuer=issuer, parent_id=parent, operations=['POLICY_CHANGE'],
            targets=['target'], not_before=0, expires_at=40, revoked=False, can_delegate=True)
    state = dict(snapshot_id='independent', policy=dict(policy_id='target', revision='p0',
        digest='old', mutable_by_policy_change=True),
        grants=[grant('L', 'person', 'root-person', 'R'),
                grant('R', 'root-person', 'external', None)],
        roots={'R': dict(revision='g0', digest='digest-R')}, at=20, max_grants=2)
    return request, state


failures = []
checks = 0


def probe(name, change, reason, ids=None):
    global checks
    request, state = fixture()
    state = change(request, state) or state
    visited = []
    result = resolve(request=request, authenticate=lambda _: 'ESTABLISHED',
        snapshot_provider=lambda: state,
        verify_grant=lambda record, at: visited.append(record['id']) or 'VERIFIED')
    checks += 1
    expected_status = 'AUTHORIZED' if reason == 'POLICY_CHANGE_AUTHORIZED' else 'UNVERIFIED'
    expected_effect = 'NOT_DETERMINED' if expected_status == 'AUTHORIZED' else 'BLOCKED'
    ok = result['reason'] == reason and result['authorization_status'] == expected_status
    ok &= result['effect_path'] == expected_effect
    if expected_status == 'UNVERIFIED':
        ok &= result['snapshot_id'] is None and result['request_binding'] is None
    if ids is not None:
        ok &= visited == ids
    print(('PASS ' if ok else 'FAIL ')+name+': '+result['reason']+' visited='+repr(visited))
    if not ok:
        failures.append(name)


def field(path, value):
    def change(request, state):
        obj = state
        for key in path[:-1]: obj = obj[key]
        obj[path[-1]] = value
    return change


probe('valid two-grant chain', lambda r,s: None, 'POLICY_CHANGE_AUTHORIZED', ['L','R'])
for name, path, value, reason in [
    ('root revoked', ('grants',1,'revoked'), True, 'AUTHORITY_REVOKED'),
    ('root unknown revocation', ('grants',1,'revoked'), None, 'AUTHORITY_UNRESOLVED'),
    ('root not current before attenuation', ('grants',1,'expires_at'), 20, 'AUTHORITY_NOT_CURRENT'),
    ('issuer binding', ('grants',0,'issuer'), 'wrong', 'AUTHORITY_SCOPE_VIOLATION'),
    ('delegation permission', ('grants',1,'can_delegate'), False, 'AUTHORITY_SCOPE_VIOLATION'),
    ('target expansion', ('grants',0,'targets'), ['target','extra'], 'AUTHORITY_SCOPE_VIOLATION'),
    ('validity expansion', ('grants',0,'expires_at'), 41, 'AUTHORITY_SCOPE_VIOLATION'),
    ('anchor revision exact', ('roots','R','revision'), 'wrong', 'AUTHORITY_UNRESOLVED'),
    ('anchor digest exact', ('roots','R','digest'), 'wrong', 'AUTHORITY_UNRESOLVED'),
    ('budget below root', ('max_grants',), 1, 'AUTHORITY_LIMIT_EXCEEDED'),
    ('bool time rejected', ('at',), True, 'INVALID_AUTHORITY_INPUT'),
    ('tuple operations rejected', ('grants',0,'operations'), ('POLICY_CHANGE',), 'INVALID_AUTHORITY_INPUT'),
    ('unknown record vocabulary', ('grants',1,'operations'), ['OTHER'], 'INVALID_AUTHORITY_INPUT'),
    ('wildcard target rejected', ('grants',0,'targets'), ['target?'], 'INVALID_AUTHORITY_INPUT'),
]:
    probe(name, field(path,value), reason)


def mixed(request,state):
    del state['policy']['revision']
    state['grants'][1]['operations'] = ['OTHER']
probe('malformed overrides missing globally', mixed, 'INVALID_AUTHORITY_INPUT', [])


def unvisited(request,state,revoked=False,malformed=False):
    record = deepcopy(state['grants'][0]); record['id']='UNUSED'; record['revoked']=revoked
    if malformed: record['operations']=['OTHER']
    state['grants'].append(record)
probe('unvisited revoked excluded from local checks', lambda r,s: unvisited(r,s,True),
      'POLICY_CHANGE_AUTHORIZED', ['L','R'])
probe('unvisited malformed included globally', lambda r,s: unvisited(r,s,False,True),
      'INVALID_AUTHORITY_INPUT', [])


class PlainSubclass(dict): pass
probe('ordinary dict subclass rejected', lambda r,s: PlainSubclass(s), 'INVALID_AUTHORITY_INPUT', [])


class SanitizingDict(dict):
    def __deepcopy__(self, memo):
        return deepcopy(dict(self),memo)
probe('copy must not normalize nonplain snapshot', lambda r,s: SanitizingDict(s),
      'INVALID_AUTHORITY_INPUT', [])
probe('copy must not normalize nonplain grant', field(('grants',0),SanitizingDict(fixture()[1]['grants'][0])),
      'INVALID_AUTHORITY_INPUT', [])


class SanitizingList(list):
    def __deepcopy__(self,memo): return list(self)
probe('copy must not normalize nonexact list', field(('grants',0,'operations'),SanitizingList(['POLICY_CHANGE'])),
      'INVALID_AUTHORITY_INPUT', [])
probe('uncopyable malformed field has input reason',
      field(('grants',0,'operations'), (x for x in ['POLICY_CHANGE'])), 'INVALID_AUTHORITY_INPUT', [])


def missing_uncopyable(request,state):
    del state['policy']['revision']
    state['grants'][1]['targets']=(x for x in ['target'])
probe('uncopyable malformed overrides missing',missing_uncopyable,'INVALID_AUTHORITY_INPUT',[])

print(f'{checks} checks; {len(failures)} mismatches')
if failures: print('MISMATCHES: '+', '.join(failures))
sys.exit(bool(failures))
