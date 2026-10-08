"""Ledger slice 2a: operator minutes and touches per change, from harness transcripts.

Ways this could fail, written before the code:
1. Machine prompts (tool results, task notifications, exec or subagent sessions) count as operator time.
2. A long pause (lunch) counts as work: credit must be capped at C.
3. Two sessions running at once count the same minute twice.
4. A session is linked to the wrong change, or an unlinked session is silently dropped instead of unattributed.
5. A change with no transcript is recorded as zero minutes instead of unknown.
6. Prompt text leaks into the ledger.
7. Re-running adds duplicate lines.
8. A transcript format change crashes the sweep instead of being skipped and counted.
"""
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import tempfile
import unittest

from tink_substrate import ledger, sessions

T0 = datetime(2026, 10, 7, 12, 0, tzinfo=timezone.utc)
SECRET = 'please fix the login bug quietly'


def at(minutes):
    return (T0 + timedelta(minutes=minutes)).isoformat().replace('+00:00', 'Z')


def write(path, entries):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(''.join(json.dumps(e) + '\n' for e in entries))


def claude_human(minute, text=SECRET, branch='tink/feature'):
    return {'type': 'user', 'timestamp': at(minute), 'gitBranch': branch, 'cwd': '/w', 'sessionId': 's',
            'origin': {'kind': 'human'}, 'promptSource': 'sdk', 'message': {'role': 'user', 'content': text}}


def claude_agent(minute):
    return {'type': 'assistant', 'timestamp': at(minute), 'message': {'role': 'assistant',
            'content': [{'type': 'text', 'text': 'done'}]}}


