"""Run-boundary failures, using real Git objects and frozen package copies."""
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tink_substrate.prepare import prepare_run, workflow, resolve_sources, SOURCES
from scripts.check_install import check

ROOT = Path(__file__).resolve().parents[1]


def git(root, *args):
    return subprocess.check_output(['git', '-c', 'core.fsmonitor=false', '-C', str(root), *args], text=True).strip()


def commit(root):
    git(root, 'add', '.')
    git(root, '-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid', 'commit', '-qm', 'fixture')
    return git(root, 'rev-parse', 'HEAD')


class PrepareTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.checkout = self.root / 'target'
        self.checkout.mkdir()
        subprocess.run(['git', 'init', '-q', str(self.checkout)], check=True)
        (self.checkout / 'README.md').write_text('user project')
        commit(self.checkout)
        self.cache = self.root / 'sources'
        self.cache.mkdir()
        self.sources = {}
        for name, spec in SOURCES.items():
            repo = self.cache / name
            repo.mkdir()
            subprocess.run(['git', 'init', '-q', str(repo)], check=True)
            (repo / 'LICENSE').write_text('fixture license')
            if name == 'tink-substrate':
                for directory in ('tink_substrate', 'docs', 'scripts', 'skills'):
                    shutil.copytree(ROOT / directory, repo / directory,
                                    ignore=shutil.ignore_patterns('__pycache__'))
                (repo / 'AGENTS.md').write_text('fixture instructions')
            elif name == 'tink-skills':
                skill = repo / 'skills/seed-me'
                (skill / 'scripts').mkdir(parents=True)
                (skill / 'SKILL.md').write_text('---\nname: seed-me\nmetadata:\n  version: "2.0.0"\n---\n')
                (skill / 'scripts/session.py').write_text('import argparse; argparse.ArgumentParser().parse_args()')
            else:
                assets = repo / 'assets'
                assets.mkdir()
                for directory in ('_system', '_shared', 'stages', '.tink'):
                    shutil.copytree(ROOT / directory, assets / directory,
                                    ignore=shutil.ignore_patterns('__pycache__'))
                (assets / 'manifest.json').write_text('{"version": "1.20.0"}')
                (repo / 'scripts').mkdir()
                (repo / 'scripts/init.py').write_text("""import argparse,json,shutil
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('target');p.add_argument('--check',action='store_true');p.add_argument('--upgrade',action='store_true');a=p.parse_args()
t=Path(a.target);src=Path(__file__).resolve().parents[1]/'assets'
if (t/'_system/scaffold.json').exists():
 for name in ('_system/scripts/sdlc.py',):
  if (t/name).read_bytes() != (src/name).read_bytes(): raise SystemExit('customized managed file')
if not a.check:
 for name in ('_system','_shared','stages','.tink'):
  if not (t/name).exists(): shutil.copytree(src/name,t/name)
 (t/'AGENTS.md').touch(exist_ok=True)
""")
            sha = commit(repo)
            self.sources[name] = {'url': spec['url'], 'revision': sha, 'workflow': spec['workflow'],
                                  'ci_run': 1, 'version': None}

    def prepare(self, run='trial'):
        with patch('tink_substrate.prepare.resolve_sources', return_value=self.sources), \
             patch('tink_substrate.prepare.fetch_sources', return_value=self.cache):
            return prepare_run(self.checkout, run, self.root / 'packages')

    def test_new_run_records_exact_objects_and_resume_is_offline(self):
        record = self.prepare()
        package = Path(record['package'])
        self.assertEqual(check(package), self.sources['tink-substrate']['revision'])
        self.assertEqual(record['components']['tink-skills']['version'], '2.0.0')
        self.assertTrue((self.checkout / 'runs/trial/tools.json').is_file())
        commit(self.checkout)
        (self.cache / 'tink-skills/skills/seed-me/SKILL.md').write_text('new mutable upstream')
        with patch('tink_substrate.prepare.resolve_sources', side_effect=AssertionError('network on resume')):
            self.assertEqual(prepare_run(self.checkout, 'trial', self.root / 'packages'), record)
        self.assertEqual(workflow(self.checkout, 'trial', ['status', 'trial', '--json']), 0)

    def test_integrity_failure_refuses_resume(self):
        record = self.prepare()
        (Path(record['package']) / 'LICENSE').write_text('changed')
        with self.assertRaisesRegex(ValueError, 'changed'):
            prepare_run(self.checkout, 'trial', self.root / 'packages')

    def test_target_runtime_changed_refuses_resume(self):
        self.prepare()
        (self.checkout / '_system/scripts/sdlc.py').write_text('different runtime')
        with self.assertRaisesRegex(ValueError, 'workflow changed'):
            prepare_run(self.checkout, 'trial', self.root / 'packages')

    def test_dirty_new_target_and_existing_unrecorded_run_refused(self):
        (self.checkout / 'README.md').write_text('other work')
        with self.assertRaisesRegex(ValueError, 'clean'):
            self.prepare()
        commit(self.checkout)
        (self.checkout / 'runs/trial').mkdir(parents=True)
        with self.assertRaisesRegex(ValueError, 'existing run'):
            self.prepare()

    def test_failed_ci_and_smoke_leave_target_untouched(self):
        with patch('tink_substrate.prepare.resolve_sources', side_effect=ValueError('CI pending')):
            with self.assertRaisesRegex(ValueError, 'CI pending'):
                prepare_run(self.checkout, 'trial', self.root / 'packages')
        with patch('tink_substrate.prepare.smoke_package', side_effect=ValueError('incompatible')):
            with self.assertRaisesRegex(ValueError, 'incompatible'):
                self.prepare()
        self.assertEqual(git(self.checkout, 'status', '--porcelain'), '')
        self.assertFalse((self.checkout / 'runs').exists())

    def test_package_storage_inside_target_refused(self):
        with self.assertRaisesRegex(ValueError, 'outside'):
            prepare_run(self.checkout, 'trial', self.checkout / 'packages')

    def test_record_from_other_checkout_and_symlink_refused(self):
        self.prepare()
        path = self.checkout / 'runs/trial/tools.json'
        data = json.loads(path.read_text()); data['checkout'] = str(self.root)
        path.write_text(json.dumps(data))
        with self.assertRaisesRegex(ValueError, 'identity'):
            prepare_run(self.checkout, 'trial', self.root / 'packages')
        path.unlink(); path.symlink_to(self.root / 'missing')
        with self.assertRaisesRegex(ValueError, 'symlink'):
            prepare_run(self.checkout, 'trial', self.root / 'packages')

    def test_main_moving_during_smoke_refuses_start(self):
        updated = {name: dict(value) for name, value in self.sources.items()}
        updated['tink-skills']['revision'] = 'b' * 40
        with patch('tink_substrate.prepare.resolve_sources', side_effect=[self.sources, updated]), \
             patch('tink_substrate.prepare.fetch_sources', return_value=self.cache):
            with self.assertRaisesRegex(ValueError, 'changed during preparation'):
                prepare_run(self.checkout, 'trial', self.root / 'packages')
        self.assertEqual(git(self.checkout, 'status', '--porcelain'), '')

    def test_target_customization_and_required_tink_refuse_start(self):
        shutil.copytree(ROOT / '_system', self.checkout / '_system')
        (self.checkout / '_system/scripts/sdlc.py').write_text('customized')
        commit(self.checkout)
        with self.assertRaisesRegex(ValueError, 'customized'):
            self.prepare()
        self.assertFalse((self.checkout / 'runs/trial').exists())
        shutil.copyfile(ROOT / '_system/scripts/sdlc.py', self.checkout / '_system/scripts/sdlc.py')
        (self.checkout / '_system/verification.json').write_text('{"require_tink": true, "checks": []}')
        commit(self.checkout)
        with self.assertRaisesRegex(ValueError, 'requires Tink'):
            self.prepare()

    def test_workflow_cannot_mutate_a_different_run_or_use_global_tools(self):
        self.prepare()
        for arguments in [['stage', 'other', '1'], ['skills', 'tink', '--', 'update'],
                          ['new', 'other'], ['status', 'other']]:
            with self.subTest(arguments=arguments), self.assertRaises(ValueError):
                workflow(self.checkout, 'trial', arguments)

    def test_package_internal_symlink_is_refused_on_resume(self):
        record = self.prepare()
        package = Path(record['package'])
        license = package / 'LICENSE'
        copy = package / 'license-copy'; copy.write_bytes(license.read_bytes())
        license.unlink(); license.symlink_to(copy)
        with self.assertRaisesRegex(ValueError, 'symlink'):
            prepare_run(self.checkout, 'trial', self.root / 'packages')


