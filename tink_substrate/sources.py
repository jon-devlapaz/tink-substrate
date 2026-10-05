"""Read selected sources. No mutations, shell interpolation, or discovery of executables."""

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tomllib


class SourceError(ValueError):
    pass


# Links a record may omit until the work reaches them: a hunch has no branch, run, or PR yet.
LINKS = ('branch', 'run', 'pr', 'seed', 'handoff')
LINKED_SOURCES = {'github': ('pr', 'pull request'), 'workflow': ('run', 'tink-sdlc run'),
                  'seed': ('seed', 'seed'), 'handoff': ('handoff', 'handoff')}
GATE_STATES = ('approved', 'pending', 'stale', 'changes-requested')


def now():
    return datetime.now(timezone.utc).isoformat()


def command(argv, cwd=None, timeout=12):
    env = {**os.environ, 'GIT_TERMINAL_PROMPT': '0', 'GH_PROMPT_DISABLED': '1'}
    try:
        result = subprocess.run(argv, cwd=cwd, env=env, capture_output=True,
                                text=True, errors='replace', timeout=timeout)
    except subprocess.TimeoutExpired:
        raise SourceError(f'{argv[0]} did not respond within {timeout} seconds.') from None
    except OSError as error:
        raise SourceError(f'{argv[0]} unavailable: {error.strerror}') from None
    if result.returncode:
        detail = (result.stderr or result.stdout).strip()[:400]
        raise SourceError(detail or f'{argv[0]} exited {result.returncode}.')
    if len(result.stdout) > 2_000_000:
        raise SourceError('Source output exceeded 2 MB.')
    return result.stdout


def git(root, *args):
    return command(['git', '--no-optional-locks', '-c', 'core.fsmonitor=false', '-C', str(root), *args])


def inside(root, relative):
    path = (root / relative).resolve()
    if Path(relative).is_absolute() or not path.is_relative_to(root.resolve()):
        raise SourceError('Artifact path must stay inside the selected checkout.')
    return path


def read_record(path):
    text = Path(path).read_text(encoding='utf-8')
    parts = text.split('+++', 2)
    if len(parts) != 3 or parts[0].strip():
        raise SourceError('Work record needs TOML metadata between +++ lines.')
    meta = tomllib.loads(parts[1])
    if meta.get('schema') != 1:
        raise SourceError('Unsupported work record schema.')
    for field in ('title', 'project', 'owner', 'next_action'):
        if not isinstance(meta.get(field), str) or not meta[field].strip():
            raise SourceError(f'Work record needs a nonempty {field}.')
    for field in LINKS:
        if field in meta and (not isinstance(meta[field], str) or not meta[field].strip()):
            raise SourceError(f'Omit {field} until it exists, or give it a nonempty value.')
    if 'run' in meta and not re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9_-]*', meta['run']):
        raise SourceError('Invalid run name.')
    if not isinstance(meta.get('questions', []), list) or not all(isinstance(x, str) for x in meta.get('questions', [])):
        raise SourceError('Questions must be a list of strings.')
    if 'pr' in meta:
        parse_pr(meta['pr'])
    return {**dict.fromkeys(LINKS), **meta, 'body': parts[2].strip(), 'path': str(Path(path).resolve())}


def parse_pr(url):
    match = re.fullmatch(r'https://github\.com/([\w.-]+)/([\w.-]+)/pull/([1-9][0-9]*)', url)
    if not match:
        raise SourceError('Use an https://github.com/owner/repository/pull/number URL.')
    return f'{match[1]}/{match[2]}', match[3]


def observe(reader):
    try:
        data = reader()
        return {'status': 'ok', 'checked_at': now(), 'data': data}
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as error:
        return {'status': 'unavailable', 'checked_at': now(), 'error': str(error)}


def changes(root):
    parts = git(root, 'status', '--porcelain=v1', '-z', '--untracked-files=normal').split('\0')
    files, i = [], 0
    while i < len(parts) and parts[i]:
        entry = parts[i]
        if len(entry) < 4:
            raise SourceError('Git returned an invalid status entry.')
        files.append({'status': entry[:2], 'path': entry[3:]})
        i += 2 if 'R' in entry[:2] or 'C' in entry[:2] else 1
    return {'dirty': bool(files), 'count': len(files), 'files': files[:100], 'truncated': len(files) > 100}


