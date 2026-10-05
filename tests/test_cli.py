from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tink_substrate.__main__ import main


class SelectionTests(unittest.TestCase):
    def test_saved_selection_explains_restart_and_preserves_config_path(self):
        with tempfile.TemporaryDirectory(prefix='substrate selection ') as directory:
            root = Path(directory).resolve()
            config = root / 'selection.json'
            record = root / 'work.md'
            record.write_text('+++\nschema = 1\ntitle = "Patch"\nproject = "example"\nowner = "Example owner"\n'
                              'next_action = "Review"\n+++\n')
            for extra in ([], ['--replace']):
                out = io.StringIO()
                with patch('tink_substrate.__main__.git', return_value=str(root)), redirect_stdout(out):
                    result = main(['--config', str(config), 'init', '--work', str(record),
                                   '--checkout', str(root), *extra])
                self.assertEqual(result, 0)
                self.assertIn('restart', out.getvalue().lower())
                self.assertIn('refresh', out.getvalue().lower())
                self.assertIn(str(config), out.getvalue())
                self.assertFalse(json.loads(config.read_text())['trust_sdlc'])