class EligibilityTests(unittest.TestCase):
    def response(self, endpoint):
        if endpoint.endswith('/commits/main'):
            return {'sha': 'a' * 40}
        return {'workflow_runs': [{'id': 42, 'head_sha': 'a' * 40, 'head_branch': 'main',
                  'event': 'push', 'status': 'completed', 'conclusion': 'success'}]}

    def test_exact_head_success_for_each_fixed_source(self):
        with patch('tink_substrate.prepare.github', side_effect=self.response):
            sources = resolve_sources()
        self.assertEqual(set(sources), set(SOURCES))
        self.assertTrue(all(s['revision'] == 'a' * 40 for s in sources.values()))

    def test_pending_failed_wrong_head_or_missing_ci_never_falls_back(self):
        for change in [{'status': 'in_progress'}, {'conclusion': 'failure'},
                       {'head_sha': 'b' * 40}, {'event': 'pull_request'}, {'id': 'bad'}]:
            def respond(endpoint):
                value = self.response(endpoint)
                if 'workflow_runs' in value: value['workflow_runs'][0].update(change)
                return value
            with self.subTest(change=change), patch('tink_substrate.prepare.github', side_effect=respond):
                with self.assertRaises(ValueError): resolve_sources()

    def test_newer_pending_attempt_does_not_accept_old_success(self):
        def respond(endpoint):
            value = self.response(endpoint)
            if 'workflow_runs' in value:
                pending = dict(value['workflow_runs'][0], id=43, status='in_progress', conclusion=None)
                value['workflow_runs'].append(pending)
            return value
        with patch('tink_substrate.prepare.github', side_effect=respond):
            with self.assertRaises(ValueError): resolve_sources()
