import re
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.install_skill import install, package_instructions
from scripts.check_install import check

ROOT = Path(__file__).resolve().parents[1]


class InstallSkillTests(unittest.TestCase):
    def test_independent_copy_and_repeat_preserves_destination(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / 'source'
            for name in ('tink_substrate/__init__.py', 'docs/start-a-change.md',
                         'LICENSE', 'AGENTS.md', 'skills/tink-substrate/SKILL.md', 'scripts/check_install.py'):
                path = source / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(name)
            subprocess.run(['git', 'init', '-q', str(source)], check=True)
            subprocess.run(['git', '-C', str(source), 'add', '.'], check=True)
            subprocess.run(['git', '-C', str(source), '-c', 'user.name=Test',
                            '-c', 'user.email=test@example.invalid', 'commit', '-qm', 'fixture'], check=True)
            (source / 'docs/private.txt').write_text('must not ship')
            (source / 'docs/start-a-change.md').write_text('uncommitted edit')
            cache = root / 'cache/tool'
            cache.mkdir(parents=True)
            subprocess.run(['git', 'init', '-q', str(cache)], check=True)
            (cache / 'LICENSE').write_text('license')
            subprocess.run(['git', '-C', str(cache), 'add', '.'], check=True)
            subprocess.run(['git', '-C', str(cache), '-c', 'user.name=Test',
                            '-c', 'user.email=test@example.invalid', 'commit', '-qm', 'fixture'], check=True)
            revision = subprocess.check_output(['git', '-C', str(cache), 'rev-parse', 'HEAD'], text=True).strip()
            (cache / 'LICENSE').write_text('uncommitted modification')
            with patch('scripts.install_skill.PINS', {'tool': ('unused', revision)}):
                destination = install(source, root / 'installed', root / 'cache')
                self.assertEqual((destination / '.substrate-tools/tool/LICENSE').read_text(), 'license')
                self.assertFalse((destination / 'docs/private.txt').exists())
                self.assertEqual((destination / 'docs/start-a-change.md').read_text(), 'docs/start-a-change.md')
                self.assertFalse(any(p.is_symlink() for p in destination.rglob('*')))
                (source / 'docs/start-a-change.md').unlink()
                self.assertTrue((destination / 'docs/start-a-change.md').is_file())
                with self.assertRaisesRegex(ValueError, 'already exists'):
                    install(source, destination, root / 'cache')
                self.assertTrue((destination / 'installation.json').is_file())
                self.assertTrue(check(destination))
                (destination / 'LICENSE').write_text('modified')
                with self.assertRaisesRegex(ValueError, 'changed'):
                    check(destination)
                (destination / 'installation.json').unlink()
                with self.assertRaises(FileNotFoundError):
                    check(destination)

    def test_existing_symlink_is_not_followed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            link = root / 'installed'
            link.symlink_to(root / 'missing', target_is_directory=True)
            with self.assertRaisesRegex(ValueError, 'already exists'):
                install(root, link)
            self.assertTrue(link.is_symlink())
            self.assertFalse((root / 'missing').exists())

    def test_failed_copy_leaves_no_partial_installation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with self.assertRaises(subprocess.CalledProcessError):
                install(root / 'missing', root / 'installed')
            self.assertFalse((root / 'installed').exists())
            self.assertEqual(list(root.iterdir()), [])

    def test_package_instructions_drop_workspace_blocks(self):
        text = ('# Rules\n\nKeep this.\n\n\n<!-- AI-Native SDLC Router -->\n## SDLC Workspace\n- Read `_system/SDLC.md`.\n'
                '<!-- End AI-Native SDLC Router -->\n\n<!-- tink:rules begin skillset=x digest=1 -->\n- rule\n'
                '<!-- tink:rules end -->\n')
        self.assertEqual(package_instructions(text), '# Rules\n\nKeep this.\n')
        self.assertEqual(package_instructions('# Rules\n'), '# Rules\n')
        with self.assertRaisesRegex(ValueError, 'unmatched'):
            package_instructions('# Rules\n<!-- tink:rules begin skillset=x -->\n- rule\n')

    def test_installed_agents_md_names_only_packaged_paths(self):
        # Installs this repository's committed HEAD; AGENTS.md does not need the pinned tools.
        with tempfile.TemporaryDirectory() as directory, patch('scripts.install_skill.PINS', {}):
            destination = install(ROOT, Path(directory) / 'installed')
            text = (destination / 'AGENTS.md').read_text()
            self.assertIn('docs/finish-a-change.md', text)
            for marker in ('SDLC Router', 'tink:rules', '_system/', 'stages/', '_shared/'):
                self.assertNotIn(marker, text)
            # AGENTS.md names tests/fixtures/ as the source repository's, not the package's.
            paths = [p for p in re.findall(r'`([^`\s]+/[^`\s]*)`', text) if not p.startswith('tests/')]
            self.assertEqual([p for p in paths if not (destination / p).exists()], [])
