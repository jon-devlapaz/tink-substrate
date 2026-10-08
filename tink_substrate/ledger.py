"""Record one observation per change from GitHub and git, then report what the observations show.

The sweep only reads: `gh` for pull requests and review comments, `git diff` in a local clone for size. It appends
JSON lines to the ledger and skips any line already there, so running it again is safe.
"""

from datetime import datetime
import json
from pathlib import Path
import re
import secrets
import statistics
import subprocess

from . import __version__

DEFAULT_LEDGER = Path.home() / '.local/share/tink-substrate/ledger/changes.jsonl'
PROCESS_PATH = re.compile(r'runs/')  # matched at the repository root only
PR_FIELDS = ('number,title,state,createdAt,mergedAt,closedAt,isDraft,headRefName,baseRefName,'
             'mergeCommit,reviews,body')  # commits are fetched per PR: listing them exceeds GitHub's node budget
MIN_CELL = 5
CHANGE_ID = re.compile(r'c\d{6}[a-z2-7]{4}')
BASE32 = 'abcdefghijklmnopqrstuvwxyz234567'


def mint(now=None):
    """A change ID minted at intake: `c` + yyMMdd + 4 base32 characters, e.g. c261007k3xq."""
    return 'c' + (now or datetime.now()).strftime('%y%m%d') + ''.join(secrets.choice(BASE32) for _ in range(4))


def run_gh(args):
    result = subprocess.run(['gh', *args], capture_output=True, text=True)
    if result.returncode:
        raise ValueError(f'gh {" ".join(args[:3])}: {result.stderr.strip()}')
    return result.stdout


def when(value):
    return datetime.fromisoformat(value.replace('Z', '+00:00')) if value else None


def git_out(clone, *args):
    result = subprocess.run(['git', '-C', str(clone), *args], capture_output=True, text=True)
    return None if result.returncode else result.stdout


def base(clone, merge, commits):
    """The commit the change started from. A merge commit or squash adds one commit on top of its first parent;
    a rebase merge replays every PR commit, recognised by matching their subjects in order."""
    parents = (git_out(clone, 'rev-list', '--parents', '-n1', merge) or '').split()
    count = len(commits)
    if len(parents) == 2 and count > 1:
        subjects = (git_out(clone, 'log', '--format=%s', f'-n{count}', merge) or '').splitlines()[::-1]
        if subjects == [c.get('messageHeadline') for c in commits]:
            return f'{merge}~{count}'
    return f'{merge}^1'


def size(clone, merge, commits=()):
    """Lines added and deleted by the change, with run records counted apart. None when the commit is not local."""
    if not merge:
        return None
    output = git_out(clone, 'diff', '--numstat', '-z', '-M', base(clone, merge, commits), merge)
    if output is None:
        return None
    added = deleted = files = process = 0
    # -z: "add<TAB>del<TAB>path<NUL>", or for a rename "add<TAB>del<TAB><NUL>old<NUL>new<NUL>"
    fields = iter(output.split('\0'))
    for entry in fields:
        if not entry:
            continue
        add, delete, path = entry.split('\t', 2)
        if not path:
            next(fields)
            path = next(fields)
        add, delete = int(add) if add != '-' else 0, int(delete) if delete != '-' else 0
        files += 1
        if PROCESS_PATH.match(path):
            process += add + delete
        else:
            added, deleted = added + add, deleted + delete
    return {'product_add': added, 'product_del': deleted, 'files': files, 'process_lines': process}


def change_id(clone, merge, commits, body):
    """The stamped change ID: a `Tink-Change:` line in the PR body, else the run record committed by the change."""
    match = re.search(r'^Tink-Change: (' + CHANGE_ID.pattern + r')\s*$', body or '', re.M)
    if match:
        return match.group(1)
    if not merge:
        return None
    paths = (git_out(clone, 'diff', '--name-only', '-z', base(clone, merge, commits), merge, '--', 'runs/') or '')
    for path in paths.split('\0'):
        if re.fullmatch(r'runs/[^/]+/tools\.json', path):
            try:
                value = json.loads(git_out(clone, 'show', f'{merge}:{path}') or '{}').get('change')
            except json.JSONDecodeError:
                continue
            if isinstance(value, str) and CHANGE_ID.fullmatch(value):
                return value
    return None


def review(pr, comments):
    """A round is a reviewed commit that a later commit replaced. Each review names the commit it saw, so this does
    not depend on when commits were made or pushed."""
    final = pr['commits'][-1]['oid'] if pr['commits'] else None
    reviewed = {(r.get('commit') or {}).get('oid') for r in pr['reviews'] if r.get('state') != 'PENDING'} - {None, final}
    return {'rounds': len(reviewed), 'p1': sum('P1 Badge' in c.get('body', '') for c in comments)}


