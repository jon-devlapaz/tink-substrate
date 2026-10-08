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
from datetime import datetime, timezone
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
GLOBS = {'claude': '*/*.jsonl', 'codex': '*/*/*/*.jsonl', 'pi': '*/*.jsonl'}  # Claude subagents sit one level deeper
PR_URL = re.compile(r'github\.com/([\w.-]+/[\w.-]+)/pull/(\d+)')
STAMP = re.compile(r'(?:^|\n)(?:Tink-Change|change): (' + CHANGE_ID.pattern + r')\b')
TRUNK = {'main', 'master', 'HEAD', ''}
TOKENS = ('input', 'output', 'cache_read', 'cache_write', 'reasoning')
OTEL = {'input': 'gen_ai.usage.input_tokens', 'output': 'gen_ai.usage.output_tokens',
        'cache_read': 'gen_ai.usage.cache_read.input_tokens', 'cache_write': 'gen_ai.usage.cache_write.input_tokens',
        'reasoning': 'gen_ai.usage.reasoning.output_tokens'}


def session(harness, sid):
    return {'harness': harness, 'id': sid, 'humans': [], 'activity': [], 'branch': None, 'repo': None,
            'prs': set(), 'pr_links': set(), 'stamps': set(), 'launched': False, 'parent': None,
            'usage': [], 'dollars': None, 'version': None, 'models': set(), 'asked': set()}


def usage(found, instant, model, effort, tokens, dollars=None):
    """One model response: tokens normalized to TOKENS, dollars only if the harness reported them."""
    found['usage'].append((instant, tokens, dollars))
    found['models'].add(f'{model}@{effort}' if effort else model)


def asks(text):
    return text.rstrip().endswith('?')


def evidence(found, text):
    found['stamps'].update(STAMP.findall(text))
    found['prs'].update(f'{repo}#{number}' for repo, number in PR_URL.findall(text))


def text_of(content):
    if isinstance(content, str):
        return content
    return '\n'.join(block.get('text', '') for block in content if isinstance(block, dict))


def read_claude(entries, sid):
    found = session('claude', sid)
    messages = set()
    for entry in entries:
        kind, stamp = entry['type'], entry.get('timestamp')
        if kind == 'pr-link':
            found['pr_links'].add(f"{entry['prRepository']}#{entry['prNumber']}")
        if entry.get('gitBranch'):
            found['branch'] = entry['gitBranch']
        if kind == 'cost-state':
            found['dollars'] = entry.get('totalCostUSD')
        if kind == 'assistant':
            message, instant = entry['message'], when(stamp)
            found['activity'].append(instant)
            found['version'] = entry.get('version') or found['version']
            text = text_of(message['content'])
            evidence(found, text)
            if asks(text) or any(isinstance(b, dict) and b.get('name') == 'AskUserQuestion' for b in message['content']):
                found['asked'].add(instant)
            spent = message.get('usage')
            if spent and message.get('id') not in messages:  # streamed lines repeat one message's usage
                messages.add(message.get('id'))
                cache_read, cache_write = spent.get('cache_read_input_tokens', 0), spent.get('cache_creation_input_tokens', 0)
                usage(found, instant, message.get('model'), None, {
                    'input': spent.get('input_tokens', 0) + cache_read + cache_write, 'output': spent.get('output_tokens', 0),
                    'cache_read': cache_read, 'cache_write': cache_write,
                    'reasoning': (spent.get('output_tokens_details') or {}).get('thinking_tokens', 0)})
        elif kind == 'user':
            content = entry['message']['content']
            origin = entry.get('origin')
            human = (not entry.get('isMeta') and not (isinstance(content, list) and any(
                isinstance(b, dict) and b.get('type') == 'tool_result' for b in content))
                and (origin.get('kind') == 'human' if isinstance(origin, dict) else entry.get('promptSource') != 'system'))
            if human:
                found['humans'].append(when(stamp))
                evidence(found, text_of(content))
    return found


def read_codex(entries, sid):
    found = session('codex', sid)
    model = effort = None
    for entry in entries:
        payload = entry.get('payload') or {}
        if entry['type'] == 'turn_context':
            model, effort = payload.get('model'), payload.get('effort')
        elif entry['type'] == 'token_usage_record':
            spent = payload['usage']
            usage(found, when(entry['timestamp']), model, effort, {
                'input': spent.get('input_tokens', 0), 'output': spent.get('output_tokens', 0),
                'cache_read': spent.get('cached_input_tokens', 0), 'cache_write': spent.get('cache_write_input_tokens', 0),
                'reasoning': spent.get('reasoning_output_tokens', 0)})
        elif entry['type'] == 'session_meta':
            found['id'] = payload.get('id', sid)
            found['version'] = payload.get('cli_version')
            source = payload.get('source')
            found['launched'] = payload.get('originator') == 'codex_exec' or isinstance(source, dict)
            if isinstance(source, dict):
                found['parent'] = ((source.get('subagent') or {}).get('thread_spawn') or {}).get('parent_thread_id')
            git = payload.get('git') or {}
            found['branch'] = git.get('branch')
            match = re.search(r'github\.com[/:]([\w.-]+/[\w.-]+?)(?:\.git)?$', git.get('repository_url') or '')
            found['repo'] = match.group(1) if match else None
        elif entry['type'] == 'event_msg' and payload.get('type') == 'item_completed':
            item = payload['item']
            if item['type'] == 'UserMessage':
                found['humans'].append(when(entry['timestamp']))
                evidence(found, text_of(item.get('content') or []))
            else:
                found['activity'].append(when(entry['timestamp']))
                if item['type'] == 'AgentMessage':
                    text = text_of(item.get('content') or [])
                    evidence(found, text)
                    if asks(text):
                        found['asked'].add(when(entry['timestamp']))
    return found


