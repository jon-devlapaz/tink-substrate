"""Ledger update: one command that keeps the ledger current without anyone remembering.

Ways this could fail, written before the code:
1. A repository is silently skipped because the list lives in someone's shell history, not a config.
2. A transcript the harness deletes is lost because nothing kept a copy.
3. The copy is world-readable (transcripts can contain secrets).
4. Every run re-fetches every PR, so the daily job gets slower forever.
5. A failure in one step hides the result of the others, or exits 0.
6. The schedule points at a Python or package path that moves.
"""
from datetime import datetime, timezone
import gzip
import json
from pathlib import Path
import plistlib
import stat
import tempfile
import unittest
from unittest.mock import patch

from tink_substrate import ledger_auto


class LedgerAutoTest(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.home = self.root / 'ledger'
        self.config = self.root / 'ledger.json'
        self.live = {'claude': self.root / 'claude', 'codex': self.root / 'codex', 'pi': self.root / 'pi'}
        (self.live['claude'] / 'p').mkdir(parents=True)
        (self.live['claude'] / 'p' / 's.jsonl').write_text('{"type": "user"}\n')
        for name in ('codex', 'pi'):
            self.live[name].mkdir()

    def write_config(self, repos):
        self.config.write_text(json.dumps({'repos': repos}))

    def test_mirror_keeps_private_compressed_copies_and_updates_only_changed_files(self):
        copied = ledger_auto.mirror(self.live, self.home / 'mirror')
        target = self.home / 'mirror' / 'claude' / 'p' / 's.jsonl.gz'
        self.assertEqual(copied, 1)
        self.assertEqual(gzip.decompress(target.read_bytes()).decode(), '{"type": "user"}\n')
        self.assertEqual(stat.S_IMODE(target.stat().st_mode), 0o600)
        self.assertEqual(stat.S_IMODE((self.home / 'mirror').stat().st_mode), 0o700)
        self.assertEqual(ledger_auto.mirror(self.live, self.home / 'mirror'), 0)
        (self.live['claude'] / 'p' / 's.jsonl').write_text('{"type": "user"}\n{"type": "assistant"}\n')
        self.assertEqual(ledger_auto.mirror(self.live, self.home / 'mirror'), 1)

    def test_a_deleted_transcript_is_still_read_from_the_mirror(self):
        ledger_auto.mirror(self.live, self.home / 'mirror')
        (self.live['claude'] / 'p' / 's.jsonl').unlink()
        found = list(ledger_auto.sessions.transcripts(self.live, None, self.home / 'mirror'))
        self.assertEqual(found, [('claude', 's', ['{"type": "user"}'])])

    def test_update_reads_repos_from_config_and_sweeps_incrementally(self):
        self.write_config({'o/r': str(self.root)})
        calls = []
        with patch.object(ledger_auto.ledger, 'sweep', lambda path, repos, since=None: calls.append((repos, since)) or 2), \
             patch.object(ledger_auto.sessions, 'sweep', lambda path, **kw: {'sessions': 1, 'added': 3}):
            first = ledger_auto.update(self.config, self.home, live=self.live)
            second = ledger_auto.update(self.config, self.home, live=self.live)
        self.assertEqual(calls[0], ([('o/r', self.root)], {}))
        self.assertIsInstance(calls[1][1]['o/r'], datetime)  # second run only asks for what changed
        self.assertEqual(first['github'], {'added': 2})
        self.assertEqual(second['mirrored'], 0)

    def test_missing_config_is_an_error_that_says_what_to_write(self):
        with self.assertRaisesRegex(ValueError, 'ledger.json'):
            ledger_auto.update(self.config, self.home, live=self.live)

    def test_a_failing_step_is_reported_and_the_others_still_run(self):
        self.write_config({'o/r': str(self.root)})
        def broken(*args, **kwargs):
            raise ValueError('gh: not logged in')
        with patch.object(ledger_auto.ledger, 'sweep', broken), \
             patch.object(ledger_auto.sessions, 'sweep', lambda path, **kw: {'sessions': 1, 'added': 0}):
            result = ledger_auto.update(self.config, self.home, live=self.live)
        self.assertEqual(result['github'], {'error': 'gh: not logged in'})
        self.assertEqual(result['sessions'], {'sessions': 1, 'added': 0})
        self.assertFalse(result['ok'])
        state = json.loads((self.home / 'state.json').read_text())
        self.assertNotIn('o/r', state.get('swept', {}))  # a failed sweep must not move the cursor

    def test_schedule_writes_a_daily_launch_agent_for_the_installed_package(self):
        agents = self.root / 'LaunchAgents'
        package = self.root / 'skills' / 'tink-substrate'
        (package / 'tink_substrate').mkdir(parents=True)
        commands = []
        path = ledger_auto.schedule(agents, package, python='/usr/bin/python3', hour=6,
                                    run=lambda argv: commands.append(argv))
        plist = plistlib.loads(path.read_bytes())
        self.assertEqual(plist['ProgramArguments'], ['/usr/bin/python3', '-B', '-m', 'tink_substrate', 'ledger', 'update'])
        self.assertEqual(plist['WorkingDirectory'], str(package))
        self.assertEqual(plist['StartCalendarInterval'], {'Hour': 6, 'Minute': 0})
        self.assertIn('/opt/homebrew/bin', plist['EnvironmentVariables']['PATH'])
        self.assertEqual(commands[-1][:2], ['launchctl', 'bootstrap'])

    def test_schedule_refuses_a_directory_without_the_package(self):
        with self.assertRaisesRegex(ValueError, 'tink_substrate'):
            ledger_auto.schedule(self.root / 'LaunchAgents', self.root, python='/usr/bin/python3', run=lambda a: None)


if __name__ == '__main__':
    unittest.main()
