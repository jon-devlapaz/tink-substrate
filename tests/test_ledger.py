"""Ledger slice 1: backfill one row per PR from GitHub and git, then report views 1 and 3.

Ways this could fail, written before the code:
1. Process records (run folders) are counted as product lines, hiding process weight.
2. Re-running the sweep duplicates rows, so counts double.
3. A revert is missed, so a reverted change counts as useful.
4. Review rounds count every review, not reviews followed by a new push.
5. A merge commit missing from the local clone crashes the sweep instead of recording unknown size.
6. The sweep writes into the repositories it reads.
7. The report shows numbers for cells with fewer than 5 changes (false precision).
"""
import contextlib
import io
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from tink_substrate.__main__ import main
from tink_substrate import ledger


def git(repo, *args):
    return subprocess.run(['git', *args], cwd=repo, check=True, capture_output=True, text=True,
                          env={'GIT_AUTHOR_NAME': 't', 'GIT_AUTHOR_EMAIL': 't@t', 'GIT_COMMITTER_NAME': 't',
                               'GIT_COMMITTER_EMAIL': 't@t', 'PATH': '/usr/bin:/bin:/opt/homebrew/bin'}).stdout.strip()


class LedgerTest(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.repo = self.root / 'repo'
        self.repo.mkdir()
        git(self.repo, 'init', '-q', '-b', 'main')
        (self.repo / 'README.md').write_text('base\n')
        git(self.repo, 'add', '-A')
        git(self.repo, 'commit', '-qm', 'base')
        git(self.repo, 'checkout', '-qb', 'feature')
        (self.repo / 'src').mkdir()
        (self.repo / 'src' / 'a.py').write_text(''.join(f'line {i}\n' for i in range(10)))
        (self.repo / 'runs' / 'r1').mkdir(parents=True)
        (self.repo / 'runs' / 'r1' / 'log.md').write_text(''.join(f'log {i}\n' for i in range(20)))
        git(self.repo, 'add', '-A')
        git(self.repo, 'commit', '-qm', 'feature')
        git(self.repo, 'checkout', '-q', 'main')
        git(self.repo, 'merge', '-q', '--no-ff', 'feature', '-m', 'Merge pull request #1')
        self.merge = git(self.repo, 'rev-parse', 'HEAD')
        self.ledger = self.root / 'ledger' / 'changes.jsonl'
        self.prs = [
            {'number': 1, 'title': 'Add a', 'state': 'MERGED', 'isDraft': False, 'body': '',
             'createdAt': '2026-10-05T10:00:00Z', 'mergedAt': '2026-10-05T14:00:00Z', 'closedAt': '2026-10-05T14:00:00Z',
             'headRefName': 'feature', 'baseRefName': 'main', 'mergeCommit': {'oid': self.merge},
             'commits': [{'oid': 'c1', 'committedDate': '2026-10-05T09:00:00Z'},
                         {'oid': 'c2', 'committedDate': '2026-10-05T12:00:00Z'},
                         {'oid': 'c3', 'committedDate': '2026-10-05T13:00:00Z'}],
             'reviews': [{'state': 'COMMENTED', 'submittedAt': '2026-10-05T11:00:00Z'},
                         {'state': 'COMMENTED', 'submittedAt': '2026-10-05T11:30:00Z'},
                         {'state': 'APPROVED', 'submittedAt': '2026-10-05T13:30:00Z'}]},
            {'number': 2, 'title': 'Revert "Add a"', 'state': 'MERGED', 'isDraft': False,
             'body': 'Reverts o/r#1', 'createdAt': '2026-10-06T10:00:00Z', 'mergedAt': '2026-10-06T11:00:00Z',
             'closedAt': '2026-10-06T11:00:00Z', 'headRefName': 'revert-1', 'baseRefName': 'main',
             'mergeCommit': {'oid': 'f' * 40}, 'commits': [], 'reviews': []},
            {'number': 3, 'title': 'Abandoned', 'state': 'CLOSED', 'isDraft': False, 'body': '',
             'createdAt': '2026-10-06T10:00:00Z', 'mergedAt': None, 'closedAt': '2026-10-06T12:00:00Z',
             'headRefName': 'x', 'baseRefName': 'main', 'mergeCommit': None, 'commits': [], 'reviews': []},
        ]
        self.comments = {1: [{'body': '![P1 Badge](x) fix this'}, {'body': '![P2 Badge](x) nit'}], 2: [], 3: []}

        def fake_gh(args):
            if args[:2] == ['pr', 'list']:
                return json.dumps([{k: v for k, v in pr.items() if k != 'commits'} for pr in self.prs])
            if args[:2] == ['pr', 'view']:
                return json.dumps({'commits': self.prs[int(args[2]) - 1]['commits']})
            if args[0] == 'api':
                number = int(args[1].split('/')[-2])
                return json.dumps(self.comments[number])
            raise AssertionError(args)

        patcher = patch.object(ledger, 'run_gh', fake_gh)
        patcher.start()
        self.addCleanup(patcher.stop)

    def cli(self, *argv):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = main(['ledger', *argv])
        return code, out.getvalue()

    def sweep(self):
        return self.cli('sweep', '--ledger', str(self.ledger), '--repo', f'o/r={self.repo}')

    def rows(self):
        return ledger.fold(ledger.read(self.ledger))

    def test_sweep_records_one_row_per_pr_with_process_lines_separate(self):
        code, _ = self.sweep()
        self.assertEqual(code, 0)
        rows = self.rows()
        self.assertEqual(sorted(rows), ['o/r#1', 'o/r#2', 'o/r#3'])
        first = rows['o/r#1']
        self.assertEqual(first['size'], {'product_add': 10, 'product_del': 0, 'files': 2, 'process_lines': 20})
        self.assertEqual(first['outcome'], {'state': 'merged', 'reverted_by': 'o/r#2'})
        self.assertEqual(first['times']['lead_hours'], 4.0)
        self.assertEqual(first['vcs'], {'vcs.repository.name': 'o/r', 'vcs.change.id': '1',
                                        'vcs.ref.head.name': 'feature', 'vcs.ref.head.revision': self.merge})
        self.assertEqual(rows['o/r#3']['outcome']['state'], 'closed')

    def test_review_rounds_count_reviews_followed_by_a_push(self):
        self.sweep()
        review = self.rows()['o/r#1']['review']
        # two reviews before the 12:00 push are one round; the 13:30 approval has no push after it
        self.assertEqual(review['rounds'], 1)
        self.assertEqual(review['p1'], 1)
        self.assertEqual(review['pushes_after_open'], 2)

    def test_missing_merge_commit_records_unknown_size(self):
        self.sweep()
        self.assertIsNone(self.rows()['o/r#2']['size'])

    def test_rerunning_the_sweep_adds_no_duplicate_lines(self):
        self.sweep()
        before = self.ledger.read_text()
        self.sweep()
        self.assertEqual(self.ledger.read_text(), before)
        lines = [json.loads(line) for line in before.splitlines()]
        self.assertTrue(all(line['schema'] == 1 and line['key'][0] == line['change'] for line in lines))

    def test_sweep_never_changes_the_repository(self):
        head, status = git(self.repo, 'rev-parse', 'HEAD'), git(self.repo, 'status', '--porcelain')
        self.sweep()
        self.assertEqual((git(self.repo, 'rev-parse', 'HEAD'), git(self.repo, 'status', '--porcelain')), (head, status))

    def test_report_hides_small_cells(self):
        self.sweep()
        code, out = self.cli('report', '--ledger', str(self.ledger))
        self.assertEqual(code, 0)
        self.assertIn('View 1', out)
        self.assertIn('View 3', out)
        self.assertIn('—', out)  # 2 merged changes: below n=5, no medians shown
        self.assertNotIn('4.0', out)
        self.assertIn('merged 2', out)
        self.assertIn('reverted 1', out)


if __name__ == '__main__':
    unittest.main()
