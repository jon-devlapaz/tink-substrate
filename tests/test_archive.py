import hashlib
import json
from pathlib import Path
import subprocess
import tarfile
import tempfile
import unittest

from tink_substrate.archive import archive_run


class ArchiveTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.repo = self.root / 'repo'
        self.repo.mkdir()
        self.git('init', '-q')
        self.git('config', 'user.name', 'Test')
        self.git('config', 'user.email', 'test@example.invalid')
        self.run = self.repo / 'runs/example'
        self.run.mkdir(parents=True)
        (self.run / 'retro.md').write_text('Actual outcome and limits.\n')
        (self.repo / 'app.py').write_text('print("example")\n')
        self.commit()

    def git(self, *args):
        return subprocess.check_output(['git', '-C', str(self.repo), *args], stderr=subprocess.PIPE)

    def commit(self):
        self.git('add', '.')
        self.git('commit', '-qm', 'fixture')

    def save(self, phase='delivery', **kwargs):
        return archive_run(self.repo, kwargs.get('project', 'demo'), 'example', phase,
                           kwargs.get('root', self.root / 'archive'))

    def test_complete_snapshot_checksums_and_repeat_do_not_overwrite(self):
        first = self.save()
        original = (first / 'SHA256SUMS').read_bytes()
        (self.run / 'retro.md').write_text('Later observation.\n')
        self.commit()
        second = self.save()
        self.assertNotEqual(first, second)
        self.assertEqual((first / 'SHA256SUMS').read_bytes(), original)
        self.assertEqual((first / 'runs/example/retro.md').read_text(), 'Actual outcome and limits.\n')
        for line in (second / 'SHA256SUMS').read_text().splitlines():
            digest, path = line.split('  ', 1)
            self.assertEqual(hashlib.sha256((second / path).read_bytes()).hexdigest(), digest)
        self.assertEqual(json.loads((second / 'metadata.json').read_text())['head'], self.git('rev-parse', 'HEAD').decode().strip())
        with tarfile.open(second / 'source.tar') as archive:
            self.assertEqual(archive.extractfile('app.py').read(), b'print("example")\n')

    def test_dirty_and_untracked_files_are_refused(self):
        for path in (self.repo / 'app.py', self.repo / 'untracked.txt'):
            path.write_text('unsaved')
            with self.assertRaisesRegex(ValueError, 'uncommitted'):
                self.save()
            if path.name == 'app.py':
                self.git('restore', 'app.py')
        self.assertFalse((self.root / 'archive').exists())

    def test_closure_requires_its_own_committed_record(self):
        with self.assertRaisesRegex(ValueError, 'closure.md'):
            self.save('closure')
        (self.run / 'closure.md').write_text('Actual merge observation.\n')
        self.commit()
        self.assertTrue((self.save('closure') / 'runs/example/closure.md').is_file())

    def test_missing_retro_is_refused(self):
        (self.run / 'retro.md').unlink()
        self.commit()
        with self.assertRaisesRegex(ValueError, 'retro.md'):
            self.save()

    def test_unsafe_destination_and_names_are_refused(self):
        with self.assertRaisesRegex(ValueError, 'outside'):
            self.save(root=self.repo / 'archive')
        with self.assertRaisesRegex(ValueError, 'simple names'):
            self.save(project='../escape')

    def test_run_symlink_is_not_followed(self):
        (self.run / 'outside').symlink_to('/etc/passwd')
        self.commit()
        with self.assertRaisesRegex(ValueError, 'link'):
            self.save()