def git_state(root):
    top = Path(git(root, 'rev-parse', '--show-toplevel').strip()).resolve()
    if top != root.resolve():
        raise SourceError('Selected checkout must be a Git worktree root.')
    before = git(root, 'rev-parse', 'HEAD').strip()
    branch = git(root, 'symbolic-ref', '--quiet', '--short', 'HEAD').strip() if git(root, 'branch', '--show-current').strip() else '(detached)'
    worktrees, current = [], {}
    for field in git(root, 'worktree', 'list', '--porcelain', '-z').split('\0'):
        if not field:
            if current:
                worktrees.append(current)
                current = {}
            continue
        key, _, value = field.partition(' ')
        if key == 'worktree':
            current['path'] = value
        elif key in ('HEAD', 'branch', 'locked', 'prunable', 'bare', 'detached'):
            current[key.lower()] = value or True
    if current:
        worktrees.append(current)
    for tree in worktrees:
        tree['branch'] = str(tree.get('branch', '(detached)')).removeprefix('refs/heads/')
        tree['selected'] = Path(tree['path']).resolve() == top
        tree['changes'] = observe(lambda tree=tree: changes(Path(tree['path'])))
    branches = []
    for line in git(root, 'for-each-ref', '--format=%(refname:short)%00%(objectname)%00%(upstream:short)%00%(upstream:track)', 'refs/heads').splitlines():
        name, head, upstream, tracking = line.split('\0')
        branches.append(dict(name=name, head=head, upstream=upstream, tracking=tracking))
    after = git(root, 'rev-parse', 'HEAD').strip()
    if before != after:
        raise SourceError('HEAD changed during collection. Refresh to read it again.')
    return {'checkout': str(top), 'branch': branch, 'head': after, 'worktrees': worktrees, 'branches': branches}


def pr_state(url):
    repo, number = parse_pr(url)
    value = json.loads(command(['gh', 'pr', 'view', number, '--repo', repo, '--json',
        'number,url,title,state,isDraft,headRefOid,headRefName,baseRefName,reviewDecision,statusCheckRollup,mergedAt']))
    if value.get('url') != url or value.get('state') not in ('OPEN', 'CLOSED', 'MERGED'):
        raise SourceError('GitHub returned an unexpected PR identity or state.')
    checks = value.get('statusCheckRollup')
    if not isinstance(checks, list) or not all(isinstance(x, dict) for x in checks):
        raise SourceError('GitHub checks were not a list.')
    statuses = []
    for check in checks:
        if check.get('__typename') == 'CheckRun':
            statuses.append('pending' if check.get('status') != 'COMPLETED' else
                            'passed' if check.get('conclusion') == 'SUCCESS' else
                            'skipped' if check.get('conclusion') in ('SKIPPED', 'NEUTRAL') else
                            'failed' if check.get('conclusion') in ('FAILURE', 'TIMED_OUT', 'CANCELLED', 'ACTION_REQUIRED', 'STALE', 'STARTUP_FAILURE') else 'unknown')
        elif check.get('__typename') == 'StatusContext':
            statuses.append({'SUCCESS': 'passed', 'PENDING': 'pending', 'FAILURE': 'failed', 'ERROR': 'failed'}.get(check.get('state'), 'unknown'))
        else:
            statuses.append('unknown')
    value['ci'] = ('none' if not statuses else 'failed' if 'failed' in statuses else
                   'pending' if 'pending' in statuses else 'unknown' if 'unknown' in statuses else
                   'passed' if all(s == 'passed' for s in statuses) else 'includes skipped checks')
    return value