def read_pi(entries, sid):
    found = session('pi', sid)
    effort = None
    for entry in entries:
        if entry['type'] == 'session':
            found['id'] = entry.get('id', sid)
            found['version'] = str(entry.get('version'))
        if entry['type'] == 'thinking_level_change':
            effort = entry.get('thinkingLevel')
        if entry['type'] != 'message':
            continue
        role = entry['message']['role']
        if role == 'user':
            found['humans'].append(when(entry['timestamp']))
            evidence(found, text_of(entry['message']['content']))
        elif role in ('assistant', 'toolResult'):
            instant = when(entry['timestamp'])
            found['activity'].append(instant)
            if role == 'assistant':
                message = entry['message']
                text = text_of(message['content'])
                evidence(found, text)
                if asks(text):
                    found['asked'].add(instant)
                spent = message.get('usage')
                if spent:
                    cache_read, cache_write = spent.get('cacheRead', 0), spent.get('cacheWrite', 0)
                    usage(found, instant, message.get('model'), effort, {
                        'input': spent.get('input', 0) + cache_read + cache_write, 'output': spent.get('output', 0),
                        'cache_read': cache_read, 'cache_write': cache_write, 'reasoning': spent.get('reasoning', 0)},
                        (spent.get('cost') or {}).get('total'))
    # Pi records no launch mode; a single-prompt session is a machine launch (`pi -p`, crew workers).
    found['launched'] = len(found['humans']) <= 1
    return found


READERS = {'claude': read_claude, 'codex': read_codex, 'pi': read_pi}


def transcript(name):
    """False for macOS resource forks and for child-agent records (Claude subagents, Pi delegate and other *_transcript files)."""
    return (name.suffix == '.jsonl' and not name.name.startswith('._') and 'subagents' not in name.parts
            and not name.stem.endswith('_transcript'))  # Pi child agents: _delegate_, _researcher_, ...)


def transcripts(dirs, snapshots):
    """(harness, name, lines) for each transcript. Live folders first; snapshots fill in what has been deleted."""
    seen = set()
    for harness, directory in dirs.items():
        for path in sorted(Path(directory).glob(GLOBS[harness])) if directory else ():
            if not transcript(path):
                continue
            seen.add((harness, path.name))
            yield harness, path.stem, path.read_text(errors='replace').splitlines()
    for archive in sorted(Path(snapshots).glob('*.tgz')) if snapshots else ():
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
                yield harness, name.stem, bundle.extractfile(member).read().decode(errors='replace').splitlines()


def link(found, rows, by_id):
    """Changes this session worked on, each with the strongest evidence: stamped, pr-link, branch, text."""
    links = {}
    for stamp in found['stamps']:
        if stamp in by_id:
            links.setdefault(by_id[stamp], 'stamped')
    for change in found['pr_links']:
        if change in rows:
            links.setdefault(change, 'pr-link')
    span = found['humans'] or found['activity']
    if not span:
        return links
    start, end = min(span), max(span)
    if found['branch'] not in TRUNK and found['branch'] is not None:
        for change, row in rows.items():
            vcs, times = row.get('vcs') or {}, row.get('times') or {}
            if vcs.get('vcs.ref.head.name') != found['branch']:
                continue
            if found['repo'] and vcs.get('vcs.repository.name') != found['repo']:
                continue
            opened, closed = when(times.get('created')), when(times.get('closed'))
            if opened and opened.timestamp() - 86400 <= end.timestamp() and (not closed or start <= closed):
                links.setdefault(change, 'branch')
    for change in found['prs']:
        if change in rows:
            links.setdefault(change, 'text')
    return links


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
            out.append((max(activity[index - 1], human - cap * 60), human))
    return out


