"""Check the skill-loading hints in this repository's own SDLC workspace.

test_skill_read_guidance.py checks the tink-sdlc text bundled through the pin.
This test checks the copy installed in this checkout (_system/, stages/ and the
AGENTS.md rule lines), which agents working here actually read.
`tink mount NAME --payload` exits 2 without --json.

Scope: text in files only. It does not prove an agent follows the hint.
"""
import unittest
from pathlib import Path

from tests.test_skill_read_guidance import bad_mount_hints

ROOT = Path(__file__).resolve().parents[1]


def workspace_files():
    return [ROOT / '_system/SDLC.md', ROOT / '_system/scripts/sdlc.py', ROOT / 'AGENTS.md',
            *sorted(ROOT.glob('stages/*/CONTEXT.md'))]


class WorkspaceGuidanceTests(unittest.TestCase):
    def test_workspace_files_present(self):
        files = workspace_files()
        self.assertEqual([p for p in files if not p.is_file()], [])
        self.assertGreaterEqual(len(files), 4)

    def test_mount_hints_use_json(self):
        found = [(str(p.relative_to(ROOT)), number, hint) for p in workspace_files() if p.is_file()
                 for number, hint in bad_mount_hints(p.read_text())]
        self.assertEqual(found, [], 'workspace prints `tink mount ... --payload` without --json; '
                                    'tink exits 2 on it: ' + repr(found))


if __name__ == '__main__':
    unittest.main()
