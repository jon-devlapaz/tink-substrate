import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from tink_substrate.sources import (SourceError, artifact, attention, changes, git_state,
                                    observe, parse_pr, pr_state, read_record, snapshot, workflow_state)


class GitTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'repo'
        self.root.mkdir()
        self.git('init', '-b', 'main')
        self.git('config', 'user.email', 'test@example.test')
        self.git('config', 'user.name', 'Test')
        (self.root / 'file.txt').write_text('baseline')
        self.git('add', '.')
        self.git('commit', '-m', 'baseline')

    def git(self, *args):
        return subprocess.check_output(['git', '-C', str(self.root), *args], stderr=subprocess.DEVNULL, text=True)

    def test_clean_dirty_and_other_worktrees(self):
        second = Path(self.temp.name) / 'second tree'
        self.git('worktree', 'add', '-b', 'feature', str(second))
        (second / 'untracked.txt').write_text('work')
        s = git_state(self.root)
        self.assertEqual(s['branch'], 'main')
        self.assertEqual(len(s['branches']), 2)
        first = next(t for t in s['worktrees'] if t['selected'])
        other = next(t for t in s['worktrees'] if not t['selected'])
        self.assertFalse(first['changes']['data']['dirty'])
        self.assertTrue(other['changes']['data']['dirty'])
        self.assertEqual(other['changes']['data']['files'][0]['path'], 'untracked.txt')

    def test_rename_spaces_and_newline_paths(self):
        self.git('mv', 'file.txt', 'new name.txt')
        (self.root / 'line\nbreak.txt').write_text('x')
        s = changes(self.root)
        self.assertEqual(s['count'], 2)
        self.assertEqual({x['path'] for x in s['files']}, {'new name.txt', 'line\nbreak.txt'})

    def test_detached_head_and_invalid_checkout(self):
        self.git('checkout', '--detach')
        self.assertEqual(git_state(self.root)['branch'], '(detached)')
        self.assertEqual(observe(lambda: git_state(Path(self.temp.name)))['status'], 'unavailable')

    def test_missing_worktree_is_unknown_not_clean(self):
        second = Path(self.temp.name) / 'gone'
        self.git('worktree', 'add', '-b', 'gone', str(second))
        moved = Path(self.temp.name) / 'moved'
        second.rename(moved)
        s = git_state(self.root)
        other = next(t for t in s['worktrees'] if not t['selected'])
        self.assertEqual(other['changes']['status'], 'unavailable')


class ContractTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.record = read_record(Path(__file__).parent / 'fixtures/work.md')

    def test_artifact_escape_and_symlink_rejected(self):
        outside = self.root.parent / 'outside.md'
        (self.root / 'link.md').symlink_to(outside)
        for path in ('../outside.md', str(outside), 'link.md'):
            with self.subTest(path=path), self.assertRaises(SourceError):
                artifact(self.root, path)
        self.assertEqual(observe(lambda: artifact(self.root, 'missing.md'))['status'], 'unavailable')

    def test_workflow_requires_explicit_trust_and_does_not_execute_by_discovery(self):
        with patch('tink_substrate.sources.command') as call:
            with self.assertRaises(SourceError):
                workflow_state(self.root, self.record, False)
            call.assert_not_called()

    def workflow(self, status='current', passed=True, run=None, **extra):
        script = self.root / '_system/scripts/sdlc.py'
        script.parent.mkdir(parents=True, exist_ok=True)
        script.write_text('')
        value = dict(protocol='tink-sdlc', api_version=1, workspace=str(self.root.resolve()),
                     run={**dict(slug=self.record['run'], verification_status=status, verification={'passed': passed},
                                 checklist=[], gates=[], errors=[], decisions=[]), **(run or {})})
        value.update(extra)
        with patch('tink_substrate.sources.command', return_value=json.dumps(value)):
            return observe(lambda: workflow_state(self.root, self.record, True))

    def test_current_requires_passing_receipt_and_known_identity(self):
        self.assertEqual(self.workflow()['status'], 'ok')
        for kwargs in [{'passed':False}, {'status':'magic'}, {'api_version':2}, {'api_version':True}, {'workspace':'/elsewhere'}]:
            self.assertEqual(self.workflow(**kwargs)['status'], 'unavailable')
        self.assertEqual(self.workflow(status='stale', passed=False)['data']['verification_status'], 'stale')

    def test_invalid_and_external_pr_urls_rejected(self):
        for url in ('https://evil.test/a/b/pull/1', 'file:///etc/passwd', 'https://github.com/a/b/pull/1;whoami'):
            with self.assertRaises(SourceError):
                parse_pr(url)

    def test_ci_empty_pending_skipped_and_unknown_never_pass(self):
        samples = [([], 'none'), ([{'__typename':'CheckRun','status':'IN_PROGRESS'}], 'pending'),
                   ([{'__typename':'CheckRun','status':'COMPLETED','conclusion':'SKIPPED'}], 'includes skipped checks'),
                   ([{'__typename':'CheckRun','status':'COMPLETED','conclusion':'NEW_STATE'}], 'unknown'),
                   ([{'__typename':'CheckRun','status':'COMPLETED','conclusion':'SUCCESS'}], 'passed')]
        for checks, expected in samples:
            with patch('tink_substrate.sources.command', return_value=json.dumps(dict(url=self.record['pr'],state='OPEN',statusCheckRollup=checks))):
                self.assertEqual(pr_state(self.record['pr'])['ci'], expected)

    def test_pr_head_mismatch_and_verification_staleness_surface(self):
        sources = {name:dict(status='ok',data={}) for name in ('git','github','workflow','seed','handoff')}
        sources['git']['data'] = dict(branch=self.record['branch'],head='local',worktrees=[])
        sources['github']['data'] = dict(headRefOid='remote',state='OPEN',ci='passed')
        sources['workflow']['data'] = dict(verification_status='stale')
        text = ' '.join(attention(self.record, sources))
        self.assertIn('head differs', text)
        self.assertIn('stale', text)
        self.assertIn('does not report approval', text)

    def sources(self, **data):
        value = {name: dict(status='ok', data={}) for name in ('git', 'github', 'workflow', 'seed', 'handoff')}
        value['git']['data'] = dict(branch=self.record['branch'], head='same', worktrees=[])
        value['github']['data'] = dict(headRefOid='same', state='OPEN', ci='passed', reviewDecision='APPROVED')
        for name, extra in data.items():
            value[name]['data'].update(extra)
        return value

    def test_sdlc_errors_and_pending_human_decisions_surface(self):
        gates = [{'stage': 2, 'status': 'pending', 'blocked': False}, {'stage': 3, 'status': 'pending', 'blocked': True}]
        blocked = self.workflow(status='blocked', passed=False, run=dict(gates=gates))['data']
        text = ' '.join(attention(self.record, self.sources(workflow=blocked)))
        self.assertIn('stage 2 is pending', text)
        self.assertNotIn('stage 3', text)
        requested = self.workflow(status='blocked', passed=False, run=dict(gates=[{'stage': 2, 'status': 'changes-requested', 'blocked': False}]))['data']
        self.assertIn('Revise the work before requesting another decision.', ' '.join(attention(self.record, self.sources(workflow=requested))))
        errors = ['Locked test input changed or disappeared: tests/test_race.py']
        current = self.workflow(run=dict(errors=errors))['data']
        self.assertIn('tink-sdlc reports: ' + errors[0], attention(self.record, self.sources(workflow=current)))
        # None also stands for an omitted field: unknown is not the same as "no gates" or "no errors".
        for run in [dict(gates=None), dict(gates='approved'), dict(gates=[{'stage': 3, 'status': 'magic', 'blocked': False}]),
                    dict(errors=None), dict(errors='none'), dict(decisions=None), dict(decisions=[{'stage': 3, 'decision': 'maybe'}])]:
            with self.subTest(run=run):
                self.assertEqual(self.workflow(run=run)['status'], 'unavailable')

    def test_pr_review_state_is_specific(self):
        text = attention(self.record, self.sources(github=dict(reviewDecision='CHANGES_REQUESTED', isDraft=True)))
        self.assertIn('GitHub reports changes requested on the PR.', text)
        self.assertIn('The PR is a draft.', text)
        self.assertEqual(attention(self.record, self.sources()), [])

    def test_merged_pr_is_distinct_from_closed_and_preserves_other_warnings(self):
        merged = self.sources(github=dict(state='MERGED'))
        self.assertEqual(attention(self.record, merged), [])
        closed = attention(self.record, self.sources(github=dict(state='CLOSED')))
        self.assertTrue(any('closed without merging' in item for item in closed))
        merged['git']['data']['head'] = 'different'
        merged['git']['data']['worktrees'] = [dict(path='/example', branch='work',
            changes=dict(status='ok', data=dict(dirty=True, count=2)))]
        merged['workflow']['data'] = dict(verification_status='stale')
        warnings = attention(self.record, merged)
        self.assertTrue(any('head differs' in item for item in warnings))
        self.assertIn('work has 2 changed paths.', warnings)
        self.assertIn('Local verification is stale.', warnings)
        merged['workflow'] = dict(status='unavailable')
        self.assertIn('Verification is unavailable. Its state is unknown.', attention(self.record, merged))

    def test_hunch_record_without_links_reads_as_not_linked(self):
        path = self.root / 'hunch.md'
        path.write_text('+++\nschema = 1\ntitle = "Try a hunch"\nproject = "p"\nowner = "Example owner"\n'
                        'next_action = "Run Seed Me."\n+++\nWhy this might matter.\n')
        record = read_record(path)
        self.assertEqual([record[k] for k in ('branch', 'run', 'pr', 'seed', 'handoff')], [None] * 5)
        config = dict(work=str(path), checkout=str(self.root), trust_sdlc=True)
        with patch('tink_substrate.sources.git_state', return_value={'branch': 'main', 'head': 'a', 'worktrees': []}), \
             patch('tink_substrate.sources.command') as call:
            value = snapshot(config)
        call.assert_not_called()
        self.assertEqual(value['sources']['git']['status'], 'ok')
        for name in ('github', 'workflow', 'seed', 'handoff'):
            self.assertEqual(value['sources'][name]['status'], 'not-linked')
            self.assertNotIn('data', value['sources'][name])
        self.assertEqual(value['attention'], [])
        for line in ('pr = ""', 'run = "../x"', 'seed = 3'):
            with self.subTest(line=line), self.assertRaises(SourceError):
                path.write_text(f'+++\nschema = 1\ntitle = "t"\nproject = "p"\nowner = "o"\nnext_action = "n"\n{line}\n+++\n')
                read_record(path)

    def test_source_failure_does_not_hide_other_sources(self):
        config=dict(work=str(Path(__file__).parent / 'fixtures/work.md'),checkout=str(self.root),trust_sdlc=False)
        with patch('tink_substrate.sources.git_state', return_value={'branch':self.record['branch'],'head':'a','worktrees':[]}), \
             patch('tink_substrate.sources.pr_state', side_effect=SourceError('Network unavailable')):
            value = snapshot(config)
        self.assertEqual(value['sources']['git']['status'], 'ok')
        self.assertEqual(value['sources']['github']['status'], 'unavailable')
        self.assertTrue(any('GitHub is unavailable' in a for a in value['attention']))