class SessionsTest(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.claude, self.codex, self.pi = self.root / 'claude', self.root / 'codex', self.root / 'pi'
        for directory in (self.claude, self.codex, self.pi):
            directory.mkdir()
        self.ledger = self.root / 'changes.jsonl'
        rows = [
            ('o/r#1', 'tink/feature', at(-60), at(300), None),
            ('o/r#2', 'other', at(-60), at(300), 'c261007abcd'),
            ('o/r#3', 'quiet', at(-60), at(300), None),
        ]
        with self.ledger.open('w') as out:
            for change, branch, created, merged, change_id in rows:
                out.write(json.dumps({'schema': 1, 'key': [change, 'backfill', 'gh', 0], 'change': change,
                                      'phase': 'backfill', 'at': merged, 'by': 't', 'fields': {
                                          'change_id': change_id, 'outcome': {'state': 'merged', 'reverted_by': None},
                                          'vcs': {'vcs.repository.name': 'o/r', 'vcs.ref.head.name': branch},
                                          'times': {'created': created, 'merged': merged, 'closed': merged,
                                                    'lead_hours': 6.0},
                                          'review': {'rounds': 0, 'p1': 0}}}) + '\n')

    def run_sweep(self):
        return sessions.sweep(self.ledger, claude=self.claude, codex=self.codex, pi=self.pi, snapshots=None)

    def rows(self):
        return ledger.fold(ledger.read(self.ledger))

    def test_claude_minutes_cap_gaps_and_ignore_machine_turns(self):
        write(self.claude / 'p' / 's.jsonl', [
            claude_human(0),  # first prompt: nothing visible before it, so no credit
            claude_agent(1),
            {'type': 'user', 'timestamp': at(2), 'message': {'role': 'user', 'content': [
                {'type': 'tool_result', 'content': 'x'}]}},
            claude_agent(3),
            claude_human(5),  # 2 minutes after the agent's last output
            claude_agent(6),
            {'type': 'user', 'timestamp': at(8), 'origin': {'kind': 'task-notification'}, 'promptSource': 'system',
             'message': {'role': 'user', 'content': 'task finished'}},
            claude_human(66),  # an hour later: capped
        ])
        write(self.claude / 'p' / 's' / 'subagents' / 'agent-1.jsonl', [claude_human(4), claude_human(30)])
        self.run_sweep()
        operator = self.rows()['o/r#1']['operator']
        self.assertEqual(operator['touches'], 3)
        self.assertEqual(operator['minutes'], {'c2': 4.0, 'c5': 7.0, 'c10': 12.0})
        self.assertEqual(operator['sessions'], [{'harness': 'claude', 'id': 's', 'link': 'branch'}])

    def test_parallel_sessions_split_overlapping_minutes(self):
        write(self.claude / 'p' / 'a.jsonl', [claude_human(0), claude_agent(1), claude_human(5)])
        write(self.claude / 'p' / 'b.jsonl', [claude_human(0, branch='other'), claude_agent(1),
                                               claude_human(5, branch='other')])
        self.run_sweep()
        rows = self.rows()
        # both sessions credit minutes 1-5; that 4-minute stretch is split, not counted twice
        self.assertEqual(rows['o/r#1']['operator']['minutes']['c5'], 2.0)
        self.assertEqual(rows['o/r#2']['operator']['minutes']['c5'], 2.0)

    def test_stamped_change_id_links_before_branch(self):
        write(self.claude / 'p' / 's.jsonl', [claude_human(0, 'change: c261007abcd\nbuild it', branch='main'),
                                               claude_agent(1), claude_human(4, branch='main')])
        self.run_sweep()
        self.assertEqual(self.rows()['o/r#2']['operator']['sessions'][0]['link'], 'stamped')

    def test_claude_pr_link_record_links_the_session(self):
        write(self.claude / 'p' / 's.jsonl', [claude_human(0, branch='main'), claude_agent(1),
                                               {'type': 'pr-link', 'prRepository': 'o/r', 'prNumber': 3,
                                                'timestamp': at(2)}, claude_human(4, branch='main')])
        self.run_sweep()
        self.assertEqual(self.rows()['o/r#3']['operator']['sessions'][0]['link'], 'pr-link')

    def test_report_shows_operator_hours_and_hides_small_cells(self):
        write(self.claude / 'p' / 's.jsonl', [claude_human(0), claude_agent(1), claude_human(4)])
        write(self.claude / 'p' / 'u.jsonl', [claude_human(0, branch='main'), claude_agent(1),
                                               claude_human(10, branch='main')])
        self.run_sweep()
        out = ledger.report(self.rows())
        self.assertIn('operator h', out)
        self.assertIn('unattributed', out)
        self.assertIn('with operator data 1/3', out)

    def test_codex_reads_user_messages_and_skips_exec_and_subagents(self):
        def codex(name, source, originator, branch):
            item = lambda kind, minute: {'timestamp': at(minute), 'type': 'event_msg', 'payload': {
                'type': 'item_completed', 'item': {'type': kind, 'content': [{'type': 'text', 'text': SECRET}]}}}
            write(self.codex / '2026' / '10' / '07' / f'rollout-{name}.jsonl', [
                {'timestamp': at(0), 'type': 'session_meta', 'payload': {
                    'id': name, 'cwd': '/w', 'originator': originator, 'source': source,
                    'git': {'branch': branch, 'repository_url': 'https://github.com/o/r.git'}}},
                item('UserMessage', 0), item('AgentMessage', 2), item('CommandExecution', 3), item('UserMessage', 6)])
        codex('live', 'vscode', 'Codex Desktop', 'tink/feature')
        codex('batch', 'exec', 'codex_exec', 'quiet')
        codex('child', {'subagent': {'thread_spawn': {'parent_thread_id': 'live'}}}, 'Codex Desktop', 'quiet')
        self.run_sweep()
        rows = self.rows()
        self.assertEqual(rows['o/r#1']['operator']['minutes']['c5'], 3.0)
        self.assertNotIn('operator', rows['o/r#3'])

    def test_pi_counts_conversations_not_single_prompt_launches(self):
        def pi(name, prompts, text):
            entries = [{'type': 'session', 'id': name, 'cwd': '/w', 'timestamp': at(0)}]
            for minute in prompts:
                entries += [{'type': 'message', 'timestamp': at(minute), 'message': {'role': 'user', 'content': [
                    {'type': 'text', 'text': text}]}},
                    {'type': 'message', 'timestamp': at(minute + 1), 'message': {'role': 'assistant', 'content': []}}]
            write(self.pi / '--w--' / f'{name}.jsonl', entries)
        pi('talk', [0, 4], 'see https://github.com/o/r/pull/3 please')
        pi('launch', [0], 'https://github.com/o/r/pull/3')
        self.run_sweep()
        operator = self.rows()['o/r#3']['operator']
        self.assertEqual(operator['touches'], 2)
        self.assertEqual(operator['minutes']['c5'], 3.0)
        self.assertEqual(operator['sessions'], [{'harness': 'pi', 'id': 'talk', 'link': 'text'}])

    def test_unlinked_time_is_unattributed_and_unknown_is_not_zero(self):
        write(self.claude / 'p' / 's.jsonl', [claude_human(0, branch='main'), claude_agent(1),
                                               claude_human(4, branch='main')])
        write(self.claude / 'p' / 'bad.jsonl', [{'type': 'user'}, 'not json'])
        summary = self.run_sweep()
        rows = self.rows()
        self.assertEqual(rows['~unattributed/2026-W41']['unattributed']['minutes']['c5'], 3.0)
        self.assertNotIn('operator', rows['o/r#1'])
        self.assertEqual(summary['skipped'], 1)

    def test_a_change_no_longer_linked_loses_its_operator_row(self):
        path = self.claude / 'p' / 's.jsonl'
        write(path, [claude_human(0), claude_agent(1), claude_human(4)])
        self.run_sweep()
        write(path, [claude_human(0, branch='main'), claude_agent(1), claude_human(4, branch='main')])
        self.run_sweep()
        self.assertIsNone(self.rows()['o/r#1']['operator'])

    def test_branch_shared_by_two_repositories_is_ambiguous(self):
        with self.ledger.open('a') as out:
            out.write(json.dumps({'schema': 1, 'key': ['p/q#9', 'backfill', 'gh', 9], 'change': 'p/q#9',
                                  'phase': 'backfill', 'at': at(300), 'by': 't', 'fields': {
                                      'change_id': None, 'outcome': {'state': 'merged', 'reverted_by': None},
                                      'vcs': {'vcs.repository.name': 'p/q', 'vcs.ref.head.name': 'tink/feature'},
                                      'times': {'created': at(-60), 'merged': at(300), 'closed': at(300)},
                                      'review': {'rounds': 0, 'p1': 0}}}) + '\n')
        write(self.claude / 'p' / 's.jsonl', [claude_human(0), claude_agent(1), claude_human(4)])
        self.run_sweep()
        rows = self.rows()
        self.assertNotIn('operator', rows['o/r#1'])
        self.assertEqual(rows['~unattributed/2026-W41']['unattributed']['minutes']['c5'], 3.0)

    def test_stamped_link_is_not_diluted_by_weaker_evidence(self):
        write(self.claude / 'p' / 's.jsonl', [claude_human(0, 'change: c261007abcd'), claude_agent(1),
                                               claude_human(4, 'see https://github.com/o/r/pull/3')])
        self.run_sweep()
        rows = self.rows()
        self.assertEqual(rows['o/r#2']['operator']['minutes']['c5'], 3.0)
        self.assertNotIn('operator', rows['o/r#1'])
        self.assertNotIn('operator', rows['o/r#3'])

    def test_branch_switch_mid_session_charges_each_branch(self):
        write(self.claude / 'p' / 's.jsonl', [claude_human(0), claude_agent(1), claude_human(4),
                                               {**claude_agent(5), 'gitBranch': 'other'},
                                               claude_human(8, branch='other')])
        self.run_sweep()
        rows = self.rows()
        self.assertEqual(rows['o/r#1']['operator']['minutes']['c5'], 3.0)
        self.assertEqual(rows['o/r#2']['operator']['minutes']['c5'], 3.0)

    def test_minutes_count_in_the_week_they_were_spent(self):
        earlier = lambda minute: (T0 - timedelta(days=7) + timedelta(minutes=minute)).isoformat()
        write(self.pi / '--w--' / 'old.jsonl', [
            {'type': 'session', 'id': 'old', 'cwd': '/w', 'timestamp': earlier(0)},
            {'type': 'message', 'timestamp': earlier(0), 'message': {'role': 'user', 'content': [
                {'type': 'text', 'text': 'https://github.com/o/r/pull/3'}]}},
            {'type': 'message', 'timestamp': earlier(1), 'message': {'role': 'assistant', 'content': []}},
            {'type': 'message', 'timestamp': earlier(4), 'message': {'role': 'user', 'content': []}}])
        self.run_sweep()
        operator = self.rows()['o/r#3']['operator']
        self.assertEqual(operator['minutes_by_week'], {'2026-W40': {'c2': 2.0, 'c5': 3.0, 'c10': 3.0}})
        self.assertIn('2026-W40', ledger.report(self.rows()))

    def test_no_prompt_text_and_rerun_is_idempotent(self):
        write(self.claude / 'p' / 's.jsonl', [claude_human(0), claude_agent(1), claude_human(4)])
        self.run_sweep()
        before = self.ledger.read_text()
        self.assertNotIn('login bug', before)
        self.run_sweep()
        self.assertEqual(self.ledger.read_text(), before)


if __name__ == '__main__':
    unittest.main()
