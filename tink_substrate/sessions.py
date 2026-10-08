"""Operator minutes, touches, cost and configuration per change, read after the fact from Claude Code, Codex and Pi
transcripts.

Each transcript reduces to one session: the times the operator typed a prompt, the times the agent did anything,
and evidence linking it to changes. A prompt is credited with the gap since the agent's last activity, capped at C
minutes. Credit from parallel sessions is merged on one timeline, so a minute is never counted twice. Rows hold
counts, IDs and times, never prompt text.

Cost counts every session that worked on a change, including launched workers and child agents, which inherit
their parent's links. Token names follow OpenTelemetry GenAI (input includes cached tokens); dollars are
`llm.cost.total` (OpenInference) and come only from what a harness itself reports, never from a price table.
"""

import bisect
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import re
import tarfile

from . import __version__
from .ledger import CHANGE_ID, read, fold, when

CAPS = (2, 5, 10)
HOME = Path.home()
DEFAULT_DIRS = {'claude': HOME / '.claude/projects', 'codex': HOME / '.codex/sessions', 'pi': HOME / '.pi/agent/sessions'}
DEFAULT_SNAPSHOTS = HOME / '.local/share/tink-substrate/ledger/transcripts'
GLOBS = {'claude': ('*/*.jsonl', '*/*/subagents/*.jsonl'), 'codex': ('*/*/*/*.jsonl',), 'pi': ('*/*.jsonl',)}
PR_URL = re.compile(r'github\.com/([\w.-]+/[\w.-]+)/pull/(\d+)')
STAMP = re.compile(r'(?:^|\n)(?:Tink-Change|change): (' + CHANGE_ID.pattern + r')\b')
TRUNK = {'main', 'master', 'HEAD', ''}
TOKENS = ('input', 'output', 'cache_read', 'cache_write', 'reasoning')
OTEL = {'input': 'gen_ai.usage.input_tokens', 'output': 'gen_ai.usage.output_tokens',
        'cache_read': 'gen_ai.usage.cache_read.input_tokens', 'cache_write': 'gen_ai.usage.cache_write.input_tokens',
        'reasoning': 'gen_ai.usage.reasoning.output_tokens'}


def session(harness, sid):
    return {'harness': harness, 'id': sid, 'humans': [], 'activity': [], 'branches': [], 'repo': None,
            'prs': set(), 'pr_links': set(), 'stamps': set(), 'launched': False, 'parent': None,
            'usage': [], 'dollars': None, 'version': None, 'asked': set()}


def usage(found, moment, model, effort, tokens, dollars=None):
    """One model response: tokens normalized to TOKENS, dollars only if the harness reported them."""
    found['usage'].append((moment, tokens, dollars, f'{model}@{effort}' if effort and model else model))


def asks(text):
    return text.rstrip().endswith('?')


def instant(value):
    """An event time; a supported event without one makes the transcript unreadable, so it is skipped."""
    if not value:
        raise ValueError('event without a timestamp')
    return when(value)


def evidence(found, text):
    found['stamps'].update(STAMP.findall(text))
    found['prs'].update(f'{repo}#{number}' for repo, number in PR_URL.findall(text))


def text_of(content):
    if isinstance(content, str):
        return content
    return '\n'.join(block.get('text', '') for block in content if isinstance(block, dict))


