"""Record one observation per change from GitHub and git, then report what the observations show.

The sweep only reads: `gh` for pull requests and review comments, `git diff` in a local clone for size. It appends
JSON lines to the ledger and skips any line already there, so running it again is safe.
"""

from datetime import datetime
import json
from pathlib import Path
import re
import statistics
import subprocess

from . import __version__

DEFAULT_LEDGER = Path.home() / '.local/share/tink-substrate/ledger/changes.jsonl'
PROCESS_PATH = re.compile(r'(^|/)runs/')
PR_FIELDS = ('number,title,state,createdAt,mergedAt,closedAt,isDraft,headRefName,baseRefName,'
             'mergeCommit,reviews,body')  # commits are fetched per PR: listing them exceeds GitHub's node budget
MIN_CELL = 5


def run_gh(args):
    result = subprocess.run(['gh', *args], capture_output=True, text=True)
    if result.returncode:
        raise ValueError(f'gh {" ".join(args[:3])}: {result.stderr.strip()}')
    return result.stdout


def when(value):
    return datetime.fromisoformat(value.replace('Z', '+00:00')) if value else None


def size(clone, merge):
    """Lines added and deleted by the merge, with run records counted apart. None when the commit is not local."""
    if not merge:
        return None
    result = subprocess.run(['git', '-C', str(clone), 'diff', '--numstat', f'{merge}^1', merge],
                            capture_output=True, text=True)
    if result.returncode:
        return None
    added = deleted = files = process = 0
    for line in result.stdout.splitlines():
        add, delete, path = line.split('\t', 2)
        add, delete = int(add) if add != '-' else 0, int(delete) if delete != '-' else 0
        files += 1
        if PROCESS_PATH.search(path):
            process += add + delete
        else:
            added, deleted = added + add, deleted + delete
    return {'product_add': added, 'product_del': deleted, 'files': files, 'process_lines': process}


def review(pr, comments):
    """A round is a run of reviews that a later push answers. Pushes count from when the PR opened."""
    opened = when(pr['createdAt'])
    pushes = sorted(when(c['committedDate']) for c in pr['commits'])
    reviews = sorted(when(r['submittedAt']) for r in pr['reviews'] if r.get('submittedAt'))
    rounds, answered = 0, None
    for push in pushes:
        if any(r < push and (answered is None or r > answered) for r in reviews):
            rounds += 1
            answered = push
    return {'rounds': rounds, 'p1': sum('P1 Badge' in c.get('body', '') for c in comments),
            'pushes_after_open': sum(push > opened for push in pushes)}


def observe(repo, clone, prs, comments_for):
    reverts = {}
    for pr in prs:
        for target in re.findall(r'Reverts ' + re.escape(repo) + r'#(\d+)', pr.get('body') or ''):
            reverts[int(target)] = f'{repo}#{pr["number"]}'
    titles = {pr['title']: pr['number'] for pr in prs}
    for pr in prs:
        match = re.fullmatch(r'Revert "(.*)"', pr['title'])
        if match and match.group(1) in titles:
            reverts.setdefault(titles[match.group(1)], f'{repo}#{pr["number"]}')
    for pr in sorted(prs, key=lambda p: p['number']):
        change = f'{repo}#{pr["number"]}'
        merge = (pr.get('mergeCommit') or {}).get('oid')
        created, merged = when(pr['createdAt']), when(pr.get('mergedAt'))
        state = 'merged' if merged else 'closed' if pr['state'] == 'CLOSED' else 'open'
        fields = {
            'vcs': {'vcs.repository.name': repo, 'vcs.change.id': str(pr['number']),
                    'vcs.ref.head.name': pr['headRefName'], 'vcs.ref.head.revision': merge},
            'outcome': {'state': state, 'reverted_by': reverts.get(pr['number'])},
            'times': {'created': pr['createdAt'], 'merged': pr.get('mergedAt'), 'closed': pr.get('closedAt'),
                      'lead_hours': round((merged - created).total_seconds() / 3600, 2) if merged else None},
            'size': size(clone, merge) if merged else None,
            'review': review(pr, comments_for(pr['number'])),
        }
        yield {'schema': 1, 'key': [change, 'backfill', 'gh', pr['number']], 'change': change,
               'phase': 'backfill', 'at': pr.get('closedAt') or pr['createdAt'], 'by': f'sweep@{__version__}',
               'fields': fields}


def read(path):
    path = Path(path)
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def fold(lines):
    """Latest observation per key wins; fields of one change merge across keys in file order."""
    rows = {}
    for line in lines:
        rows.setdefault(line['change'], {}).update(line['fields'])
    return rows


def sweep(ledger_path, repos, comments=True):
    ledger_path = Path(ledger_path)
    existing = read(ledger_path)
    latest = {json.dumps(line['key']): line['fields'] for line in existing}
    added = 0
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    with ledger_path.open('a') as out:
        for repo, clone in repos:
            prs = json.loads(run_gh(['pr', 'list', '-R', repo, '--state', 'all', '--limit', '1000',
                                     '--json', PR_FIELDS]))
            for pr in prs:
                pr['commits'] = json.loads(run_gh(['pr', 'view', str(pr['number']), '-R', repo,
                                                   '--json', 'commits']))['commits']

            def comments_for(number):
                if not comments:
                    return []
                return json.loads(run_gh(['api', f'repos/{repo}/pulls/{number}/comments', '--paginate']) or '[]')
            for line in observe(repo, clone, prs, comments_for):
                if latest.get(json.dumps(line['key'])) == line['fields']:
                    continue
                out.write(json.dumps(line, sort_keys=True) + '\n')
                added += 1
    return added


def cell(values, show):
    return show(values) if len(values) >= MIN_CELL else '—'


def report(rows):
    merged = [row for row in rows.values() if row['outcome']['state'] == 'merged']
    weeks = {}
    for row in merged:
        year, week, _ = when(row['times']['merged']).isocalendar()
        weeks.setdefault(f'{year}-W{week:02d}', []).append(row)
    median = lambda values: f'{statistics.median(values):.1f}'
    lines = ['View 1: throughput (merged changes per week, median lead hours)']
    for week in sorted(weeks):
        group = weeks[week]
        lines.append(f'  {week}  merged {len(group)}  lead {cell([r["times"]["lead_hours"] for r in group], median)}')
    reverted = sum(bool(row['outcome']['reverted_by']) for row in merged)
    share = lambda values: f'{100 * sum(values) / len(values):.0f}%'
    lines += ['View 3: quality',
              f'  merged {len(merged)}  reverted {reverted}',
              f'  median review rounds {cell([r["review"]["rounds"] for r in merged], median)}',
              f'  changes with a P1 finding {cell([r["review"]["p1"] > 0 for r in merged], share)}',
              f'  median lead hours {cell([r["times"]["lead_hours"] for r in merged], median)}',
              f'  (cells with fewer than {MIN_CELL} changes show —)']
    return '\n'.join(lines)