def workflow_state(root, record, trusted):
    if not trusted:
        raise SourceError('SDLC execution is not enabled. Register with --trust-sdlc after reviewing the selected runtime.')
    script = inside(root, '_system/scripts/sdlc.py')
    if not script.is_file():
        raise SourceError('No SDLC runtime in this checkout.')
    argv = [sys.executable, '-B', str(script), 'status', record['run']]
    try:
        output = command([*argv, '--json'], root, timeout=15)
    except SourceError as error:
        # Only an explicit unsupported flag allows the older text interface.
        # Malformed JSON, identity mismatches and runtime failures stay errors.
        if not any(line.strip() == 'sdlc.py: error: unrecognized arguments: --json'
                   for line in str(error).splitlines()):
            raise
        output = command(argv, root, timeout=15)
        if not output.strip():
            raise SourceError('SDLC text status was empty.')
        return {'slug': record['run'], 'format': 'text', 'status_text': output,
                'verification_status': 'unknown', 'verification': None,
                'gates': [], 'checklist': [], 'decisions': [], 'errors': [],
                'next_action': 'Read the installed SDLC status below. Structured verification is unavailable.'}
    value = json.loads(output)
    if value.get('protocol') != 'tink-sdlc' or type(value.get('api_version')) is not int or value.get('api_version') != 1 or value.get('workspace') != str(root.resolve()):
        raise SourceError('Unsupported or mismatched SDLC API identity.')
    run = value.get('run')
    if not isinstance(run, dict) or run.get('slug') != record['run']:
        raise SourceError('SDLC returned a different run.')
    status = run.get('verification_status')
    if status not in ('blocked', 'running', 'not-run', 'current', 'stale', 'failed', 'interrupted'):
        raise SourceError('Unknown SDLC verification status.')
    receipt = run.get('verification') or {}
    if status == 'current' and receipt.get('passed') is not True:
        raise SourceError('SDLC current status has no passing verification.')
    for item in run.get('checklist', []):
        if item.get('status') not in ('pending', 'passed', 'failed'):
            raise SourceError('Unknown checklist status.')
    # Gates, errors, and decisions carry the reason for a status and any human decision it awaits.
    gates = run.get('gates')
    if not isinstance(gates, list) or not all(isinstance(g, dict) and type(g.get('stage')) is int and
                                              g.get('status') in GATE_STATES and isinstance(g.get('blocked'), bool) for g in gates):
        raise SourceError('Unknown SDLC gate data.')
    errors = run.get('errors')
    if not isinstance(errors, list) or not all(isinstance(e, str) for e in errors):
        raise SourceError('SDLC errors were not a list of messages.')
    decisions = run.get('decisions')
    if not isinstance(decisions, list) or not all(isinstance(d, dict) and type(d.get('stage')) is int and
                                                  d.get('decision') in ('approved', 'changes-requested') for d in decisions):
        raise SourceError('Unknown SDLC decision receipts.')
    return {key: run.get(key) for key in ('slug', 'meta', 'gates', 'verification_status', 'verification', 'checklist', 'next_action', 'errors', 'has_lock', 'decisions')}


def artifact(root, relative):
    path = inside(root, relative)
    if not path.is_file():
        raise SourceError('Linked artifact is missing.')
    if path.stat().st_size > 256_000:
        raise SourceError('Linked artifact exceeds 256 KB; open it locally.')
    return {'path': str(path), 'text': path.read_text(encoding='utf-8')}



def stage_artifacts(root, record, profile=None):
    """Read a bounded set of known run documents; never expose a file browser."""
    run = record.get('run')
    base = f'runs/{run}/' if run else None
    groups = [
        ('plan', 'Plan', [('Seed contract', record.get('seed')),
                         ('Brief', base and base + 'brief.md'),
                         ('Intent', base and base + '01-plan/output/intent.md')]),
        ('design', 'Design', [('Specification', base and base + '02-design/output/spec.md')]),
        ('build', 'Build', [('Implementation plan', base and base + '03-build/output/plan.md'),
                           ('Checklist', base and base + 'checklist.json'),
                           ('Handoff', record.get('handoff'))]),
        ('test', 'Test', [('Test log', base and base + '04-test/output/test-log.md'),
                         ('Verification receipt', base and base + '04-test/output/verification.json')]),
        ('review', 'Review & release', [('Review findings', base and base + '05-deploy/output/REVIEW-findings.md')]),
    ]
    if profile == 'light':
        checklist = groups[2][2].pop(1)
        groups[0][2].insert(2, checklist)
    result = []
    for key, title, candidates in groups:
        documents = []
        for label, relative in candidates:
            if not relative:
                continue
            # Missing future outputs are normal; unsafe or unreadable paths stay visible.
            def read(relative=relative):
                path = inside(root, relative)
                if not path.exists() and not (root / relative).is_symlink():
                    return None
                return artifact(root, relative)
            source = observe(read)
            if source['status'] == 'ok' and source['data'] is None:
                if relative not in (record.get('seed'), record.get('handoff')):
                    continue
                source = {'status': 'unavailable', 'checked_at': now(), 'error': 'Linked artifact is missing.'}
            documents.append({'label': label, 'relative_path': relative, **source})
        result.append({'id': key, 'title': title, 'documents': documents})
    return result

