"""Serve the real page with controlled PR states for a browser review.

Run: PYTHONPATH=. python3 tests/serve_review_fixture.py --state-file /tmp/pr-state.
Write MERGED, CLOSED, or unavailable to that file, then Refresh sources.
"""
import argparse
from pathlib import Path
from unittest.mock import patch

from tink_substrate.server import make_server
from tink_substrate.sources import attention, now


def fixture(state_file):
    state = state_file.read_text().strip()
    if state not in ('MERGED', 'CLOSED', 'unavailable'):
        raise ValueError('Expected MERGED, CLOSED, or unavailable')
    record = dict(title='PR state review fixture', project='example', owner='Reviewer',
                  next_action='Inspect the PR state and warnings.', body='Controlled browser review data.',
                  path=str(state_file), branch='patch', questions=[])
    sources = {name: dict(status='ok', checked_at=now(), data={})
               for name in ('git', 'github', 'workflow', 'seed', 'handoff')}
    sources['git']['data'] = dict(branch='patch', head='same', branches=[], worktrees=[
        dict(path='/example', branch='patch', selected=True, changes=dict(status='ok',
             data=dict(dirty=True, count=1, files=[dict(path='example.py', status='M')], truncated=False)))])
    sources['github']['data'] = dict(state=state, headRefOid='same', ci='passed', reviewDecision='',
                                   number=1, url='https://github.com/example/project/pull/1')
    if state == 'unavailable':
        sources['github'] = dict(status='unavailable', checked_at=now(), error='Fixture: source unavailable')
    sources['workflow']['data'] = dict(verification_status='stale', checklist=[], decisions=[])
    return dict(schema=1, observed_at=now(), record=record, sources=sources,
                attention=attention(record, sources), artifacts=[], limits='Review fixture; no live repository data.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--state-file', type=Path, required=True)
    args = parser.parse_args()
    with patch('tink_substrate.server.snapshot', side_effect=lambda _: fixture(args.state_file)):
        server = make_server({}, 0)
        print(f'http://127.0.0.1:{server.server_port}', flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
        finally:
            server.server_close()
