"""`surface --json`: one read-only JSON for a human surface (Tinkery) and for agents asking "what happened?".

Ways this could fail, written before the code:
1. Missing data is shown as zero (an unlinked change has no operator minutes, not 0 minutes).
2. A stale or missing selection crashes instead of saying how to fix it.
3. The ledger row is linked to the wrong change, or silently picked when the change ID and PR disagree.
4. Informational notes drown out what actually needs the human.
5. A half-written last ledger line (the daily job appending) makes the whole ledger unavailable.
6. The command writes anything.
7. Small weekly samples get a precise-looking useful/hour.
"""
from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from tink_substrate import surface
from tink_substrate.__main__ import main

PR = 'https://github.com/o/r/pull/7'


def source(data=None, status='ok', error=None):
    value = {'status': status, 'checked_at': '2026-10-08T12:00:00+00:00'}
    return {**value, 'data': data} if status == 'ok' else {**value, 'error': error or 'unreachable'}


class SurfaceTest(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.checkout = self.root / 'checkout'
        (self.checkout / 'runs' / 'r1').mkdir(parents=True)
        self.work = self.root / 'work.md'
        self.work.write_text('+++\nschema = 1\ntitle = "Add a thing"\nproject = "example"\nowner = "me"\n'
                             f'next_action = "Review the PR"\nrun = "r1"\npr = "{PR}"\n+++\nWhy we want it.\n')
        self.config = self.root / 'config.json'
        self.config.write_text(json.dumps({'schema': 1, 'work': str(self.work), 'checkout': str(self.checkout)}))
        self.ledger = self.root / 'changes.jsonl'
        self.snap = {
            'schema': 1, 'observed_at': '2026-10-08T12:00:00+00:00',
            'record': {'title': 'Add a thing', 'project': 'example', 'next_action': 'Review the PR', 'run': 'r1',
                       'pr': PR, 'seed': None, 'handoff': None, 'body': 'Why we want it.'},
            'sources': {
                'git': source({'head': 'abc', 'branch': 'feature', 'worktrees': []}),
                'github': source({'number': 7, 'state': 'OPEN', 'isDraft': False, 'ci': 'failed',
                                  'reviewDecision': None, 'mergedAt': None, 'headRefOid': 'abc'}),
                'workflow': source({'format': None, 'verification_status': 'current', 'next_action': 'Decide stage 3',
                                    'gates': [{'stage': 3, 'status': 'pending', 'blocked': False},
                                              {'stage': 4, 'status': 'pending', 'blocked': True}],
                                    'decisions': [{'stage': 1, 'decision': 'approved', 'reviewer': 'me'}],
                                    'checklist': [{'status': 'passed'}, {'status': 'pending'}], 'errors': []}),
                'seed': source(status='not-linked'), 'handoff': source(status='not-linked')},
            'artifacts': [{'id': 'plan', 'title': 'Plan', 'documents': [
                {'label': 'Brief', 'relative_path': 'runs/r1/brief.md', 'status': 'ok',
                 'data': {'path': '/x', 'text': '# Brief\nDo the thing.'}}]}],
            'attention': ['tink-sdlc stage 3 is pending. Review the documents, then approve or request changes.',
                          'PR checks: failed.', 'The PR is open; GitHub does not report approval.',
                          'feature has 2 changed paths.'],
            'limits': 'Refresh before acting.'}
        patcher = patch.object(surface, 'snapshot', lambda config: self.snap)
        patcher.start()
        self.addCleanup(patcher.stop)

    def write_ledger(self, *rows, tail=''):
        lines = [json.dumps({'schema': 1, 'key': [change, 'backfill', 'gh', 0], 'change': change, 'phase': 'backfill',
                             'at': '2026-10-08T11:00:00+00:00', 'by': 't', 'fields': fields}) for change, fields in rows]
        self.ledger.write_text('\n'.join(lines) + '\n' + tail)

    def row(self, change_id=None, merged=None, operator=None, p1=0):
        return {'change_id': change_id, 'outcome': {'state': 'merged' if merged else 'open', 'reverted_by': None},
                'times': {'created': '2026-10-08T09:00:00Z', 'merged': merged, 'closed': merged, 'lead_hours': None},
                'size': {'product_add': 9, 'product_del': 1, 'files': 2, 'process_lines': 40},
                'review': {'rounds': 1, 'p1': p1}, 'operator': operator,
                'cost': {'llm.cost.total': 0.5, 'cost_known_share': 0.9}}

    def build(self):
        return surface.build(self.config, self.ledger)

    def test_links_the_ledger_row_by_pr_and_keeps_unknown_minutes_unknown(self):
        self.write_ledger(('o/r#7', self.row()))
        value = self.build()
        self.assertEqual(value['schema'], 'tink-surface/1')
        self.assertEqual(value['change']['ledger_key'], 'o/r#7')
        self.assertEqual(value['change']['link'], 'pr')
        self.assertEqual(value['ledger']['status'], 'ok')
        self.assertIsNone(value['ledger']['row']['operator'])  # unknown, never 0
        self.assertEqual(value['ledger']['row']['size']['process_lines'], 40)
        self.assertEqual(value['brief'], {'status': 'ok', 'label': 'Brief', 'relative_path': 'runs/r1/brief.md',
                                          'text': '# Brief\nDo the thing.', 'error': None})

    def test_change_id_links_first_and_a_disagreement_is_unavailable(self):
        (self.checkout / 'runs' / 'r1' / 'tools.json').write_text(json.dumps({'change': 'c261008abcd'}))
        self.write_ledger(('o/r#9', self.row('c261008abcd')), ('o/r#7', self.row()))
        value = self.build()
        self.assertEqual(value['change']['change_id'], 'c261008abcd')
        self.assertEqual(value['ledger']['status'], 'unavailable')
        self.assertIn('disagree', value['ledger']['error'])
        self.write_ledger(('o/r#7', self.row('c261008abcd')))
        value = self.build()
        self.assertEqual((value['change']['link'], value['ledger']['status']), ('change_id', 'ok'))

    def test_needs_you_holds_only_consequential_items(self):
        self.write_ledger(('o/r#7', self.row(p1=2)))
        value = self.build()
        kinds = [item['kind'] for item in value['needs_you']]
        self.assertEqual(kinds, ['gate', 'ci', 'p1'])
        self.assertIn('feature has 2 changed paths.', value['notes'])
        self.assertNotIn('PR checks: failed.', value['notes'])
        self.assertEqual(value['workflow']['data']['checklist'], {'total': 2, 'passed': 1})
        self.assertEqual(value['workflow']['data']['gates'][0], {'stage': 3, 'status': 'pending', 'blocked': False})

    def test_a_merged_change_has_no_gates_waiting(self):
        self.snap['sources']['github']['data'].update(state='MERGED', mergedAt='2026-10-08T10:00:00Z')
        self.write_ledger(('o/r#7', self.row(p1=2)))
        value = self.build()
        self.assertEqual(value['needs_you'], [])
        self.assertIn('tink-sdlc stage 3 is pending. Review the documents, then approve or request changes.',
                      value['notes'])

    def test_unavailable_source_needs_the_human(self):
        self.snap['sources']['github'] = source(status='unavailable', error='gh: not logged in')
        self.snap['attention'] = ['GitHub is unavailable. Its state is unknown.']
        self.write_ledger(('o/r#7', self.row()))
        value = self.build()
        self.assertEqual(value['pr'], {'status': 'unavailable', 'error': 'gh: not logged in', 'data': None})
        self.assertEqual(value['needs_you'], [{'kind': 'source', 'text': 'GitHub is unavailable. Its state is unknown.'}])

    def test_partial_last_line_is_tolerated_but_a_bad_middle_line_is_not(self):
        self.write_ledger(('o/r#7', self.row()), tail='{"schema": 1, "key"')
        self.assertEqual(self.build()['ledger']['status'], 'ok')
        self.ledger.write_text('not json\n' + self.ledger.read_text())
        value = self.build()
        self.assertEqual(value['ledger']['status'], 'unavailable')
        self.assertIn('line 1', value['ledger']['error'])

    def test_missing_ledger_and_missing_row(self):
        value = self.build()
        self.assertEqual((value['ledger']['status'], value['ledger']['row']), ('missing', None))
        self.write_ledger(('o/r#1', self.row()))
        value = self.build()
        self.assertEqual((value['ledger']['status'], value['ledger']['row']), ('ok', None))

    def test_week_hides_useful_per_hour_below_five_changes(self):
        operator = {'minutes': {'c2': 2, 'c5': 5, 'c10': 6}, 'minutes_by_week': {'2026-W41': {'c2': 2, 'c5': 5, 'c10': 6}}}
        self.write_ledger(('o/r#7', self.row(merged='2026-10-08T10:00:00Z', operator=operator)))
        week = surface.build(self.config, self.ledger, today='2026-10-08')['ledger']['week']
        self.assertEqual((week['name'], week['merged'], week['useful'], week['covered']), ('2026-W41', 1, 1, 1))
        self.assertEqual(week['operator_hours_c5'], round(5 / 60, 2))
        self.assertEqual(week['useful_per_hour'], {'c2': None, 'c5': None, 'c10': None})
        self.assertIn('fewer than 5', week['suppressed'])

    def test_missing_or_stale_selection_says_how_to_fix_it(self):
        self.config.unlink()
        value = self.build()
        self.assertEqual(value['selection']['status'], 'missing')
        self.assertIn('init', value['selection']['fix'])
        self.assertIsNone(value['change'])
        self.config.write_text(json.dumps({'schema': 1, 'work': str(self.root / 'gone.md'),
                                           'checkout': str(self.root / 'gone')}))
        value = self.build()
        self.assertEqual(value['selection']['status'], 'unavailable')
        self.assertIn('gone', value['selection']['error'])


class SurfaceCommandTest(unittest.TestCase):
    def test_cli_prints_json_and_writes_nothing(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            checkout = root / 'checkout'
            checkout.mkdir()
            env = {'GIT_AUTHOR_NAME': 't', 'GIT_AUTHOR_EMAIL': 't@t', 'GIT_COMMITTER_NAME': 't',
                   'GIT_COMMITTER_EMAIL': 't@t', 'PATH': '/usr/bin:/bin:/opt/homebrew/bin'}
            for argv in (['init', '-q', '-b', 'main'], ['commit', '-q', '--allow-empty', '-m', 'base']):
                subprocess.run(['git', *argv], cwd=checkout, check=True, env=env)
            work = root / 'work.md'
            work.write_text('+++\nschema = 1\ntitle = "Hunch"\nproject = "p"\nowner = "me"\nnext_action = "Think"\n+++\n')
            config = root / 'config.json'
            config.write_text(json.dumps({'schema': 1, 'work': str(work), 'checkout': str(checkout)}))
            ledger = root / 'changes.jsonl'
            ledger.write_text('')

            def tree():
                return sorted((str(p), p.stat().st_mtime_ns) for p in root.rglob('*'))
            before = tree()
            out = io.StringIO()
            with redirect_stdout(out):
                code = main(['--config', str(config), 'surface', '--json', '--ledger', str(ledger)])
            self.assertEqual(code, 0)
            value = json.loads(out.getvalue())
            self.assertEqual(value['change']['title'], 'Hunch')
            self.assertEqual(value['change']['link'], 'none')
            self.assertEqual(tree(), before)


if __name__ == '__main__':
    unittest.main()
