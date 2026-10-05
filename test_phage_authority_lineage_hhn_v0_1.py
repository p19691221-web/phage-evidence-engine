"""Proposed fixture acceptance tests; absent module is surface RED only."""
import importlib
import unittest
import subprocess
import sys
import json
from pathlib import Path
from copy import deepcopy

FIELDS = ('requester_id', 'policy_id', 'expected_revision', 'expected_digest',
          'proposed_revision', 'proposed_digest', 'operation', 'leaf_grant_id')


def grant(identifier, subject, issuer, parent):
    return dict(id=identifier, revision='r1', digest='d-'+identifier,
                subject=subject, issuer=issuer, parent_id=parent,
                operations=['POLICY_CHANGE'], targets=['policy'],
                not_before=0, expires_at=100, revoked=False, can_delegate=True)


def inputs():
    request = dict(zip(FIELDS, ('alice', 'policy', 'p1', 'pd1', 'p2', 'pd2',
                                'POLICY_CHANGE', 'leaf')))
    state = dict(snapshot_id='s1', policy=dict(policy_id='policy', revision='p1',
                 digest='pd1', mutable_by_policy_change=True),
                 grants=[grant('leaf', 'alice', 'root-subject', 'root'),
                         grant('root', 'root-subject', 'external', None)],
                 roots={'root': dict(revision='r1', digest='d-root')},
                 at=10, max_grants=2)
    return request, state


def bounded_cycle(request, state):
    # subprocess.run kills and waits for the disposable child on timeout.
    worker = """
import json,sys,importlib
m=importlib.import_module('phage_authority_lineage_hhn_v0_1')
r,s=json.load(sys.stdin); seen=[]
def verify(record,at):
    seen.append(record['id'])
    return 'VERIFIED'
result=m.resolve_policy_change(request=r,authenticate=lambda subject:'ESTABLISHED',
    snapshot_provider=lambda:s,verify_grant=verify)
print(json.dumps(dict(result=result,seen=seen,request=r,state=s)))
"""
    completed = subprocess.run([sys.executable, '-c', worker],
        cwd=Path(__file__).resolve().parent, input=json.dumps([request, state]),
        capture_output=True, text=True, timeout=5)
    if completed.returncode != 0:
        raise AssertionError('cycle worker failed: '+completed.stderr)
    return json.loads(completed.stdout)