def attention(record, sources):
    items = []
    for key, label in (('git', 'Git'), ('github', 'GitHub'), ('workflow', 'Verification')):
        if sources[key]['status'] not in ('ok', 'not-linked'):
            items.append(f'{label} is unavailable. Its state is unknown.')
    g = sources['git'].get('data', {})
    p = sources['github'].get('data', {})
    w = sources['workflow'].get('data', {})
    if g and record['branch'] and g['branch'] != record['branch']:
        items.append('Selected checkout is on a different branch from the work record.')
    if g and p and p.get('headRefOid') != g['head']:
        items.append('The PR head differs from this checkout. CI does not cover this local HEAD.')
    if w.get('format') == 'text':
        items.append('Older SDLC: read its text status below. Structured verification and approval are unavailable.')
    if w and w['verification_status'] in ('stale', 'failed', 'interrupted'):
        items.append(f"Local verification is {w['verification_status']}.")
    for gate in w.get('gates', []):
        if gate['status'] != 'approved' and not gate['blocked']:
            next_step = {"pending": "Review the documents, then approve or request changes.", "stale": "Approved inputs changed. Review again before continuing.", "changes-requested": "Revise the work before requesting another decision."}[gate["status"]]
            items.append(f"tink-sdlc stage {gate['stage']} is {gate['status']}. {next_step}")
    for error in w.get('errors', []):
        items.append(f'tink-sdlc reports: {error}')
    if p.get('ci') in ('failed', 'pending', 'unknown', 'none', 'includes skipped checks'):
        items.append(f"PR checks: {p['ci']}.")
    if p.get('state') == 'OPEN' and p.get('isDraft'):
        items.append('The PR is a draft.')
    if p.get('state') == 'OPEN' and p.get('reviewDecision') == 'CHANGES_REQUESTED':
        items.append('GitHub reports changes requested on the PR.')
    elif p.get('state') == 'OPEN' and p.get('reviewDecision') != 'APPROVED':
        items.append('The PR is open; GitHub does not report approval.')
    if p.get('state') == 'CLOSED':
        items.append('The PR closed without merging. Revisit the saved next action before continuing.')
    for tree in g.get('worktrees', []):
        change = tree['changes']
        if change['status'] != 'ok':
            items.append(f"Cannot read worktree: {tree['path']}")
        elif change['data']['dirty']:
            items.append(f"{tree['branch']} has {change['data']['count']} changed paths.")
    for name in ('seed', 'handoff'):
        if sources[name]['status'] not in ('ok', 'not-linked'):
            items.append(f'The linked {name} is unavailable.')
    return items


def not_linked(label):
    return {'status': 'not-linked', 'checked_at': now(), 'reason': f'The work record names no {label} yet.'}


def snapshot(config):
    record = read_record(config['work'])
    root = Path(config['checkout']).resolve()
    readers = {
        'git': lambda: git_state(root),
        'github': lambda: pr_state(record['pr']),
        'workflow': lambda: workflow_state(root, record, config.get('trust_sdlc', False)),
        'seed': lambda: artifact(root, record['seed']),
        'handoff': lambda: artifact(root, record['handoff']),
    }
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {name: executor.submit(observe, read) for name, read in readers.items()
                   if name not in LINKED_SOURCES or record[LINKED_SOURCES[name][0]]}
        sources = {name: futures[name].result() if name in futures else not_linked(LINKED_SOURCES[name][1])
                   for name in readers}
    return {'schema': 1, 'observed_at': now(), 'record': record, 'sources': sources,
            'artifacts': stage_artifacts(root, record, sources['workflow'].get('data', {}).get('meta', {}).get('profile')),
            'attention': attention(record, sources),
            'limits': 'Sources were checked separately. Refresh before acting. This view does not approve changes or release software.'}
