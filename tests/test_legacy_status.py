from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tink_substrate.sources import SourceError, workflow_state


class LegacyStatusTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        script = self.root / '_system/scripts/sdlc.py'
        script.parent.mkdir(parents=True)
        script.touch()
        self.record = {'run': 'example'}

    def test_explicit_unsupported_json_shows_text_without_inferred_approval(self):
        text = 'Stage 3: approved\nVerification: current\n<script>unsafe</script>\n'
        with patch('tink_substrate.sources.command', side_effect=[
                SourceError('sdlc.py: error: unrecognized arguments: --json\nCommands: status'), text]) as call:
            value = workflow_state(self.root, self.record, True)
        self.assertEqual(value['status_text'], text)
        self.assertEqual(value['verification_status'], 'unknown')
        self.assertEqual(value['gates'], [])
        self.assertIsNone(value['verification'])
        self.assertEqual(call.call_count, 2)
        self.assertEqual(call.call_args_list[1].args[0][-2:], ['status', 'example'])

    def test_other_errors_and_bad_json_never_fall_back(self):
        for result in (SourceError('permission denied'), SourceError('timeout'), '{bad json',
                       '{"protocol":"wrong","api_version":1}'):
            with self.subTest(result=result), patch('tink_substrate.sources.command') as call:
                if isinstance(result, Exception):
                    call.side_effect = result
                else:
                    call.return_value = result
                with self.assertRaises(ValueError):
                    workflow_state(self.root, self.record, True)
                self.assertEqual(call.call_count, 1)

    def test_empty_or_failed_text_stays_unavailable(self):
        for result in ('', SourceError('unknown run')):
            with patch('tink_substrate.sources.command', side_effect=[
                    SourceError('sdlc.py: error: unrecognized arguments: --json'), result]):
                with self.assertRaises(SourceError):
                    workflow_state(self.root, self.record, True)

    def test_untrusted_runtime_is_never_called(self):
        with patch('tink_substrate.sources.command') as call:
            with self.assertRaises(SourceError):
                workflow_state(self.root, self.record, False)
            call.assert_not_called()
