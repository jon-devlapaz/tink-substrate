"""One read-only JSON for the selected change: what it is, its state, what needs the human, and its ledger row.

A human surface (Tinkery) renders it; an agent asked "what happened?" can read the same thing. It writes nothing.
Expected absences (no selection, no ledger, no row) are reported in the JSON, never as errors and never as zero.
"""

from datetime import date, datetime, timezone
import json
from pathlib import Path

from . import ledger
from .ledger import CHANGE_ID, MIN_CELL
from .sources import SourceError, parse_pr, read_record, snapshot

SCHEMA = 'tink-surface/1'
FIX = 'python3 -m tink_substrate init --replace --work <work record> --checkout <checkout>'


def selection(config_path):
    path = Path(config_path)
    if not path.is_file():
        return {'status': 'missing', 'config': str(path), 'error': None, 'fix': FIX}, None
    try:
        config = json.loads(path.read_text())
        if config.get('schema') != 1:
            raise SourceError('Unsupported configuration schema.')
        read_record(config['work'])
        if not Path(config['checkout']).is_dir():
            raise SourceError(f"The selected checkout {config['checkout']} is gone.")
    except (OSError, ValueError, KeyError) as error:
        return {'status': 'unavailable', 'config': str(path), 'error': str(error), 'fix': FIX}, None
    return {'status': 'ok', 'config': str(path), 'error': None, 'fix': None}, config


def change_id(checkout, run):
    """The change ID `prepare` stamped in the committed run record, if any."""
    try:
        value = json.loads((Path(checkout) / 'runs' / run / 'tools.json').read_text()).get('change')
    except (OSError, ValueError, AttributeError, TypeError):
        return None
    return value if isinstance(value, str) and CHANGE_ID.fullmatch(value) else None


def read_ledger(path):
    """Ledger lines, tolerating only a half-written last line (the daily update may be appending)."""
    lines = Path(path).read_text().splitlines()
    out = []
    for number, line in enumerate(lines, 1):
        if not line.strip():
            continue
        try:
            out.append(json.loads(line))
        except ValueError:
            if number == len(lines):
                break
            raise ValueError(f'ledger line {number} is not JSON') from None
    return out


def brief(record, artifacts):
    for group in artifacts:
        for document in group['documents']:
            if document['label'] in ('Seed contract', 'Brief') and document['status'] == 'ok':
                return {'status': 'ok', 'label': document['label'], 'relative_path': document['relative_path'],
                        'text': document['data']['text'], 'error': None}
    if record.get('body'):
        return {'status': 'ok', 'label': 'Record', 'relative_path': record.get('path'), 'text': record['body'],
                'error': None}
    return {'status': 'not-linked', 'label': None, 'relative_path': None, 'text': None, 'error': None}


def workflow(source):
    data = source.get('data')
    if source['status'] != 'ok' or not data:
        return {'status': source['status'], 'error': source.get('error') or source.get('reason'), 'data': None}
    checklist = data.get('checklist') or []
    return {'status': 'ok', 'error': None, 'data': {
        'format': data.get('format') or 'json', 'status_text': data.get('status_text'),
        'verification_status': data.get('verification_status'), 'next_action': data.get('next_action'),
        'gates': [{key: gate[key] for key in ('stage', 'status', 'blocked')} for gate in data.get('gates') or []],
        'decisions': [{'stage': d['stage'], 'decision': d['decision'], 'reviewer': d.get('reviewer')}
                      for d in data.get('decisions') or []],
        'checklist': {'total': len(checklist), 'passed': sum(item.get('status') == 'passed' for item in checklist)}}}


def pull_request(source, git):
    data = source.get('data')
    if source['status'] != 'ok' or not data:
        return {'status': source['status'], 'error': source.get('error') or source.get('reason'), 'data': None}
    head = (git.get('data') or {}).get('head') if git['status'] == 'ok' else None
    return {'status': 'ok', 'error': None, 'data': {
        'number': data.get('number'), 'state': data.get('state'), 'draft': data.get('isDraft'), 'ci': data.get('ci'),
        'review_decision': data.get('reviewDecision'), 'merged_at': data.get('mergedAt'),
        'head_matches_checkout': None if head is None else data.get('headRefOid') == head}}


