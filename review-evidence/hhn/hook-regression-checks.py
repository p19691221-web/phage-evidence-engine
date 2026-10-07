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



checks = 0
counter = []
class Hostile(str):
    def __hash__(self): counter.append('hash'); return str.__hash__(self)
    def __eq__(self, other): counter.append('eq'); return str.__eq__(self, other)
    def __str__(self): counter.append('str'); return str.__str__(self)
    def __iter__(self): counter.append('iter'); return iter(())
    def __deepcopy__(self, memo): counter.append('deepcopy'); return str.__str__(self)
class HostileList(list):
    def __iter__(self): counter.append('iter'); return list.__iter__(self)
    def __deepcopy__(self, memo): counter.append('deepcopy'); return list(self)

def probe(name, mutate):
    global checks
    request, state = fixture()
    mutate(request, state)
    counter.clear()  # Setup insertion may hash; resolution must never do so.
    seams = []
    result = resolve(request=request, authenticate=lambda _: seams.append('auth') or 'ESTABLISHED',
        snapshot_provider=lambda: seams.append('provider') or state,
        verify_grant=lambda *args: seams.append('verify') or 'VERIFIED')
    assert result['reason'] == 'INVALID_AUTHORITY_INPUT', (name, result)
    assert counter == [], (name, counter)
    assert 'verify' not in seams, (name, seams)
    assert state['grants'][0]['revoked'] is False
    if name.startswith('request'): assert seams == [], seams
    checks += 1
    print('PASS', name)

def key(record, field):
    value = record.pop(field)
    record[Hostile(field)] = value

probe('request key', lambda r,s: key(r,'requester_id'))
probe('request value', lambda r,s: r.update(requester_id=Hostile('person')))
probe('snapshot key', lambda r,s: key(s,'snapshot_id'))
probe('policy key', lambda r,s: key(s['policy'],'policy_id'))
probe('grant key', lambda r,s: key(s['grants'][0],'id'))
probe('anchor key', lambda r,s: key(s['roots']['R'],'digest'))
probe('root identifier', lambda r,s: key(s['roots'],'R'))
probe('snapshot value', lambda r,s: s.update(snapshot_id=Hostile('independent')))
probe('scope element', lambda r,s: s['grants'][0].update(targets=[Hostile('target')]))
probe('scope list', lambda r,s: s['grants'][0].update(targets=HostileList(['target'])))
probe('bool integer', lambda r,s: s.update(at=True))
probe('tuple scope remains malformed', lambda r,s: s['grants'][0].update(targets=('target',)))

deep = []
for _ in range(10000): deep = [deep]
probe('deep scope', lambda r,s: s['grants'][0].update(targets=deep))
cycle = []; cycle.append(cycle)
probe('cycle scope', lambda r,s: s['grants'][0].update(targets=cycle))
shared = ['target']
for _ in range(100): shared = [shared, shared]
probe('shared expansion', lambda r,s: s['grants'][0].update(targets=shared))

# Authentication can mutate caller input; provider must observe a detached binding.
r,s = fixture()
expected = tuple(r.values())
def auth(_): r['requester_id']='changed'; return 'ESTABLISHED'
provider_calls=[]
def provider(): provider_calls.append(r['requester_id']); return s
result=resolve(request=r,authenticate=auth,snapshot_provider=provider,
               verify_grant=lambda *args:'VERIFIED')
assert provider_calls == ['changed']
assert result['request_binding'] == expected, result
checks += 1
print('PASS request detached before provider')
print(checks, 'checks; 0 mismatches; hook counter = 0')
