import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from guard import Guard


class GuardTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / 'guard.sqlite'
        self.guard = Guard(self.path, clock=lambda: 100)
        self.guard.initialize()
        self.policy = dict(id='budget', agents=['a', 'b'], actions=['order'], targets=['supplier'],
                           currency='TWD_MINOR', start=50, end=200, per_action=30,
                           total=100, review_above=25)
        self.guard.add_policy(self.policy)

    def request(self, key='r', **changes):
        return dict(dict(policy_id='budget', request_id=key, agent='a', action='order',
                         target='supplier', currency='TWD_MINOR', amount=20), **changes)

    def test_aggregate_shared_across_agents(self):
        for i in range(5):
            r = self.request(str(i)); r['agent'] = 'a' if i % 2 else 'b'
            self.assertEqual(self.guard.reserve(r)['decision'], 'RESERVED')
        self.assertEqual(self.guard.reserve(self.request('sixth'))['reason'], 'AGGREGATE_LIMIT')

    def test_replay_does_not_consume_budget(self):
        self.guard.reserve(self.request())
        r = self.guard.reserve(self.request())
        self.assertTrue(r['reused']); self.assertEqual(r['reserved_total'], 20)

    def test_changed_request_id_conflict(self):
        self.guard.reserve(self.request())
        r = self.request(); r['amount'] = 21
        self.assertEqual(self.guard.reserve(r)['reason'], 'REQUEST_ID_CONFLICT')

    def test_window_rechecked_on_replay(self):
        self.guard.reserve(self.request())
        self.guard.clock = lambda: 200
        self.assertEqual(self.guard.reserve(self.request())['reason'], 'OUTSIDE_WINDOW')

    def test_scope(self):
        for field, value, reason in [('agent','intruder','AGENT_OUT_OF_SCOPE'),
                                     ('action','delete','ACTION_OUT_OF_SCOPE'),
                                     ('target','other','TARGET_OUT_OF_SCOPE'),
                                     ('currency','USD','CURRENCY_MISMATCH')]:
            r = self.request(); r[field] = value
            self.assertEqual(self.guard.reserve(r)['reason'], reason)

    def test_limits_and_review(self):
        r = self.request(); r['amount'] = 31
        self.assertEqual(self.guard.reserve(r)['reason'], 'PER_ACTION_LIMIT')
        r['amount'] = 26
        self.assertEqual(self.guard.reserve(r)['decision'], 'REVIEW_REQUIRED')
        self.assertEqual(self.guard.reserve(self.request())['reserved_total'], 20)

    def test_policy_immutable(self):
        self.guard.add_policy(self.policy)
        with self.assertRaises(ValueError):
            self.guard.add_policy({**self.policy, 'total': 200})

    def test_reject_malformed_amount(self):
        for value in [-1, 1.2, True, '20', 2**63]:
            r = self.request(); r['amount'] = value
            with self.assertRaises(ValueError): self.guard.reserve(r)

    def test_unknown_policy_and_no_external_effect(self):
        r = self.request(); r['policy_id'] = 'missing'
        result = self.guard.reserve(r)
        self.assertEqual(result['decision'], 'DENY')
        self.assertFalse(result['executes_external_action'])

    def test_concurrent_requests_cannot_overreserve(self):
        def run(i):
            return Guard(self.path, clock=lambda: 100).reserve(self.request(str(i)))
        with ThreadPoolExecutor(max_workers=10) as pool:
            result = list(pool.map(run, range(10)))
        self.assertEqual(sum(r['decision'] == 'RESERVED' for r in result), 5)
        self.assertEqual(max(r['reserved_total'] for r in result), 100)
        self.assertEqual(len(self.guard.ledger()), 10)

    def test_concurrent_duplicate_consumes_once(self):
        with ThreadPoolExecutor(max_workers=5) as pool:
            result = list(pool.map(lambda _: Guard(self.path,clock=lambda:100).reserve(self.request()),range(5)))
        self.assertEqual(sum(not r['reused'] for r in result),1)
        self.assertTrue(all(r['reserved_total']==20 for r in result))

    def test_database_error_does_not_allow(self):
        with self.assertRaises(Exception):
            Guard(Path(self.tmp.name)/'missing'/'db').reserve(self.request())


if __name__ == '__main__':
    unittest.main()