def triage(attention, pr):
    """Split attention into what needs the human (consequential) and notes (everything else)."""
    state = (pr.get('data') or {}).get('state')
    open_pr, finished = state == 'OPEN', state in ('MERGED', 'CLOSED')
    needs, notes = [], []
    for text in attention:
        kind = ('source' if text.endswith('is unavailable. Its state is unknown.') or
                (text.startswith('The linked ') and text.endswith(' is unavailable.')) else
                # once the PR merged or closed, workflow gates are history, not a decision waiting
                'gate' if text.startswith(('tink-sdlc stage ', 'Local verification is ', 'tink-sdlc reports: '))
                and not finished else
                'ci' if text == 'PR checks: failed.' and open_pr else
                'review' if text.startswith('GitHub reports changes requested') else None)
        if kind:
            needs.append({'kind': kind, 'text': text})
        else:
            notes.append(text)
    return needs, notes


def ledger_view(path, change_key, stamped, today):
    view = {'status': 'ok', 'path': str(path), 'error': None, 'as_of': None, 'row': None, 'week': None}
    if not Path(path).is_file():
        return {**view, 'status': 'missing'}, change_key, None
    try:
        folded = ledger.fold(read_ledger(path))
    except (OSError, ValueError, KeyError) as error:
        return {**view, 'status': 'unavailable', 'error': str(error)}, change_key, None
    view['as_of'] = datetime.fromtimestamp(Path(path).stat().st_mtime, timezone.utc).isoformat()
    rows = {key: row for key, row in folded.items() if 'outcome' in row}
    by_id = [key for key, row in rows.items() if stamped and row.get('change_id') == stamped]
    link = 'none'
    if len(by_id) == 1:
        if change_key and by_id[0] != change_key:
            return {**view, 'status': 'unavailable',
                    'error': f'change ID and PR disagree: {stamped} is {by_id[0]}, the record names {change_key}'}, \
                change_key, None
        change_key, link = by_id[0], 'change_id'
    elif change_key:
        link = 'pr'
    if change_key in rows:
        row = rows[change_key]
        view['row'] = {key: row.get(key) for key in ('outcome', 'times', 'size', 'review', 'operator', 'cost', 'config')}
    unattributed = {key.split('/', 1)[1]: row['unattributed'] for key, row in folded.items() if row.get('unattributed')}
    year, number, _ = today.isocalendar()
    name = f'{year}-W{number:02d}'
    week = ledger.week_numbers(rows, unattributed).get(name)
    hours = (week or {}).get('hours', {})
    covered = len(week['covered']) if week else 0
    view['week'] = {
        'name': name, 'merged': len(week['merged']) if week else 0, 'useful': len(week['useful']) if week else 0,
        'covered': covered, 'operator_hours_c5': round(hours['c5'], 2) if 'c5' in hours else None,
        'useful_per_hour': {cap: None if value is None else round(value, 2)
                            for cap, value in ((week or {}).get('per_hour') or dict.fromkeys(('c2', 'c5', 'c10'))).items()},
        'suppressed': f'fewer than {MIN_CELL} changes with operator data' if covered < MIN_CELL else None}
    return view, change_key, link


def build(config_path, ledger_path=ledger.DEFAULT_LEDGER, today=None):
    today = date.fromisoformat(today) if isinstance(today, str) else today or date.today()
    chosen, config = selection(config_path)
    value = {'schema': SCHEMA, 'observed_at': datetime.now(timezone.utc).isoformat(),
             'limits': 'Read once; refresh before acting. Reading is not approval.',
             'selection': chosen, 'change': None, 'brief': None, 'workflow': None, 'pr': None,
             'needs_you': [], 'notes': []}
    stamped = change_key = None
    if config:
        snap = snapshot(config)
        record, sources = snap['record'], snap['sources']
        if record.get('pr'):
            repo, number = parse_pr(record['pr'])
            change_key = f'{repo}#{number}'
        stamped = change_id(config['checkout'], record['run']) if record.get('run') else None
        value['brief'] = brief(record, snap['artifacts'])
        value['workflow'] = workflow(sources['workflow'])
        value['pr'] = pull_request(sources['github'], sources['git'])
        value['needs_you'], value['notes'] = triage(snap['attention'], value['pr'])
        value['limits'] = snap['limits']
        value['change'] = {'title': record['title'], 'project': record['project'],
                           'next_action': record['next_action'], 'run': record.get('run'), 'pr': record.get('pr'),
                           'change_id': stamped, 'ledger_key': change_key, 'link': 'none'}
    value['ledger'], change_key, link = ledger_view(ledger_path, change_key, stamped, today)
    if value['change']:
        value['change']['ledger_key'], value['change']['link'] = change_key, link or 'none'
        p1 = ((value['ledger']['row'] or {}).get('review') or {}).get('p1')
        if p1 and (value['pr']['data'] or {}).get('state') == 'OPEN':
            value['needs_you'].append({'kind': 'p1', 'text': f'{p1} P1 review finding{"s" if p1 > 1 else ""} '
                                                             f'(ledger as of {value["ledger"]["as_of"]}).'})
    return value
