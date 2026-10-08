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
9. Streamed Claude messages repeat their usage on every line, so tokens are counted several times.
10. Worker sessions with no human (exec, launched, child agents) are left out of a change's cost.
11. Dollars are invented for a harness that does not report them.
12. A follow-up prompt the agent asked for is counted as the operator steering.
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


def claude_usage(minute, message, text='done', model='claude-x'):
    return {'type': 'assistant', 'timestamp': at(minute), 'version': '2.1.0', 'message': {
        'id': message, 'role': 'assistant', 'model': model, 'content': [{'type': 'text', 'text': text}],
        'usage': {'input_tokens': 10, 'cache_read_input_tokens': 90, 'cache_creation_input_tokens': 0,
                  'output_tokens': 5, 'output_tokens_details': {'thinking_tokens': 2}}}}


def codex_session(root, name, branch, source='vscode', originator='Codex Desktop', humans=(0, 6), model='gpt-x'):
    entries = [{'timestamp': at(0), 'type': 'session_meta', 'payload': {
        'id': name, 'cwd': '/w', 'originator': originator, 'source': source, 'cli_version': '0.9',
        'git': {'branch': branch, 'repository_url': 'https://github.com/o/r.git'}}},
        {'timestamp': at(0), 'type': 'turn_context', 'payload': {'model': model, 'effort': 'low'}}]
    for minute in humans:
        entries.append({'timestamp': at(minute), 'type': 'event_msg', 'payload': {
            'type': 'item_completed', 'item': {'type': 'UserMessage', 'content': [{'type': 'text', 'text': SECRET}]}}})
        entries.append({'timestamp': at(minute + 2), 'type': 'event_msg', 'payload': {
            'type': 'item_completed', 'item': {'type': 'AgentMessage', 'content': [{'type': 'text', 'text': 'ok'}]}}})
    entries.append({'timestamp': at(3), 'type': 'token_usage_record', 'payload': {'usage': {
        'input_tokens': 100, 'cached_input_tokens': 60, 'cache_write_input_tokens': 0, 'output_tokens': 7,
        'reasoning_output_tokens': 3}}})
    write(root / '2026' / '10' / '07' / f'rollout-{name}.jsonl', entries)


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
        self.assertEqual(operator['sessions'], [{'harness': 'claude', 'id': 's', 'link': 'branch', 'role': 'interactive'}])

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
        self.assertIn('View 2', out)
        self.assertIn('touches by kind:', out)

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
        self.assertEqual(operator['sessions'], [{'harness': 'pi', 'id': 'launch', 'link': 'text', 'role': 'launched'},
                                                {'harness': 'pi', 'id': 'talk', 'link': 'text', 'role': 'interactive'}])

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

    def test_cost_dedupes_streamed_usage_and_takes_dollars_only_from_the_harness(self):
        write(self.claude / 'p' / 's.jsonl', [
            claude_human(0), claude_usage(1, 'm1'), claude_usage(1, 'm1'), claude_usage(2, 'm2'), claude_human(4),
            {'type': 'cost-state', 'totalCostUSD': 1.0}, {'type': 'cost-state', 'totalCostUSD': 2.5}])
        codex_session(self.codex, 'worker', 'tink/feature', source='exec', originator='codex_exec', humans=(0,))
        self.run_sweep()
        row = self.rows()['o/r#1']
        cost = row['cost']
        self.assertEqual(cost['gen_ai.usage.input_tokens'], 300)  # 2 Claude messages x 100, plus Codex 100
        self.assertEqual(cost['gen_ai.usage.output_tokens'], 17)
        self.assertEqual(cost['gen_ai.usage.cache_read.input_tokens'], 240)
        self.assertEqual(cost['gen_ai.usage.reasoning.output_tokens'], 7)
        self.assertEqual(cost['llm.cost.total'], 2.5)  # Claude's own total; Codex reports no dollars
        self.assertLess(cost['cost_known_share'], 1)
        self.assertEqual(row['config']['models_seen'], {'interactive': ['claude-x'], 'launched': ['gpt-x@low']})
        self.assertTrue(row['config']['config_mixed'])
        self.assertEqual(row['config']['harnesses'], ['claude@2.1.0', 'codex@0.9'])

    def test_codex_child_agent_cost_follows_its_parent(self):
        codex_session(self.codex, 'parent', 'tink/feature')
        codex_session(self.codex, 'child', 'main', source={'subagent': {'thread_spawn': {'parent_thread_id': 'parent'}}},
                      humans=(1,), model='gpt-mini')
        self.run_sweep()
        cost = self.rows()['o/r#1']['cost']
        self.assertEqual(cost['gen_ai.usage.input_tokens'], 200)
        self.assertIsNone(cost['llm.cost.total'])

    def test_pi_cost_comes_from_its_own_per_message_dollars(self):
        entries = [{'type': 'session', 'id': 'pi1', 'cwd': '/w', 'timestamp': at(0), 'version': 3},
                   {'type': 'thinking_level_change', 'thinkingLevel': 'high', 'timestamp': at(0)}]
        for minute in (0, 4):
            entries += [{'type': 'message', 'timestamp': at(minute), 'message': {'role': 'user', 'content': [
                {'type': 'text', 'text': 'https://github.com/o/r/pull/3'}]}},
                {'type': 'message', 'timestamp': at(minute + 1), 'message': {
                    'role': 'assistant', 'model': 'gpt-y', 'content': [{'type': 'text', 'text': 'Ready?'}],
                    'usage': {'input': 10, 'output': 2, 'cacheRead': 30, 'cacheWrite': 0, 'reasoning': 1,
                              'cost': {'total': 0.25}}}}]
        write(self.pi / '--w--' / 'pi1.jsonl', entries)
        self.run_sweep()
        row = self.rows()['o/r#3']
        self.assertEqual(row['cost']['llm.cost.total'], 0.5)
        self.assertEqual(row['cost']['gen_ai.usage.input_tokens'], 80)
        self.assertEqual(row['config']['models_seen']['interactive'], ['gpt-y@high'])
        self.assertEqual(row['operator']['phases'], {'intake': 1, 'agent_asked': 1})

    def test_touch_phases(self):
        write(self.claude / 'p' / 's.jsonl', [
            claude_human(0), claude_usage(1, 'a', 'Which file should I change?'), claude_human(3),
            claude_usage(4, 'b'), claude_human(6), claude_usage(7, 'c'), claude_human(340)])  # merged at 300
        self.run_sweep()
        self.assertEqual(self.rows()['o/r#1']['operator']['phases'],
                         {'intake': 1, 'agent_asked': 1, 'steered': 1, 'post_merge': 1})
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