def merge_timeline(intervals):
    """intervals: (start, end, {label: weight}). Each instant is split evenly between the intervals covering it."""
    points = sorted({p for start, end, _ in intervals for p in (start, end)})
    totals = {}
    for left, right in zip(points, points[1:]):
        covering = [labels for start, end, labels in intervals if start <= left and end >= right]
        for labels in covering:
            for label, weight in labels.items():
                totals[label] = totals.get(label, 0) + (right - left) * weight / len(covering)
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
        weights = [tokens['input'] + tokens['output'] for _, tokens, _ in found['usage']]
        for (instant, tokens, dollars), weight in zip(found['usage'], weights):
            if found['harness'] == 'claude' and found['dollars'] is not None:
                dollars = found['dollars'] * weight / (sum(weights) or 1)
            for label, share in (assign(instant.timestamp(), found['links'], rows) or unattributed(instant.timestamp())).items():
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


def configs(everyone):
    """Harness versions and models per change, split by sessions the operator talked to and launched workers."""
    seen = {}
    for found in everyone:
        role = 'launched' if found['launched'] else 'interactive'
        for change in found['links']:
            config = seen.setdefault(change, {'harnesses': set(), 'interactive': set(), 'launched': set()})
            config['harnesses'].add(f"{found['harness']}@{found['version']}")
            config[role].update(model for model in found['models'] if model)
    return {change: {'harnesses': sorted(config['harnesses']),
                     'models_seen': {'interactive': sorted(config['interactive']), 'launched': sorted(config['launched'])},
                     'config_mixed': len({m.split('@')[0] for m in config['interactive'] | config['launched']}) > 1}
            for change, config in seen.items()}


def sweep(ledger_path, claude=DEFAULT_DIRS['claude'], codex=DEFAULT_DIRS['codex'], pi=DEFAULT_DIRS['pi'],
          snapshots=DEFAULT_SNAPSHOTS):
    ledger_path = Path(ledger_path)
    existing = read(ledger_path)
    rows = {change: row for change, row in fold(existing).items() if 'outcome' in row}
    by_id = {row['change_id']: change for change, row in rows.items() if row.get('change_id')}
    everyone, skipped = [], 0
    for harness, name, lines in transcripts({'claude': claude, 'codex': codex, 'pi': pi}, snapshots):
        try:
            entries = [json.loads(line) for line in lines if line.strip()]
            found = READERS[harness](entries, name)
        except (ValueError, KeyError, TypeError, AttributeError):
            skipped += 1
            continue
        if found['humans'] or found['usage']:
            found['links'] = link(found, rows, by_id)
            everyone.append(found)
    by_session = {(found['harness'], found['id']): found for found in everyone}
    for found in everyone:  # child agents work for their parent's changes
        parent = by_session.get((found['harness'], found['parent']))
        if parent and not found['links']:
            found['links'] = {change: 'parent' for change in parent['links']}
    talked = [found for found in everyone if not found['launched'] and found['humans']]

    minutes = {}
    for cap in CAPS:
        intervals = [(start, end, assign(end, found['links'], rows) or unattributed(end))
                     for found in talked for start, end in credits(found, cap)]
        minutes[cap] = merge_timeline(intervals)
    touches, phases, members = {}, {}, {}
    for found in talked:
        first = min(found['humans'])
        for human in found['humans']:
            kind = phase(found, human, first)
            for label, weight in (assign(human.timestamp(), found['links'], rows) or unattributed(human.timestamp())).items():
                merged = when((rows.get(label, {}).get('times') or {}).get('merged'))
                touch = 'post_merge' if merged and human > merged else kind
                touches[label] = touches.get(label, 0) + weight
                counts = phases.setdefault(label, {})
                counts[touch] = round(counts.get(touch, 0) + weight, 2)
    for found in everyone:
        for change, how in found['links'].items():
            members.setdefault(change, []).append({'harness': found['harness'], 'id': found['id'], 'link': how,
                                                   'role': 'launched' if found['launched'] else 'interactive'})
    spent, setups = costs(everyone, rows), configs(everyone)

    operator = {}
    for label in set(touches) | set(minutes[CAPS[0]]):
        numbers = {'minutes': {f'c{cap}': round(minutes[cap].get(label, 0) / 60, 1) for cap in CAPS},
                   'touches': round(touches.get(label, 0), 2)}
        operator[label] = {'unattributed': numbers} if label.startswith('~') else {'operator': {
            **numbers, 'phases': phases.get(label, {}), 'method': 'gap-cap',
            'sessions': sorted(members.get(label, []), key=lambda s: (s['harness'], s['id']))}}
    money = {label: {'unattributed_cost': value} if label.startswith('~') else {'cost': value, 'config': setups.get(label)}
             for label, value in spent.items()}
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


def assign(instant, links, rows):
    """Weights per change for one moment of a session linked to several changes: those whose window holds it."""
    if not links:
        return None
    if len(links) == 1:
        return {next(iter(links)): 1.0}
    inside = [change for change in links if window(rows[change])[0] <= instant <= window(rows[change])[1]]
    if not inside:
        inside = [min(links, key=lambda c: min(abs(instant - edge) for edge in window(rows[c])))]
    return {change: 1 / len(inside) for change in inside}


def week(instant):
    year, number, _ = datetime.fromtimestamp(instant, timezone.utc).isocalendar()
    return f'{year}-W{number:02d}'