def read_claude(entries, sid):
    found = session('claude', sid)
    messages, questions = {}, set()
    for entry in entries:
        kind, stamp = entry['type'], entry.get('timestamp')
        if kind == 'pr-link':
            found['pr_links'].add(f"{entry['prRepository']}#{entry['prNumber']}")
        if entry.get('gitBranch') and stamp:  # a session can switch branches; keep each switch
            found['branches'].append((when(stamp), entry['gitBranch']))
        if entry.get('entrypoint') == 'sdk-cli':  # `claude -p` or the Agent SDK: nobody at the keyboard
            found['launched'] = True
        if kind == 'cost-state':  # Claude flags totals it could not price; those stay unknown
            found['dollars'] = None if entry.get('hasUnknownModelCost') else entry.get('totalCostUSD')
        if kind == 'assistant':
            message, moment = entry['message'], instant(stamp)
            found['activity'].append(moment)
            found['version'] = entry.get('version') or found['version']
            text = text_of(message['content'])
            evidence(found, text)
            for block in message['content']:
                if isinstance(block, dict) and block.get('name') == 'AskUserQuestion':
                    questions.add(block.get('id'))
                    found['asked'].add(moment)
            if asks(text):
                found['asked'].add(moment)
            spent = message.get('usage')
            if spent:
                # Streamed lines repeat one message's usage, and early copies can hold partial counts: keep the largest.
                cache_read, cache_write = spent.get('cache_read_input_tokens', 0), spent.get('cache_creation_input_tokens', 0)
                tokens = {'input': spent.get('input_tokens', 0) + cache_read + cache_write,
                          'output': spent.get('output_tokens', 0), 'cache_read': cache_read, 'cache_write': cache_write,
                          'reasoning': (spent.get('output_tokens_details') or {}).get('thinking_tokens', 0)}
                key = message.get('id') or id(entry)
                if key not in messages or tokens['output'] > messages[key][1]['output']:
                    messages[key] = (moment, tokens, message.get('model'))
        elif kind == 'user':
            content = entry['message']['content']
            origin = entry.get('origin')
            results = [b for b in content if isinstance(b, dict) and b.get('type') == 'tool_result'] \
                if isinstance(content, list) else []
            if any(b.get('tool_use_id') in questions for b in results):  # the operator answering the agent's question
                found['humans'].append(instant(stamp))
            elif (not entry.get('isMeta') and not results and (origin.get('kind') == 'human' if isinstance(origin, dict)
                                                              else entry.get('promptSource') != 'system')):
                found['humans'].append(instant(stamp))
                evidence(found, text_of(content))
    for moment, tokens, model in messages.values():
        usage(found, moment, model, None, tokens)
    return found


def codex_tokens(spent):
    return {'input': spent.get('input_tokens', 0), 'output': spent.get('output_tokens', 0),
            'cache_read': spent.get('cached_input_tokens', 0), 'cache_write': spent.get('cache_write_input_tokens', 0),
            'reasoning': spent.get('reasoning_output_tokens', 0)}


def read_codex(entries, sid):
    found = session('codex', sid)
    model = effort = None
    counted, previous = [], dict.fromkeys(TOKENS, 0)
    for entry in entries:
        payload = entry.get('payload') or {}
        if entry['type'] == 'event_msg' and payload.get('type') == 'token_count' and payload.get('info'):
            # Codex CLI rollouts carry only a running total; each event's share is the growth since the last one.
            total = codex_tokens(payload['info'].get('total_token_usage') or {})
            if total != previous:
                counted.append((instant(entry['timestamp']), model, effort,
                                {name: max(total[name] - previous[name], 0) for name in TOKENS}))
                previous = total
        if entry['type'] == 'event_msg' and payload.get('type') == 'request_user_input':
            found['activity'].append(instant(entry['timestamp']))
            found['asked'].add(instant(entry['timestamp']))
        if entry['type'] == 'turn_context':
            model, effort = payload.get('model'), payload.get('effort')
        elif entry['type'] == 'token_usage_record':
            usage(found, instant(entry['timestamp']), model, effort, codex_tokens(payload['usage']))
        elif entry['type'] == 'session_meta':
            found['id'] = payload.get('id', sid)
            found['version'] = payload.get('cli_version')
            source = payload.get('source')
            found['launched'] = payload.get('originator') == 'codex_exec' or isinstance(source, dict)
            if isinstance(source, dict):
                found['parent'] = ((source.get('subagent') or {}).get('thread_spawn') or {}).get('parent_thread_id')
            git = payload.get('git') or {}
            if git.get('branch'):
                found['branches'].append((instant(entry['timestamp']), git['branch']))
            match = re.search(r'github\.com[/:]([\w.-]+/[\w.-]+?)(?:\.git)?$', git.get('repository_url') or '')
            found['repo'] = match.group(1) if match else None
        elif entry['type'] == 'event_msg' and payload.get('type') == 'item_completed':
            item = payload['item']
            if item['type'] == 'UserMessage':
                found['humans'].append(instant(entry['timestamp']))
                evidence(found, text_of(item.get('content') or []))
            else:
                found['activity'].append(instant(entry['timestamp']))
                if item['type'] == 'AgentMessage':
                    text = text_of(item.get('content') or [])
                    evidence(found, text)
                    if asks(text):
                        found['asked'].add(when(entry['timestamp']))
    if not found['usage']:  # no per-response records: fall back to the running totals
        for moment, used_model, used_effort, tokens in counted:
            usage(found, moment, used_model, used_effort, tokens)
    return found