def observe(repo, clone, prs, comments_for):
    reverts = {}
    merged_prs = [pr for pr in prs if pr.get('mergedAt')]
    for pr in merged_prs:
        for target in re.findall(r'Reverts ' + re.escape(repo) + r'#(\d+)', pr.get('body') or ''):
            reverts[int(target)] = f'{repo}#{pr["number"]}'
    titles = {pr['title']: pr['number'] for pr in prs}
    for pr in merged_prs:
        match = re.fullmatch(r'Revert "(.*)"', pr['title'])
        if match and match.group(1) in titles:
            reverts.setdefault(titles[match.group(1)], f'{repo}#{pr["number"]}')
    for pr in sorted(prs, key=lambda p: p['number']):
        change = f'{repo}#{pr["number"]}'
        merge = (pr.get('mergeCommit') or {}).get('oid')
        created, merged = when(pr['createdAt']), when(pr.get('mergedAt'))
        state = 'merged' if merged else 'closed' if pr['state'] == 'CLOSED' else 'open'
        fields = {
            'change_id': change_id(clone, merge, pr['commits'], pr.get('body')) if merged else None,
            'vcs': {'vcs.repository.name': repo, 'vcs.change.id': str(pr['number']),
                    'vcs.ref.head.name': pr['headRefName'], 'vcs.ref.head.revision': merge},
            'outcome': {'state': state, 'reverted_by': reverts.get(pr['number'])},
            'times': {'created': pr['createdAt'], 'merged': pr.get('mergedAt'), 'closed': pr.get('closedAt'),
                      'lead_hours': round((merged - created).total_seconds() / 3600, 2) if merged else None},
            'size': size(clone, merge, pr['commits']) if merged else None,
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
                pages = json.loads(run_gh(['api', f'repos/{repo}/pulls/{number}/comments', '--paginate', '--slurp']))
                return [comment for page in pages for comment in page]
            for line in observe(repo, clone, prs, comments_for):
                if latest.get(json.dumps(line['key'])) == line['fields']:
                    continue
                out.write(json.dumps(line, sort_keys=True) + '\n')
                added += 1
    return added


def cell(values, show):
    return show(values) if len(values) >= MIN_CELL else '—'


def operator_view(rows, unattributed):
    """The one number: useful merged changes per operator hour, at caps C = 2, 5 and 10 minutes."""
    weeks = {}
    for row in rows.values():
        stamp = row['times'].get('merged') or row['times'].get('closed')
        if stamp:
            year, number, _ = when(stamp).isocalendar()
            weeks.setdefault(f'{year}-W{number:02d}', []).append(row)
    lines = ['View 1b: operator attention (minutes from transcripts; C = gap cap)']
    for name in sorted(set(weeks) | set(unattributed)):
        group = weeks.get(name, [])
        merged = [r for r in group if r['outcome']['state'] == 'merged']
        useful = [r for r in merged if not r['outcome']['reverted_by']]
        covered = [r for r in merged if r.get('operator')]
        if not covered and name not in unattributed:
            continue
        loose = unattributed.get(name, {}).get('minutes', {})
        hours = {cap: (sum(r['operator']['minutes'][cap] for r in group if r.get('operator')) + loose.get(cap, 0)) / 60
                 for cap in ('c2', 'c5', 'c10')}
        per_hour = ' '.join(f'{cap}:{len(useful) / hours[cap]:.1f}' if hours[cap] and len(covered) >= MIN_CELL
                            else f'{cap}:—' for cap in hours)
        median = cell([r['operator']['minutes']['c5'] for r in covered], lambda v: f'{statistics.median(v):.0f}')
        lines.append(f'  {name}  with operator data {len(covered)}/{len(merged)}  operator h {hours["c5"]:.1f}'
                     f'  unattributed h {loose.get("c5", 0) / 60:.1f}  median min/change {median}'
                     f'  useful/h {per_hour}')
    return lines


def report(rows):
    unattributed = {change.split('/', 1)[1]: row['unattributed'] for change, row in rows.items() if row.get('unattributed')}
    rows = {change: row for change, row in rows.items() if 'outcome' in row}
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
    lines += operator_view(rows, unattributed)
    reverted = sum(bool(row['outcome']['reverted_by']) for row in merged)
    share = lambda values: f'{100 * sum(values) / len(values):.0f}%'
    lines += ['View 3: quality',
              f'  merged {len(merged)}  reverted {reverted}',
              f'  median review rounds {cell([r["review"]["rounds"] for r in merged], median)}',
              f'  changes with a P1 finding {cell([r["review"]["p1"] > 0 for r in merged], share)}',
              f'  median lead hours {cell([r["times"]["lead_hours"] for r in merged], median)}',
              f'  (cells with fewer than {MIN_CELL} changes show —)']
    return '\n'.join(lines)
