"""Reproduce the skill-loading guidance bug bundled through the tink-sdlc pin.

Agents copy the commands that tink-sdlc prints. `tink mount NAME --payload`
exits 2 and asks for `--json`, so the printed hint fails. This test reads the
bundled SDLC.md and sdlc.py at a pinned revision and looks for that hint.

Scope: it checks the text that tink-sdlc ships. It does not prove the rule line
that the tink binary writes into AGENTS.md (`tink use`), and it does not prove
that an agent follows guidance.

Source of the tink-sdlc clone:
  1. TINK_SDLC_CACHE, a directory laid out like `--tool-cache` (CACHE/tink-sdlc).
  2. Otherwise a --no-checkout clone of the PINS url into a temp dir.
If neither works the tests skip, except when CI is set, where they fail.
"""
import os
import re
import subprocess
import tempfile
import unittest
from pathlib import Path

from scripts import install_skill

OLD_PIN = '328a2304b9af703dd846666757d6ffd1166df470'
FILES = ('assets/_system/SDLC.md', 'assets/_system/scripts/sdlc.py')
MOUNT = re.compile(r'tink mount[^\n]*')


def bad_mount_hints(text):
    """Return (line number, line) for `tink mount ... --payload` lines without --json."""
    found = []
    for number, line in enumerate(text.splitlines(), 1):
        for match in MOUNT.finditer(line):
            hint = match.group(0)
            if '--payload' in hint and '--json' not in hint:
                found.append((number, hint.strip()[:60]))
    return found


def read_at(repo, revision, path):
    return subprocess.check_output(['git', '-C', str(repo), 'show', f'{revision}:{path}'], text=True)


class ScannerTests(unittest.TestCase):
    def test_flags_payload_without_json(self):
        self.assertEqual(bad_mount_hints('run: tink mount unslop --payload.'),
                         [(1, 'tink mount unslop --payload.')])

    def test_accepts_json_payload_either_order(self):
        self.assertEqual(bad_mount_hints('tink mount a --json --payload\ntink mount b --payload --json'), [])

    def test_ignores_plain_mount(self):
        self.assertEqual(bad_mount_hints('run: tink mount NAME)'), [])


class BundledGuidanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix='skill-read-guidance-')
        cls.addClassCleanup(cls.temp.cleanup)
        url, cls.pin = install_skill.PINS['tink-sdlc']
        cache = os.environ.get('TINK_SDLC_CACHE')
        try:
            if cache:
                cls.repo = Path(cache) / 'tink-sdlc'
            else:
                cls.repo = Path(cls.temp.name) / 'tink-sdlc'
                subprocess.run(['git', 'clone', '--quiet', '--no-checkout', url, str(cls.repo)],
                               check=True, stderr=subprocess.PIPE, text=True)
            for revision in (cls.pin, OLD_PIN):
                subprocess.run(['git', '-C', str(cls.repo), 'cat-file', '-e', revision + '^{commit}'],
                               check=True, stderr=subprocess.PIPE)
        except (subprocess.CalledProcessError, OSError) as error:
            message = f'tink-sdlc clone unavailable (set TINK_SDLC_CACHE for offline use): {error}'
            if os.environ.get('CI'):
                raise AssertionError(message)
            raise unittest.SkipTest(message)

    def hints(self, revision):
        return [(path, number, hint) for path in FILES
                for number, hint in bad_mount_hints(read_at(self.repo, revision, path))]

    def test_old_pin_has_the_bug(self):
        found = self.hints(OLD_PIN)
        self.assertTrue(found, 'expected the old pin to print `tink mount ... --payload` without --json')
        self.assertEqual({path for path, _, _ in found}, set(FILES))

    def test_current_pin_tells_agents_to_use_json(self):
        found = self.hints(self.pin)
        self.assertEqual(found, [], f'tink-sdlc at {self.pin} prints `tink mount ... --payload` without '
                                    '--json; `tink mount` exits 2 on it: ' + repr(found))


if __name__ == '__main__':
    unittest.main()
