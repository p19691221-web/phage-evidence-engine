"""Synthetic data only; does not call any external service."""
import json
import tempfile
import time
from pathlib import Path
from guard import Guard

with tempfile.TemporaryDirectory() as directory:
    guard = Guard(Path(directory) / 'demo.sqlite')
    guard.initialize()
    now = int(time.time())
    guard.add_policy(dict(id='shared-demo-budget', agents=['agent-a', 'agent-b'],
                          actions=['order'], targets=['synthetic-supplier'], currency='DEMO_UNITS',
                          start=now - 1, end=now + 3600, per_action=30, total=100, review_above=25))
    for i in range(6):
        result = guard.reserve(dict(policy_id='shared-demo-budget', request_id=f'order-{i+1}',
                                    agent='agent-a' if i % 2 else 'agent-b', action='order',
                                    target='synthetic-supplier', currency='DEMO_UNITS', amount=20))
        print(json.dumps({'request': i+1, **result}, ensure_ascii=False))