class HHNTests(unittest.TestCase):
    def setUp(self):
        try:
            self.module = importlib.import_module('phage_authority_lineage_hhn_v0_1')
        except ModuleNotFoundError as error:
            if error.name != 'phage_authority_lineage_hhn_v0_1':
                raise
            self.fail('H/H-prime/N module absent: surface RED, not behavioral RED')
        self.request, self.state = inputs()
        self.calls = []

    def resolve(self, authentication='ESTABLISHED', provider=None, verifier=None):
        def auth(subject):
            self.calls.append(('auth', subject))
            return authentication
        def snapshot():
            self.calls.append(('snapshot',))
            return self.state
        def verify(record, at):
            self.calls.append(('grant', record['id'], at))
            return 'VERIFIED'
        before = deepcopy((self.request, self.state))
        result = self.module.resolve_policy_change(request=self.request,
                 authenticate=auth, snapshot_provider=provider or snapshot,
                 verify_grant=verifier or verify)
        self.assertEqual((self.request, self.state), before)
        return result

    def denied(self, reason, **kwargs):
        result = self.resolve(**kwargs)
        status = 'VERIFICATION_ERROR' if reason == 'AUTHORITY_VERIFICATION_ERROR' else 'UNVERIFIED'
        self.assertEqual(result, dict(authorization_status=status, reason=reason,
                         effect_path='BLOCKED', request_binding=None, snapshot_id=None))

    def test_HP01_HP02_positive_binding_and_order(self):
        result = self.resolve()
        self.assertEqual(result, dict(authorization_status='AUTHORIZED',
            reason='POLICY_CHANGE_AUTHORIZED', effect_path='NOT_DETERMINED',
            request_binding=tuple(self.request[k] for k in FIELDS), snapshot_id='s1'))
        self.assertEqual(self.calls, [('auth', 'alice'), ('snapshot',),
                                     ('grant', 'leaf', 10), ('grant', 'root', 10)])

    def test_H01_H02_caller_claims(self):
        for extra in ['authenticated', 'trusted_root', 'new_grant', 'self_authorized']:
            with self.subTest(extra=extra):
                self.request, self.state = inputs(); self.calls = []
                self.request[extra] = True
                self.denied('INVALID_AUTHORITY_INPUT')
                self.assertEqual(self.calls, [])
        self.request, self.state = inputs()
        self.state['grants'] = []
        self.denied('AUTHORITY_UNRESOLVED')

    def test_H03_protected_target(self):
        self.state['policy']['mutable_by_policy_change'] = False
        self.denied('AUTHORITY_SCOPE_VIOLATION')
        self.assertFalse(any(c[0] == 'grant' for c in self.calls))

    def test_A01_authentication_hard_stop(self):
        for outcome, reason in [('NOT_ESTABLISHED', 'AUTHENTICATION_NOT_ESTABLISHED'),
                                ('VERIFICATION_ERROR', 'AUTHORITY_VERIFICATION_ERROR'),
                                (True, 'AUTHORITY_VERIFICATION_ERROR')]:
            with self.subTest(outcome=outcome):
                self.calls = []; self.denied(reason, authentication=outcome)
                self.assertEqual(self.calls, [('auth', 'alice')])
        def fault(subject):
            raise RuntimeError('fault')
        forbidden = []
        def provider():
            forbidden.append('provider')
            return self.state
        def verifier(*args):
            forbidden.append('verifier')
            return 'VERIFIED'
        before = deepcopy((self.request, self.state))
        result = self.module.resolve_policy_change(request=self.request, authenticate=fault,
                 snapshot_provider=provider, verify_grant=verifier)
        self.assertEqual(forbidden, [])
        self.assertEqual((self.request, self.state), before)
        self.assertEqual(result, dict(authorization_status='VERIFICATION_ERROR',
            reason='AUTHORITY_VERIFICATION_ERROR', effect_path='BLOCKED',
            request_binding=None, snapshot_id=None))

    def test_A02_missing_state_and_exact_root(self):
        for case in ['leaf', 'parent', 'root', 'root_digest', 'root_revision', 'revocation']:
            with self.subTest(case=case):
                self.request, self.state = inputs()
                if case == 'leaf': self.state['grants'].pop(0)
                elif case == 'parent': self.state['grants'].pop(1)
                elif case == 'root': self.state['roots'] = {}
                elif case.startswith('root_'): self.state['roots']['root'][case[5:]] = 'other'
                else: self.state['grants'][0]['revoked'] = None
                self.denied('AUTHORITY_UNRESOLVED')

    def test_A03_delegation_attenuation(self):
        for case in ['subject', 'issuer', 'delegation', 'targets', 'start', 'end']:
            with self.subTest(case=case):
                self.request, self.state = inputs()
                leaf, root = self.state['grants']
                if case in ('subject', 'issuer'): leaf[case] = 'wrong'
                elif case == 'delegation': root['can_delegate'] = False
                elif case == 'targets': leaf['targets'].append('extra')
                elif case == 'start': leaf['not_before'] = -1
                else: leaf['expires_at'] = 101
                self.denied('AUTHORITY_SCOPE_VIOLATION')

    def test_A04_revocation_and_time(self):
        for revoked, at, reason in [(True, 10, 'AUTHORITY_REVOKED'),
                                   (False, -1, 'AUTHORITY_NOT_CURRENT'),
                                   (False, 100, 'AUTHORITY_NOT_CURRENT')]:
            with self.subTest(at=at, revoked=revoked):
                self.request, self.state = inputs()
                self.state['grants'][0]['revoked'] = revoked; self.state['at'] = at
                self.denied(reason)
        self.request, self.state = inputs(); self.state['at'] = 0
        self.assertEqual(self.resolve()['authorization_status'], 'AUTHORIZED')

    def test_root_and_intermediate_local_validity(self):
        for location in ['root', 'middle']:
            for field, value, reason in [('revoked', True, 'AUTHORITY_REVOKED'),
                    ('revoked', None, 'AUTHORITY_UNRESOLVED'),
                    ('not_before', 11, 'AUTHORITY_NOT_CURRENT'),
                    ('expires_at', 10, 'AUTHORITY_NOT_CURRENT')]:
                with self.subTest(location=location, field=field, value=value):
                    self.request, self.state = inputs(); self.calls = []
                    leaf, root = self.state['grants']
                    middle = grant('middle', 'middle-subject', 'root-subject', 'root')
                    leaf.update(issuer='middle-subject', parent_id='middle')
                    self.state['grants'].insert(1, middle); self.state['max_grants'] = 3
                    self.assertEqual(self.resolve(), dict(authorization_status='AUTHORIZED',
                        reason='POLICY_CHANGE_AUTHORIZED', effect_path='NOT_DETERMINED',
                        request_binding=tuple(self.request[k] for k in FIELDS), snapshot_id='s1'))
                    self.assertEqual([c[1] for c in self.calls if c[0] == 'grant'],
                                     ['leaf', 'middle', 'root'])
                    self.calls = []
                    selected = root if location == 'root' else middle
                    selected[field] = value
                    self.denied(reason)
                    self.assertLessEqual(sum(c[0] == 'grant' for c in self.calls), 3)
        self.request, self.state = inputs()
        self.assertEqual(self.resolve()['authorization_status'], 'AUTHORIZED')

    def test_matching_scopes_without_requested_authority(self):
        for field, value in [('operations', []), ('targets', ['other-policy'])]:
            with self.subTest(field=field):
                self.request, self.state = inputs()
                for record in self.state['grants']: record[field] = deepcopy(value)
                self.denied('AUTHORITY_SCOPE_VIOLATION')
        self.request, self.state = inputs()
        self.assertEqual(self.resolve()['authorization_status'], 'AUTHORIZED')

    def test_A05_policy_and_request_binding(self):
        for field in ['policy_id', 'expected_revision', 'expected_digest']:
            with self.subTest(field=field):
                self.request, self.state = inputs(); self.request[field] = 'other'
                self.denied('POLICY_STATE_MISMATCH')
        self.request, self.state = inputs()
        previous = self.resolve(); self.request['proposed_digest'] = 'new-content'
        current = self.resolve()
        self.assertNotEqual(previous['request_binding'], current['request_binding'])
        self.assertEqual(previous['request_binding'][5], 'pd2')

    def test_N01_N02_cycles(self):
        for count, prefix in [(1, False), (2, False), (2, True)]:
            with self.subTest(count=count, prefix=prefix):
                self.request, self.state = inputs(); self.calls = []
                nodes = [grant(str(i), 'alice', 'alice', str((i+1) % count)) for i in range(count)]
                if prefix: nodes.insert(0, grant('prefix', 'alice', 'alice', '0'))
                self.state.update(grants=nodes, roots={}, max_grants=len(nodes))
                self.request['leaf_grant_id'] = nodes[0]['id']
                observed = bounded_cycle(self.request, self.state)
                self.assertEqual(observed['result'], dict(authorization_status='UNVERIFIED',
                    reason='AUTHORITY_CYCLE_DETECTED', effect_path='BLOCKED',
                    request_binding=None, snapshot_id=None))
                self.assertEqual(observed['request'], self.request)
                self.assertEqual(observed['state'], self.state)
                seen = observed['seen']
                self.assertEqual(len(seen), len(nodes)); self.assertEqual(len(seen), len(set(seen)))

    def test_N03_N04_budget_boundary(self):
        self.state['max_grants'] = 1
        self.denied('AUTHORITY_LIMIT_EXCEEDED')
        self.assertEqual([c[1] for c in self.calls if c[0] == 'grant'], ['leaf'])
        self.state['max_grants'] = 2
        self.assertEqual(self.resolve()['authorization_status'], 'AUTHORIZED')

    def test_E01_provider_and_verifier_faults(self):
        def fault(*args): raise RuntimeError('private fault')
        self.denied('AUTHORITY_VERIFICATION_ERROR', provider=fault)
        self.denied('AUTHORITY_UNRESOLVED', provider=lambda: None)
        self.denied('AUTHORITY_VERIFICATION_ERROR', verifier=fault)
        for outcome in [True, 1, None, 'VERIFICATION_ERROR']:
            with self.subTest(outcome=outcome):
                self.denied('AUTHORITY_VERIFICATION_ERROR', verifier=lambda *a: outcome)
        self.denied('AUTHORITY_UNRESOLVED', verifier=lambda *a: 'UNVERIFIED')

    def test_R01_reacquires_state(self):
        self.assertEqual(self.resolve()['authorization_status'], 'AUTHORIZED')
        self.state['grants'][0]['revoked'] = True
        self.denied('AUTHORITY_REVOKED')
        self.assertEqual(sum(c[0] == 'snapshot' for c in self.calls), 2)
        self.request, self.state = inputs(); self.state['policy']['revision'] = 'p3'
        self.denied('POLICY_STATE_MISMATCH')

    def test_V01_duplicate_and_malformed(self):
        self.state['grants'].append(deepcopy(self.state['grants'][0]))
        self.denied('INVALID_AUTHORITY_INPUT')
        for budget in [0, -1, True, '2']:
            with self.subTest(budget=budget):
                self.request, self.state = inputs(); self.state['max_grants'] = budget
                self.denied('INVALID_AUTHORITY_INPUT')

    def test_missing_malformed_and_extra_state_table(self):
        cases = [
            (('snapshot_id',), 'delete', None, 'AUTHORITY_UNRESOLVED'),
            (('policy', 'revision'), 'delete', None, 'AUTHORITY_UNRESOLVED'),
            (('roots', 'root', 'digest'), 'delete', None, 'AUTHORITY_UNRESOLVED'),
            (('grants', 1, 'revoked'), 'delete', None, 'AUTHORITY_UNRESOLVED'),
            (('at',), 'set', True, 'INVALID_AUTHORITY_INPUT'),
            (('policy', 'mutable_by_policy_change'), 'set', 1, 'INVALID_AUTHORITY_INPUT'),
            (('roots', 'root'), 'set', [], 'INVALID_AUTHORITY_INPUT'),
            (('roots', 'root', 'extra'), 'set', 'x', 'INVALID_AUTHORITY_INPUT'),
            (('policy', 'extra'), 'set', 'x', 'INVALID_AUTHORITY_INPUT'),
            (('extra',), 'set', 'x', 'INVALID_AUTHORITY_INPUT'),
            (('grants', 0, 'extra'), 'set', 'x', 'INVALID_AUTHORITY_INPUT'),
            (('grants', 0, 'not_before'), 'set', False, 'INVALID_AUTHORITY_INPUT'),
            (('grants', 0, 'operations'), 'set', ['POLICY_CHANGE', 'extra'], 'INVALID_AUTHORITY_INPUT'),
            (('grants', 0, 'operations'), 'set', ['POLICY_CHANGE']*2, 'INVALID_AUTHORITY_INPUT'),
            (('grants', 0, 'targets'), 'set', ['*'], 'INVALID_AUTHORITY_INPUT'),
            (('grants', 0, 'targets'), 'set', ['policy']*2, 'INVALID_AUTHORITY_INPUT'),
            (('grants', 0, 'targets'), 'set', [''], 'INVALID_AUTHORITY_INPUT'),
            (('grants',), 'set', {}, 'INVALID_AUTHORITY_INPUT'),
        ]
        for path, action, value, reason in cases:
            with self.subTest(path=path, action=action, value=value):
                self.request, self.state = inputs(); self.calls = []
                target = self.state
                for key in path[:-1]: target = target[key]
                if action == 'delete': del target[path[-1]]
                else: target[path[-1]] = value
                self.denied(reason)
                self.assertFalse(any(c[0] == 'grant' for c in self.calls))
        self.request, self.state = inputs(); self.calls = []
        del self.state['policy']['revision']
        self.state['grants'][1]['operations'] = ['extra']
        self.denied('INVALID_AUTHORITY_INPUT')
        self.assertFalse(any(c[0] == 'grant' for c in self.calls))
        self.request, self.state = inputs()
        self.assertEqual(self.resolve()['authorization_status'], 'AUTHORIZED')

    def test_request_and_api_validation_table(self):
        for field, action, value in [('expected_digest', 'delete', None),
                ('requester_id', 'set', ''), ('proposed_digest', 'set', 3)]:
            with self.subTest(field=field):
                self.request, self.state = inputs(); self.calls = []
                if action == 'delete': del self.request[field]
                else: self.request[field] = value
                self.denied('INVALID_AUTHORITY_INPUT'); self.assertEqual(self.calls, [])
        self.request, self.state = inputs(); self.request['operation'] = 'extra'
        self.denied('AUTHORITY_SCOPE_VIOLATION')
        class DictSubclass(dict): pass
        for argument, value in [('request', []), ('request', DictSubclass(inputs()[0])),
                ('authenticate', None), ('snapshot_provider', 1), ('verify_grant', False)]:
            with self.subTest(argument=argument):
                calls = []
                def auth(subject): calls.append('auth'); return 'ESTABLISHED'
                def provider(): calls.append('provider'); return self.state
                def verifier(*args): calls.append('verify'); return 'VERIFIED'
                kwargs = dict(request=inputs()[0], authenticate=auth,
                              snapshot_provider=provider, verify_grant=verifier)
                kwargs[argument] = value
                with self.assertRaises(TypeError): self.module.resolve_policy_change(**kwargs)
                self.assertEqual(calls, [])

    def test_seam_argument_isolation(self):
        def mutate(record, at):
            record['revoked'] = True; record['targets'].clear()
            return 'VERIFIED'
        result = self.resolve(verifier=mutate)
        self.assertEqual(result, dict(authorization_status='AUTHORIZED',
            reason='POLICY_CHANGE_AUTHORIZED', effect_path='NOT_DETERMINED',
            request_binding=tuple(self.request[k] for k in FIELDS), snapshot_id='s1'))


if __name__ == '__main__':
    unittest.main()
