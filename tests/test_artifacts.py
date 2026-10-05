from pathlib import Path
import tempfile
import unittest

from tink_substrate.sources import stage_artifacts


class ArtifactTests(unittest.TestCase):
    def test_groups_existing_outputs_and_keeps_future_stages_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run = root / 'runs/demo'
            run.mkdir(parents=True)
            (run / 'brief.md').write_text('# Actual brief\nKeep this content.')
            (run / 'checklist.json').write_text('{"items": []}')
            groups = stage_artifacts(root, {'run': 'demo'})
            self.assertEqual(groups[0]['documents'][0]['data']['text'], '# Actual brief\nKeep this content.')
            self.assertEqual(groups[1]['documents'], [])
            self.assertEqual(groups[2]['documents'][0]['label'], 'Checklist')
            self.assertEqual(groups[3]['documents'], [])
            (run / 'brief.md').write_text('Changed brief')
            self.assertEqual(stage_artifacts(root, {'run': 'demo'})[0]['documents'][0]['data']['text'], 'Changed brief')

    def test_light_review_keeps_brief_and_checklist_together(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run = root / 'runs/demo'
            run.mkdir(parents=True)
            (run / 'brief.md').write_text('Brief')
            (run / 'checklist.json').write_text('{"items": []}')
            light = stage_artifacts(root, {'run': 'demo'}, 'light')
            self.assertEqual([d['label'] for d in light[0]['documents']], ['Brief', 'Checklist'])
            self.assertEqual(light[2]['documents'], [])
            full = stage_artifacts(root, {'run': 'demo'}, 'full')
            self.assertEqual([d['label'] for d in full[2]['documents']], ['Checklist'])

    def test_unsafe_large_and_missing_linked_documents_are_visible_errors(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / 'repo'
            run = root / 'runs/demo'
            run.mkdir(parents=True)
            outside = Path(tmp) / 'private.md'
            outside.write_text('DO NOT EXPOSE')
            (run / 'brief.md').symlink_to(outside)
            (run / 'checklist.json').write_text('x' * 256001)
            groups = stage_artifacts(root, {'run': 'demo', 'seed': '../private.md', 'handoff': 'missing.md'})
            documents = [d for g in groups for d in g['documents']]
            self.assertEqual(len(documents), 4)
            self.assertTrue(all(d['status'] == 'unavailable' for d in documents))
            self.assertNotIn('DO NOT EXPOSE', str(documents))