def read_pi(entries, sid, copied=None):
    """copied: entry IDs already read; a forked Pi session repeats its source's history under the same IDs."""
    found = session('pi', sid)
    effort = None
    copied = set() if copied is None else copied
    for entry in entries:
        if entry.get('id') and entry['type'] != 'session':
            if entry['id'] in copied:
                continue
            copied.add(entry['id'])
        if entry['type'] == 'session':
            found['id'] = entry.get('id', sid)
            # the header's version is the session file format, not the Pi release, so the release stays unknown
        if entry['type'] == 'thinking_level_change':
            effort = entry.get('thinkingLevel')
        if entry['type'] != 'message':
            continue
        role = entry['message']['role']
        if role == 'user':
            found['humans'].append(instant(entry['timestamp']))
            evidence(found, text_of(entry['message']['content']))
        elif role in ('assistant', 'toolResult'):
            moment = instant(entry['timestamp'])
            found['activity'].append(moment)
            if role == 'assistant':
                message = entry['message']
                text = text_of(message['content'])
                evidence(found, text)
                if asks(text):
                    found['asked'].add(moment)
                spent = message.get('usage')
                if spent:
                    cache_read, cache_write = spent.get('cacheRead', 0), spent.get('cacheWrite', 0)
                    usage(found, moment, message.get('model'), effort, {
                        'input': spent.get('input', 0) + cache_read + cache_write, 'output': spent.get('output', 0),
                        'cache_read': cache_read, 'cache_write': cache_write, 'reasoning': spent.get('reasoning', 0)},
                        (spent.get('cost') or {}).get('total'))
    # Pi records no launch mode; a single-prompt session is a machine launch (`pi -p`, crew workers).
    found['launched'] = len(found['humans']) <= 1
    return found


def read_pi_child(entries, sid):
    """A Pi delegate's record (`<run>_<agent>_transcript.jsonl`): one line per event, usage on assistant lines."""
    found = session('pi', sid)
    found['launched'] = True
    for entry in entries:
        if entry.get('recordType') != 'message' or entry.get('role') != 'assistant':
            continue
        moment = instant(entry.get('timestamp'))
        found['activity'].append(moment)
        evidence(found, entry.get('text') or '')
        spent = entry.get('usage')
        if spent:
            cache_read, cache_write = spent.get('cacheRead', 0), spent.get('cacheWrite', 0)
            cost = spent.get('cost')
            usage(found, moment, entry.get('model'), None, {
                'input': spent.get('input', 0) + cache_read + cache_write, 'output': spent.get('output', 0),
                'cache_read': cache_read, 'cache_write': cache_write, 'reasoning': spent.get('reasoning', 0)},
                cost.get('total') if isinstance(cost, dict) else cost)
    return found


READERS = {'claude': read_claude, 'codex': read_codex, 'pi': read_pi}


def transcript(name):
    """False for macOS resource forks. Child agents (Claude subagents, Pi `*_transcript` delegates) are kept: they
    cost money for their parent's change, though they never count as operator touches."""
    return name.suffix == '.jsonl' and not name.name.startswith('._')


def child_name(path):
    """A Claude subagent file is named `<parent session>/subagents/<agent>`, which keeps its parent findable."""
    return f'{path.parent.parent.name}/subagents/{path.stem}' if path.parent.name == 'subagents' else path.stem


def transcripts(dirs, snapshots):
    """(harness, name, lines) for each transcript. Live folders first; snapshots fill in what has been deleted."""
    seen = set()
    for harness, directory in dirs.items():
        paths = sorted(p for pattern in GLOBS[harness] for p in Path(directory).glob(pattern)) if directory else ()
        for path in paths:
            if not transcript(path):
                continue
            seen.add((harness, path.name))
            yield harness, child_name(path), path.read_text(errors='replace').splitlines()
    for archive in sorted(Path(snapshots).glob('*.tgz'), reverse=True) if snapshots else ():  # newest copy wins
        harness = {'claude-projects': 'claude', 'codex-sessions': 'codex', 'pi-sessions': 'pi'}.get(
            archive.name.rsplit('-', 2)[0])
        if not harness:
            continue
        with tarfile.open(archive) as bundle:
            for member in bundle:
                name = Path(member.name)
                if not member.isfile() or not transcript(name) or (harness, name.name) in seen:
                    continue
                seen.add((harness, name.name))
                yield harness, child_name(name), bundle.extractfile(member).read().decode(errors='replace').splitlines()


