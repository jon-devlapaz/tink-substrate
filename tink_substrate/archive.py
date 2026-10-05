"""Save a committed run independently without changing its checkout."""

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import uuid


def checksum(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def archive_run(checkout, project, run, phase, root):
    for name in (project, run):
        if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]*', name):
            raise ValueError('Project and run must be simple names, without path separators.')
    if phase not in ('delivery', 'closure'):
        raise ValueError('Phase must be delivery or closure.')
    checkout = Path(checkout).resolve()
    root = Path(root).expanduser().resolve()
    if root == checkout or checkout in root.parents:
        raise ValueError('Save archives outside the target checkout.')

    def git(*args):
        result = subprocess.run(['git', '-c', 'core.fsmonitor=false', '-C', str(checkout), *args],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
        if result.returncode:
            raise ValueError(result.stderr.decode(errors='replace').strip())
        return result.stdout

    if Path(git('rev-parse', '--show-toplevel').decode().strip()).resolve() != checkout:
        raise ValueError('Select the checkout root.')
    head = git('rev-parse', 'HEAD').decode().strip()
    if git('status', '--porcelain', '--untracked-files=all'):
        raise ValueError('Checkout has uncommitted files. Commit the intended evidence first; preserve unrelated work.')
    prefix = f'runs/{run}/'
    entries = []
    for entry in git('ls-tree', '-r', '-z', head, '--', prefix).split(b'\0'):
        if not entry:
            continue
        fields, path = entry.split(b'\t', 1)
        mode, kind, oid = fields.decode().split()
        path = path.decode('utf-8')
        if mode not in ('100644', '100755') or kind != 'blob':
            raise ValueError(f'Run contains a link or unsupported entry: {path}')
        entries.append((path, oid))
    required = prefix + ('retro.md' if phase == 'delivery' else 'closure.md')
    if required not in [path for path, _ in entries] or not git('show', f'{head}:{required}').strip():
        raise ValueError(f'Commit a nonempty {required} before archiving.')
    parent = root / project / run
    parent.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H%M%S.%fZ')
    destination = parent / f'{stamp}-{phase}-{uuid.uuid4().hex[:8]}'
    temporary = Path(tempfile.mkdtemp(prefix='.saving-', dir=parent))
    try:
        with (temporary / 'source.tar').open('wb') as output:
            result = subprocess.run(['git', '-C', str(checkout), 'archive', '--format=tar', head],
                                    stdout=output, stderr=subprocess.PIPE, check=False)
        if result.returncode:
            raise ValueError(result.stderr.decode(errors='replace').strip())
        for path, oid in entries:
            target = temporary / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(git('cat-file', 'blob', oid))
        metadata = {'schema': 1, 'project': project, 'run': run, 'phase': phase,
                    'head': head, 'checkout': str(checkout), 'saved_at': stamp,
                    'limits': 'Committed source and run files only. No ignored files, conversation history, live forge checks or approval inferred.'}
        (temporary / 'metadata.json').write_text(json.dumps(metadata, indent=2) + '\n')
        files = sorted(p for p in temporary.rglob('*') if p.is_file())
        checksums = [(checksum(p), p.relative_to(temporary)) for p in files]
        (temporary / 'SHA256SUMS').write_text(''.join(f'{digest}  {path}\n' for digest, path in checksums))
        for digest, path in checksums:
            if checksum(temporary / path) != digest:
                raise ValueError(f'Archive checksum failed: {path}')
        if git('rev-parse', 'HEAD').decode().strip() != head or git('status', '--porcelain', '--untracked-files=all'):
            raise ValueError('Checkout changed during archiving; retry after its writer finishes.')
        temporary.rename(destination)
        return destination
    finally:
        if temporary.exists():
            shutil.rmtree(temporary)
