"""Keep the ledger current with one command, run daily, so nobody has to remember.

`ledger update` reads the repositories from a config file, keeps a private compressed copy of every harness
transcript (harnesses delete old ones), sweeps GitHub for what changed since the last run, then re-reads sessions.
`ledger schedule` installs a daily macOS LaunchAgent that runs it from the installed package.
"""

from datetime import datetime, timedelta, timezone
import gzip
import json
import os
from pathlib import Path
import plistlib
import shutil
import subprocess
import sys
import tempfile

from . import ledger, sessions

HOME = Path.home()
DEFAULT_CONFIG = HOME / '.config/tink-substrate/ledger.json'
DEFAULT_HOME = ledger.DEFAULT_LEDGER.parent
LABEL = 'ai.tink-substrate.ledger-update'
MARGIN = timedelta(days=1)  # re-read a day of overlap so a PR updated mid-sweep is never missed


def private_dir(path):
    path.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(path, 0o700)
    return path


def mirror(live, root):
    """Copy each transcript that is new or changed to root/<harness>/<path>.gz (mode 600). Returns how many."""
    copied = 0
    for harness, directory in live.items():
        directory = Path(directory)
        if not directory.is_dir():
            continue
        for source in directory.rglob('*.jsonl'):
            if source.name.startswith('._'):
                continue
            target = root / harness / source.relative_to(directory).parent / (source.name + '.gz')
            info = source.stat()
            if target.exists() and target.stat().st_mtime_ns == info.st_mtime_ns:
                continue
            folder = private_dir(target.parent)
            for parent in target.parents:  # every level of the copy stays private
                if parent == root.parent:
                    break
                os.chmod(parent, 0o700)
            descriptor, temporary = tempfile.mkstemp(dir=folder, prefix='.', suffix='.gz')
            with os.fdopen(descriptor, 'wb') as raw, gzip.GzipFile(fileobj=raw, mode='wb', mtime=0) as out, \
                    source.open('rb') as data:
                shutil.copyfileobj(data, out)
            os.chmod(temporary, 0o600)
            os.utime(temporary, ns=(info.st_atime_ns, info.st_mtime_ns))
            os.replace(temporary, target)
            copied += 1
    return copied


def read_config(path):
    path = Path(path)
    if not path.is_file():
        raise ValueError(f'No ledger config at {path}. Write {{"repos": {{"owner/name": "/path/to/clone"}}}} '
                         'listing each repository to measure.')
    repos = json.loads(path.read_text()).get('repos') or {}
    if not repos:
        raise ValueError(f'{path} lists no repos')
    return [(name, Path(clone).expanduser()) for name, clone in sorted(repos.items())]


def update(config=DEFAULT_CONFIG, home=DEFAULT_HOME, live=None):
    """Mirror transcripts, sweep GitHub incrementally, re-read sessions. Each step reports on its own."""
    repos = read_config(config)
    home = private_dir(Path(home))
    live = live or sessions.DEFAULT_DIRS
    ledger_path = home / 'changes.jsonl'
    state_path = home / 'state.json'
    state = json.loads(state_path.read_text()) if state_path.is_file() else {}
    swept = state.setdefault('swept', {})
    result = {'at': datetime.now(timezone.utc).isoformat(), 'ok': True}

    try:
        result['mirrored'] = mirror(live, home / 'mirror')
    except OSError as error:
        result['ok'], result['mirrored'] = False, {'error': str(error)}

    started = datetime.now(timezone.utc)
    since = {name: datetime.fromisoformat(swept[name]) - MARGIN for name, _ in repos if name in swept}
    try:
        result['github'] = {'added': ledger.sweep(ledger_path, repos, since=since)}
        swept.update({name: started.isoformat() for name, _ in repos})
    except (OSError, ValueError, KeyError) as error:
        result['ok'], result['github'] = False, {'error': str(error)}

    try:
        result['sessions'] = sessions.sweep(ledger_path, claude=live.get('claude'), codex=live.get('codex'),
                                            pi=live.get('pi'), snapshots=home / 'transcripts', mirror=home / 'mirror')
    except (OSError, ValueError, KeyError) as error:
        result['ok'], result['sessions'] = False, {'error': str(error)}

    temporary = state_path.with_name('.state.json.tmp')
    temporary.write_text(json.dumps(state, indent=2) + '\n')
    temporary.replace(state_path)
    return result


def launchctl(argv):
    completed = subprocess.run(argv, capture_output=True, text=True)
    if completed.returncode and argv[1] == 'bootstrap':
        raise ValueError(f'launchctl bootstrap failed: {completed.stderr.strip()}')
    return completed


def schedule(agents=HOME / 'Library/LaunchAgents', package=None, python=None, hour=6, home=DEFAULT_HOME,
             run=launchctl):
    """Install (or replace) a LaunchAgent that runs `ledger update` daily from the installed package."""
    package = Path(package or Path(__file__).resolve().parents[1])
    if not (package / 'tink_substrate').is_dir():
        raise ValueError(f'{package} does not contain the tink_substrate package; pass the installed skill directory')
    agents = Path(agents)
    agents.mkdir(parents=True, exist_ok=True)
    log = Path(home) / 'update.log'
    plist = {
        'Label': LABEL,
        'ProgramArguments': [python or os.path.realpath(sys.executable), '-B', '-m', 'tink_substrate', 'ledger', 'update'],
        'WorkingDirectory': str(package),
        'StartCalendarInterval': {'Hour': hour, 'Minute': 0},
        'EnvironmentVariables': {'PATH': '/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin', 'HOME': str(HOME)},
        'StandardOutPath': str(log),
        'StandardErrorPath': str(log),
    }
    path = agents / f'{LABEL}.plist'
    path.write_bytes(plistlib.dumps(plist))
    domain = f'gui/{os.getuid()}'
    run(['launchctl', 'bootout', f'{domain}/{LABEL}'])  # replacing an earlier schedule; absent is fine
    run(['launchctl', 'bootstrap', domain, str(path)])
    return path