def link(found, rows, by_id):
    """Changes this session worked on, from the strongest tier of evidence that finds any: stamped change ID,
    Claude pr-link, branch within the change's time, then a PR URL in the conversation. Weaker tiers are fallbacks,
    never added on top."""
    stamped = {by_id[stamp] for stamp in found['stamps'] if stamp in by_id}
    if stamped:
        return dict.fromkeys(stamped, 'stamped')
    linked = {change for change in found['pr_links'] if change in rows}
    if linked:
        return dict.fromkeys(linked, 'pr-link')
    branched = set()
    for branch in {name for _, name in found['branches']} - TRUNK:
        matches = [change for change, row in rows.items()
                   if (row.get('vcs') or {}).get('vcs.ref.head.name') == branch
                   and (not found['repo'] or row['vcs'].get('vcs.repository.name') == found['repo'])]
        if len({rows[change]['vcs'].get('vcs.repository.name') for change in matches}) > 1:
            continue  # the same branch name in several repositories: ambiguous without the session's repository
        times = [t for t in found['humans'] + found['activity'] + [u[0] for u in found['usage']]
                 if branch_at(found, t) == branch]
        if not times:
            continue
        first, last = min(times).timestamp(), max(times).timestamp()
        branched.update(change for change in matches if window(rows[change])[0] <= last
                        and first <= window(rows[change])[1])
    if branched:
        return dict.fromkeys(branched, 'branch')
    return dict.fromkeys((change for change in found['prs'] if change in rows), 'text')


def branch_at(found, moment):
    """The branch the session was on at a moment: the latest switch at or before it, else the first one seen."""
    current = found['branches'][0][1] if found['branches'] else None
    for switched, name in sorted(found['branches']):
        if switched > moment:
            break
        current = name
    return current


def window(row):
    times = row.get('times') or {}
    opened, closed = when(times.get('created')), when(times.get('closed'))
    return (opened.timestamp() - 12 * 3600 if opened else float('-inf'),
            closed.timestamp() + 3600 if closed else float('inf'))


def credits(found, cap):
    """(start, end) intervals in seconds, one per prompt: the gap since the agent's last activity, at most cap."""
    activity = sorted(t.timestamp() for t in found['activity'])
    out = []
    for human in sorted(t.timestamp() for t in found['humans']):
        index = bisect.bisect_right(activity, human)
        if index:  # the session's first prompt has nothing visible before it, so it earns no credit
            start = max(activity[index - 1], human - cap * 60, out[-1][1] if out else float('-inf'))
            if start < human:  # prompts sent back to back share one stretch of the session's time, never two
                out.append((start, human))
    return out


