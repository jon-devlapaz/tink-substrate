import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
import venv
from unittest.mock import patch

from tink_substrate import __version__
from tink_substrate.__main__ import main


ROOT = Path(__file__).resolve().parents[1]


class VersionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.env = dict(os.environ, HOME=str(self.root), PYTHONDONTWRITEBYTECODE='1')
        self.env.pop('PYTHONPATH', None)
        self.env.pop('PYTHONHOME', None)

    def command(self, argv, cwd=ROOT, env=None):
        return subprocess.run(argv, cwd=cwd, env=env or self.env,
                              capture_output=True, text=True, timeout=90)

    def assert_version(self, result):
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, f'tink-substrate {__version__}\n')
        self.assertEqual(result.stderr, '')

    def test_source_version_without_config_or_subcommand(self):
        self.assert_version(self.command([sys.executable, '-m', 'tink_substrate', '--version']))
        self.assertEqual(list(self.root.iterdir()), [])

    def test_missing_malformed_and_selected_config_unchanged(self):
        config = self.root / 'selection.json'
        work = self.root / 'work.md'
        work.write_text('Do not read this work item.\n')
        for content in (None, '{invalid json', json.dumps({'schema': 1, 'work': str(work)})):
            with self.subTest(content=content):
                if content is not None:
                    config.write_text(content)
                before = {p.name: p.read_bytes() for p in self.root.iterdir()}
                self.assert_version(self.command([sys.executable, '-m', 'tink_substrate',
                                                  '--config', str(config), '--version']))
                self.assertEqual(before, {p.name: p.read_bytes() for p in self.root.iterdir()})

    def test_version_exits_before_reading_config_or_running_commands(self):
        with patch('pathlib.Path.read_text', side_effect=AssertionError('read config')), \
             patch('tink_substrate.__main__.snapshot', side_effect=AssertionError('read work')), \
             patch('tink_substrate.__main__.make_server', side_effect=AssertionError('started server')), \
             patch('sys.stdout', new_callable=io.StringIO) as output:
            with self.assertRaises(SystemExit) as raised:
                main(['--version'])
        self.assertEqual(raised.exception.code, 0)
        self.assertEqual(output.getvalue(), f'tink-substrate {__version__}\n')

    def test_help_and_missing_subcommand(self):
        help_result = self.command([sys.executable, '-m', 'tink_substrate', '--help'])
        self.assertEqual(help_result.returncode, 0, help_result.stderr)
        self.assertIn('--version', help_result.stdout)
        result = self.command([sys.executable, '-m', 'tink_substrate'])
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, '')
        self.assertIn('the following arguments are required: command', result.stderr)

    def test_source_ignores_other_distribution_version(self):
        metadata = self.root / 'tink_substrate-99.0.0.dist-info'
        metadata.mkdir()
        (metadata / 'METADATA').write_text('Metadata-Version: 2.1\nName: tink-substrate\nVersion: 99.0.0\n')
        env = dict(self.env, PYTHONPATH=str(self.root))
        result = self.command([sys.executable, '-c',
                               'import importlib.metadata as m; print(m.version("tink-substrate"))'], env=env)
        self.assertEqual(result.stdout, '99.0.0\n', result.stderr)
        self.assert_version(self.command([sys.executable, '-m', 'tink_substrate', '--version'], env=env))

    def test_built_package_console_module_and_metadata_outside_source(self):
        # Copy only build inputs so setuptools cannot leave files in the checkout.
        source = self.root / 'source'
        source.mkdir()
        for name in ('pyproject.toml', 'LICENSE'):
            shutil.copy2(ROOT / name, source / name)
        shutil.copytree(ROOT / 'tink_substrate', source / 'tink_substrate',
                        ignore=shutil.ignore_patterns('__pycache__'))
        environment = self.root / 'venv'
        venv.EnvBuilder(with_pip=True).create(environment)
        python = environment / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')
        install = self.command([str(python), '-m', 'pip', 'install', '--disable-pip-version-check',
                                '--no-deps', str(source)], cwd=self.root)
        self.assertEqual(install.returncode, 0, install.stdout + install.stderr)
        shutil.rmtree(source)
        console = python.parent / ('tink-substrate.exe' if os.name == 'nt' else 'tink-substrate')
        for argv in ([str(console), '--version'], [str(python), '-m', 'tink_substrate', '--version']):
            self.assert_version(self.command(argv, cwd=self.root))
        metadata = self.command([str(python), '-c',
                                  'import importlib.metadata as m; print(m.version("tink-substrate"))'],
                                 cwd=self.root)
        self.assertEqual(metadata.returncode, 0, metadata.stderr)
        self.assertEqual(metadata.stdout, __version__ + '\n')
