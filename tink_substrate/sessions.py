"""Operator minutes and touches per change, read after the fact from Claude Code, Codex and Pi transcripts.

Each transcript reduces to one session: the times the operator typed a prompt, the times the agent did anything,
and evidence linking it to changes. A prompt is credited with the gap since the agent's last activity, capped at C
minutes. Credit from parallel sessions is merged on one timeline, so a minute is never counted twice. Rows hold
counts, IDs and times, never prompt text.
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


def session(harness, sid):
    return {'harness': harness, 'id': sid, 'humans': [], 'activity': [], 'branches': [], 'repo': None,
            'prs': set(), 'pr_links': set(), 'stamps': set(), 'launched': False}


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
    for entry in entries:
        kind, stamp = entry['type'], entry.get('timestamp')
        if kind == 'pr-link':
            found['pr_links'].add(f"{entry['prRepository']}#{entry['prNumber']}")
        if entry.get('gitBranch') and stamp:  # a session can switch branches; keep each switch
            found['branches'].append((when(stamp), entry['gitBranch']))
        if kind == 'assistant':
            found['activity'].append(instant(stamp))
            evidence(found, text_of(entry['message']['content']))
        elif kind == 'user':
            content = entry['message']['content']
            origin = entry.get('origin')
            human = (not entry.get('isMeta') and not (isinstance(content, list) and any(
                isinstance(b, dict) and b.get('type') == 'tool_result' for b in content))
                and (origin.get('kind') == 'human' if isinstance(origin, dict) else entry.get('promptSource') != 'system'))
            if human:
                found['humans'].append(instant(stamp))
                evidence(found, text_of(content))
    return found


def read_codex(entries, sid):
    found = session('codex', sid)
    for entry in entries:
        payload = entry.get('payload') or {}
        if entry['type'] == 'session_meta':
            found['id'] = payload.get('id', sid)
            found['launched'] = payload.get('originator') == 'codex_exec' or isinstance(payload.get('source'), dict)
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
                    evidence(found, text_of(item.get('content') or []))
    return found


def read_pi(entries, sid):
    found = session('pi', sid)
    for entry in entries:
        if entry['type'] == 'session':
            found['id'] = entry.get('id', sid)
        if entry['type'] != 'message':
            continue
        role = entry['message']['role']
        if role == 'user':
            found['humans'].append(instant(entry['timestamp']))
            evidence(found, text_of(entry['message']['content']))
        elif role in ('assistant', 'toolResult'):
            found['activity'].append(instant(entry['timestamp']))
            if role == 'assistant':
                evidence(found, text_of(entry['message']['content']))
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
                yield harness, name.stem, bundle.extractfile(member).read().decode(errors='replace').splitlines()


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
        times = [t for t in found['humans'] + found['activity'] if branch_at(found, t) == branch]
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
    points = sorted({p for start, end, _ in intervals for p in (start, end)})
    totals = {}
    for left, right in zip(points, points[1:]):
        covering = [labels for start, end, labels in intervals if start <= left and end >= right]
        for labels in covering:
            for label, weight in labels.items():
                key = (label, week(left))
                totals[key] = totals.get(key, 0) + (right - left) * weight / len(covering)
    return totals


def sweep(ledger_path, claude=DEFAULT_DIRS['claude'], codex=DEFAULT_DIRS['codex'], pi=DEFAULT_DIRS['pi'],
          snapshots=DEFAULT_SNAPSHOTS):
    ledger_path = Path(ledger_path)
    existing = read(ledger_path)
    rows = {change: row for change, row in fold(existing).items() if 'outcome' in row}
    by_id = {row['change_id']: change for change, row in rows.items() if row.get('change_id')}
    parsed, skipped = [], 0
    for harness, name, lines in transcripts({'claude': claude, 'codex': codex, 'pi': pi}, snapshots):
        try:
            entries = [json.loads(line) for line in lines if line.strip()]
            found = READERS[harness](entries, name)
        except (ValueError, KeyError, TypeError, AttributeError):
            skipped += 1
            continue
        if found['launched'] or not found['humans']:
            continue
        found['links'] = link(found, rows, by_id)
        parsed.append(found)

    minutes = {cap: {} for cap in CAPS}
    by_week = {}  # operator time is reported in the week it was spent, not the week the change merged
    touches, members = {}, {}
    for cap in CAPS:
        intervals = []
        for found in parsed:
            links = found['links']
            for start, end in credits(found, cap):
                labels = assign(end, found, rows) or {f'~unattributed/{week(end)}': 1.0}
                intervals.append((start, end, labels))
        for (label, spent), seconds in merge_timeline(intervals).items():
            minutes[cap][label] = minutes[cap].get(label, 0) + seconds
            weekly = by_week.setdefault(label, {}).setdefault(spent, {})
            weekly[f'c{cap}'] = round(weekly.get(f'c{cap}', 0) + seconds / 60, 2)
    for found in parsed:
        for human in found['humans']:
            for label, weight in (assign(human.timestamp(), found, rows)
                                  or {f'~unattributed/{week(human.timestamp())}': 1.0}).items():
                touches[label] = touches.get(label, 0) + weight
        for change, how in found['links'].items():
            members.setdefault(change, []).append({'harness': found['harness'], 'id': found['id'], 'link': how})

    latest = {json.dumps(line['key']): line['fields'] for line in existing}
    produced = set(touches) | set(minutes[CAPS[0]])
    # A change this sweep no longer links gets its earlier operator row retracted, not left stale.
    retract = {line['change'] for line in existing if line['key'][1:3] == ['operator', 'transcripts']} - produced
    added = 0
    with ledger_path.open('a') as out:
        for label in sorted(produced | retract):
            numbers = {'minutes': {f'c{cap}': round(minutes[cap].get(label, 0) / 60, 2) for cap in CAPS},
                       'minutes_by_week': by_week.get(label, {}), 'touches': round(touches.get(label, 0), 2)}
            if label in retract:
                fields = {'unattributed' if label.startswith('~') else 'operator': None}
            elif label.startswith('~'):
                fields = {'unattributed': numbers}
            else:
                fields = {'operator': {**numbers, 'method': 'gap-cap', 'sessions': sorted(
                    members.get(label, []), key=lambda s: (s['harness'], s['id']))}}
            line = {'schema': 1, 'key': [label, 'operator', 'transcripts', 0], 'change': label, 'phase': 'operator',
                    'at': datetime.now(timezone.utc).isoformat(), 'by': f'sessions@{__version__}', 'fields': fields}
            if latest.get(json.dumps(line['key'])) == fields:
                continue
            out.write(json.dumps(line, sort_keys=True) + '\n')
            added += 1
    return {'sessions': len(parsed), 'linked': sum(bool(f['links']) for f in parsed), 'skipped': skipped,
            'added': added}


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