def merge_timeline(intervals):
    """intervals: (start, end, {label: weight}). Each instant is split evenly between the intervals covering it.
    Seconds per (label, ISO week the time was spent in)."""
    points = {p for start, end, _ in intervals for p in (start, end)}
    for start, end, _ in intervals:  # cut at each Monday 00:00 UTC so time lands in the week it was spent
        monday = datetime.fromtimestamp(start, timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        monday = (monday + timedelta(days=7 - monday.weekday())).timestamp()
        if monday < end:
            points.add(monday)
    points = sorted(points)
    totals = {}
    for left, right in zip(points, points[1:]):
        covering = [labels for start, end, labels in intervals if start <= left and end >= right]
        for labels in covering:
            for label, weight in labels.items():
                key = (label, week(left))
                totals[key] = totals.get(key, 0) + (right - left) * weight / len(covering)
    return totals


def unattributed(instant):
    return {f'~unattributed/{week(instant)}': 1.0}


def phase(found, human, first):
    """Who started this touch: the session's opening prompt, a reply to an agent's question, or operator steering."""
    if human == first:
        return 'intake'
    before = [t for t in found['activity'] if t <= human]
    return 'agent_asked' if before and max(before) in found['asked'] else 'steered'


def costs(everyone, rows):
    """Tokens and reported dollars per label. A Claude session reports one dollar total; it is spread over its
    responses by token weight. Codex reports no dollars, so its share stays unknown."""
    totals = {}
    for found in everyone:
        weights = [tokens['input'] + tokens['output'] for _, tokens, _, _ in found['usage']]
        for (moment, tokens, dollars, _), weight in zip(found['usage'], weights):
            if found['harness'] == 'claude' and found['dollars'] is not None:
                dollars = found['dollars'] * weight / (sum(weights) or 1)
            for label, share in (assign(moment.timestamp(), found, rows) or unattributed(moment.timestamp())).items():
                total = totals.setdefault(label, {'tokens': dict.fromkeys(TOKENS, 0), 'dollars': 0.0, 'known': 0, 'all': 0})
                for name in TOKENS:
                    total['tokens'][name] += tokens[name] * share
                total['all'] += weight * share
                if dollars is not None:
                    total['dollars'] += dollars * share
                    total['known'] += weight * share
    return {label: {**{OTEL[name]: round(value) for name, value in total['tokens'].items()},
                    'llm.cost.total': round(total['dollars'], 4) if total['known'] else None,
                    'cost_known_share': round(total['known'] / total['all'], 3) if total['all'] else None}
            for label, total in totals.items()}


def configs(everyone, rows):
    """Harness versions and models per change, split by sessions the operator talked to and launched workers.
    A model counts for a change only where one of its responses was assigned to that change."""
    seen = {}
    for found in everyone:
        role = 'launched' if found['launched'] else 'interactive'
        for change in found['links']:
            seen.setdefault(change, {'harnesses': set(), 'interactive': set(), 'launched': set()})['harnesses'].add(
                f"{found['harness']}@{found['version']}")
        for moment, _, _, model in found['usage']:
            for change in assign(moment.timestamp(), found, rows) or {}:
                if model:
                    seen[change][role].add(model)
    return {change: {'harnesses': sorted(config['harnesses']),
                     'models_seen': {'interactive': sorted(config['interactive']), 'launched': sorted(config['launched'])},
                     'config_mixed': len({m.split('@')[0] for m in config['interactive'] | config['launched']}) > 1}
            for change, config in seen.items()}


def sweep(ledger_path, claude=DEFAULT_DIRS['claude'], codex=DEFAULT_DIRS['codex'], pi=DEFAULT_DIRS['pi'],
          snapshots=DEFAULT_SNAPSHOTS):
    ledger_path = Path(ledger_path)
    existing = read(ledger_path)
    rows = {change: row for change, row in fold(existing).items() if 'outcome' in row}
    stamps = [row['change_id'] for row in rows.values() if row.get('change_id')]
    by_id = {row['change_id']: change for change, row in rows.items()  # an ID two changes share links neither
             if row.get('change_id') and stamps.count(row['change_id']) == 1}
    everyone, skipped, copied = [], 0, set()
    for harness, name, lines in transcripts({'claude': claude, 'codex': codex, 'pi': pi}, snapshots):
        try:
            lines = [line for line in lines if line.strip()]
            entries = [json.loads(line) for line in lines[:-1]]
            try:
                entries.append(json.loads(lines[-1])) if lines else None
            except ValueError:
                pass  # a live transcript can end in a line still being written
            if harness == 'pi' and name.endswith('_transcript'):
                found = read_pi_child(entries, name)
            elif harness == 'pi':
                found = read_pi(entries, name, copied)
            else:
                found = READERS[harness](entries, name)
            if '/subagents/' in name:  # a Claude subagent: launched by its parent session
                found['launched'], found['parent'] = True, name.split('/')[0]
        except (ValueError, KeyError, TypeError, AttributeError):
            skipped += 1
            continue
        if found['humans'] or found['usage']:
            found['links'] = link(found, rows, by_id)
            everyone.append(found)
    by_session = {(found['harness'], found['id']): found for found in everyone}
    changed = True
    while changed:  # child agents work for their parent's changes, however deep the nesting
        changed = False
        for found in everyone:
            parent = by_session.get((found['harness'], found['parent']))
            if parent and parent['links'] and not found['links']:
                found['links'] = {change: 'parent' for change in parent['links']}
                changed = True
    talked = [found for found in everyone if not found['launched'] and found['humans']]

    minutes = {cap: {} for cap in CAPS}
    by_week = {}  # operator time is reported in the week it was spent, not the week the change merged
    for cap in CAPS:
        intervals = [(start, end, assign(end, found, rows) or unattributed(end))
                     for found in talked for start, end in credits(found, cap)]
        for (label, spent), seconds in merge_timeline(intervals).items():
            minutes[cap][label] = minutes[cap].get(label, 0) + seconds
            weekly = by_week.setdefault(label, {}).setdefault(spent, {})
            weekly[f'c{cap}'] = round(weekly.get(f'c{cap}', 0) + seconds / 60, 2)
    touches, phases, members = {}, {}, {}
    for found in talked:
        first = min(found['humans'])
        for human in found['humans']:
            kind = phase(found, human, first)
            for label, weight in (assign(human.timestamp(), found, rows) or unattributed(human.timestamp())).items():
                merged = when((rows.get(label, {}).get('times') or {}).get('merged'))
                touch = 'post_merge' if merged and human > merged else kind
                touches[label] = touches.get(label, 0) + weight
                counts = phases.setdefault(label, {})
                counts[touch] = counts.get(touch, 0) + weight
    for found in everyone:
        for change, how in found['links'].items():
            members.setdefault(change, []).append({'harness': found['harness'], 'id': found['id'], 'link': how,
                                                   'role': 'launched' if found['launched'] else 'interactive'})
    spent, setups = costs(everyone, rows), configs(everyone, rows)

    operator = {}
    for label in set(touches) | set(minutes[CAPS[0]]):
        numbers = {'minutes': {f'c{cap}': round(minutes[cap].get(label, 0) / 60, 2) for cap in CAPS},
                   'minutes_by_week': by_week.get(label, {}), 'touches': round(touches.get(label, 0), 2)}
        operator[label] = {'unattributed': numbers} if label.startswith('~') else {'operator': {
            **numbers, 'phases': {name: round(value, 2) for name, value in phases.get(label, {}).items()},
            'method': 'gap-cap',
            'sessions': sorted(members.get(label, []), key=lambda s: (s['harness'], s['id']))}}
    money = {label: {'unattributed_cost': spent[label]} if label.startswith('~')
             else {'cost': spent.get(label), 'config': setups.get(label)}
             for label in set(spent) | set(setups)}
    added = write_rows(ledger_path, existing, 'operator', operator) + write_rows(ledger_path, existing, 'cost', money)
    return {'sessions': len(talked), 'workers': len(everyone) - len(talked),
            'linked': sum(bool(f['links']) for f in everyone), 'skipped': skipped, 'added': added}


def write_rows(ledger_path, existing, kind, produced):
    """Append one line per label unless identical to its latest; retract labels this sweep no longer produces."""
    latest = {json.dumps(line['key']): line['fields'] for line in existing}
    earlier = {line['change']: line['fields'] for line in existing if line['key'][1:3] == [kind, 'transcripts']}
    added = 0
    with ledger_path.open('a') as out:
        for label in sorted(set(produced) | set(earlier)):
            fields = produced.get(label) or dict.fromkeys(earlier[label], None)
            line = {'schema': 1, 'key': [label, kind, 'transcripts', 0], 'change': label, 'phase': kind,
                    'at': datetime.now(timezone.utc).isoformat(), 'by': f'sessions@{__version__}', 'fields': fields}
            if latest.get(json.dumps(line['key'])) == fields:
                continue
            out.write(json.dumps(line, sort_keys=True) + '\n')
            added += 1
    return added


def assign(moment, found, rows):
    """Weights per change for one moment of a session. Branch links take the change on the branch the session was on,
    within that change's time; other links take the one change, or those whose window holds the moment."""
    links = found['links']
    if not links:
        return None
    if set(links.values()) == {'branch'}:
        branch = branch_at(found, datetime.fromtimestamp(moment, timezone.utc))
        inside = [change for change in links if rows[change]['vcs'].get('vcs.ref.head.name') == branch
                  and window(rows[change])[0] <= moment <= window(rows[change])[1]]
        return {change: 1 / len(inside) for change in inside} or None
    if len(links) == 1:
        return {next(iter(links)): 1.0}
    inside = [change for change in links if window(rows[change])[0] <= moment <= window(rows[change])[1]]
    if not inside:
        inside = [min(links, key=lambda c: min(abs(moment - edge) for edge in window(rows[c])))]
    return {change: 1 / len(inside) for change in inside}


def week(instant):
    year, number, _ = datetime.fromtimestamp(instant, timezone.utc).isocalendar()
    return f'{year}-W{number:02d}'
