"""Refresh bundled sources at a new-run boundary; keep resumes offline and fixed."""
import contextlib
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import shlex
import subprocess
import sys
import tempfile
import uuid

from .package import install, check

SOURCES = {
    'tink-substrate': {'url': 'https://github.com/jon-devlapaz/tink-substrate.git', 'workflow': 'ci.yml'},
    'tink-skills': {'url': 'https://github.com/jon-devlapaz/tink-skills.git', 'workflow': 'validate.yml'},
    'tink-sdlc': {'url': 'https://github.com/jon-devlapaz/tink-sdlc.git', 'workflow': 'validate.yml'},
}
DEFAULT_PACKAGES = Path.home() / '.local/share/tink-substrate/packages'


def command(argv, cwd=None, env=None, timeout=120):
    try:
        result = subprocess.run([str(a) for a in argv], cwd=cwd, env=env, timeout=timeout,
                                capture_output=True, text=True)
    except (OSError, subprocess.TimeoutExpired) as error:
        raise ValueError(f'{argv[0]} could not complete: {error}') from None
    if result.returncode:
        raise ValueError(f'{Path(str(argv[0])).name} failed: {(result.stderr or result.stdout).strip()[:1200]}')
    return result.stdout


def git(root, *args):
    return command(['git', '--no-optional-locks', '-c', 'core.fsmonitor=false', '-C', root, *args]).strip()


def github(endpoint):
    return json.loads(command(['gh', 'api', endpoint], timeout=30))


def resolve_sources():
    selected = {}
    for name, spec in SOURCES.items():
        repo = f'jon-devlapaz/{name}'
        sha = github(f'repos/{repo}/commits/main').get('sha')
        if not isinstance(sha, str) or not re.fullmatch('[0-9a-f]{40}', sha):
            raise ValueError(f'{name}: invalid main commit')
        value = github(f'repos/{repo}/actions/workflows/{spec["workflow"]}/runs?branch=main&head_sha={sha}&event=push&per_page=100')
        runs = value.get('workflow_runs')
        if not isinstance(runs, list):
            raise ValueError(f'{name}: malformed CI response')
        matches = [r for r in runs if isinstance(r, dict) and r.get('head_sha') == sha
                   and r.get('head_branch') == 'main' and r.get('event') == 'push']
        if not matches or any(type(r.get('id')) is not int for r in matches):
            raise ValueError(f'{name}: no valid CI evidence for current main {sha}')
        latest = max(matches, key=lambda r: r['id'])
        if latest.get('status') != 'completed' or latest.get('conclusion') != 'success':
            raise ValueError(f'{name}: current main {sha} CI is {latest.get("status")}/{latest.get("conclusion")}')
        selected[name] = {**spec, 'revision': sha, 'ci_run': latest['id']}
    return selected


def fetch_sources(sources, destination):
    for name, spec in sources.items():
        repo = destination / name
        repo.mkdir()
        git(repo, 'init', '-q')
        git(repo, 'remote', 'add', 'origin', spec['url'])
        git(repo, 'fetch', '--quiet', '--depth=1', 'origin', spec['revision'])
        git(repo, 'checkout', '--quiet', '--detach', spec['revision'])
        if git(repo, 'rev-parse', 'HEAD') != spec['revision']:
            raise ValueError(f'{name}: fetched commit differs from selected main')
    return destination


@contextlib.contextmanager
def basic_environment():
    """No global Tink/router can leak into the bundled-only run."""
    with tempfile.TemporaryDirectory(prefix='substrate-path-') as temporary:
        for name in ('git', 'bash', 'python3'):
            executable = sys.executable if name == 'python3' else shutil.which(name)
            if not executable:
                raise ValueError(f'{name} is required')
            (Path(temporary) / name).symlink_to(Path(executable).resolve())
        env = {**os.environ, 'PATH': temporary, 'PYTHONDONTWRITEBYTECODE': '1',
               'GIT_TERMINAL_PROMPT': '0'}
        yield env


def smoke_package(package):
    """Execute the exported combination in a disposable project without approvals."""
    check(package)
    tools = package / '.substrate-tools'
    with tempfile.TemporaryDirectory(prefix='substrate-smoke-') as directory, basic_environment() as env:
        target = Path(directory) / 'project'
        target.mkdir()
        command(['git', 'init', '-q', target], env=env)
        command(['git', '-C', target, '-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid',
                 'commit', '--allow-empty', '-qm', 'synthetic compatibility fixture'], env=env)
        helper = tools / 'tink-skills/skills/seed-me/scripts/session.py'
        session = json.loads(command([sys.executable, '-B', helper, 'init', '--root',
                                      Path(directory) / 'seed-sessions', '--operator', 'simulated'], env=env))
        ledger = json.loads(command([sys.executable, '-B', helper, 'read', session['session']], env=env))
        if ledger.get('status') != 'active' or ledger.get('operator') != 'simulated':
            raise ValueError('Bundled Seed Me did not preserve simulated session authority')
        command([sys.executable, '-B', helper, 'end', session['session'], '--status', 'stopped',
                 '--reason', 'Synthetic compatibility check only'], env=env)
        command([sys.executable, '-B', tools / 'tink-sdlc/scripts/init.py', target], env=env)
        runtime = target / '_system/scripts/sdlc.py'
        capabilities = json.loads(command([sys.executable, '-B', runtime, 'capabilities', '--json'], env=env))
        if (capabilities.get('protocol') != 'tink-sdlc' or type(capabilities.get('api_version')) is not int
                or capabilities.get('api_version') != 1):
            raise ValueError('Bundled SDLC does not supply supported API 1')
        command([sys.executable, '-B', runtime, 'new', 'smoke', '--profile', 'light', '--kind', 'feature'], env=env)
        record = Path(directory) / 'work.md'
        record.write_text('+++\nschema = 1\ntitle = "Synthetic compatibility check"\nproject = "smoke"\nowner = "test"\nnext_action = "human review"\nrun = "smoke"\n+++\nFixture only.\n')
        config = Path(directory) / 'config.json'
        config.write_text(json.dumps({'schema': 1, 'work': str(record), 'checkout': str(target), 'trust_sdlc': True}))
        snapshot = json.loads(command([sys.executable, '-B', '-m', 'tink_substrate', '--config', config, 'status'], cwd=package, env=env))
        source = snapshot['sources']['workflow']
        if source['status'] != 'ok' or source['data'].get('verification_status') != 'blocked':
            raise ValueError('Bundled dashboard did not report the unapproved SDLC run as blocked')
        refused = subprocess.run([sys.executable, '-B', runtime, 'verify', 'smoke'], env=env,
                                 capture_output=True, text=True, timeout=30)
        if refused.returncode == 0:
            raise ValueError('Bundled SDLC accepted verification without human approval')
        return {'result': 'passed', 'checks': ['seed-simulated-session', 'sdlc-api-1', 'dashboard-unapproved-run', 'unapproved-verify-refused'],
                'limits': 'Synthetic compatibility check; no interview or feature delivery.'}


def versions(package, sources):
    selected = {name: dict(value) for name, value in sources.items()}
    seed = (package / '.substrate-tools/tink-skills/skills/seed-me/SKILL.md').read_text()
    match = re.search(r'^\s+version:\s*["\']?([0-9]+\.[0-9]+\.[0-9]+)', seed, re.MULTILINE)
    if not match:
        raise ValueError('Seed Me version missing')
    selected['tink-skills']['version'] = match[1]
    selected['tink-sdlc']['version'] = json.loads((package / '.substrate-tools/tink-sdlc/assets/manifest.json').read_text())['version']
    source = (package / 'tink_substrate/__init__.py').read_text()
    match = re.search(r'__version__\s*=\s*["\']([^"\']+)', source)
    if not match:
        raise ValueError('Substrate version missing')
    selected['tink-substrate']['version'] = match[1]
    return selected


def workflow_digest(checkout):
    receipt = checkout / '_system/scaffold.json'
    value = json.loads(receipt.read_text())
    owned = set(value.get('projectOwned', [])) | {'_system/verification.json'}
    paths = ['_system/scaffold.json', *(name for name in value['files'] if name not in owned)]
    hashes = {}
    for name in paths:
        path = checkout / name
        if Path(name).is_absolute() or '..' in Path(name).parts or path.is_symlink() or not path.resolve().is_relative_to(checkout):
            raise ValueError('Unsafe workflow path')
        hashes[name] = hashlib.sha256(path.read_bytes()).hexdigest()
    return hashlib.sha256(json.dumps(hashes, sort_keys=True).encode()).hexdigest()


def local_records(checkout):
    """Machine-specific bindings live in this checkout's Git directory, never in commits."""
    return Path(git(checkout, 'rev-parse', '--absolute-git-dir')) / 'substrate-runs'


def portable(record):
    """The committed run evidence: versions and checks, without machine paths."""
    return {key: record[key] for key in ('schema', 'run', 'components', 'integrations', 'checked_at', 'compatibility')}


def validate_record(checkout, run, record):
    if (record.get('schema') != 1 or record.get('checkout') != str(checkout)
            or record.get('run') != run or record.get('integrations') != 'bundled-only'):
        raise ValueError('Run tools identity does not match this checkout and run')
    package = Path(record['package'])
    if not package.is_absolute() or package.is_symlink() or package.resolve().is_relative_to(checkout):
        raise ValueError('Invalid run package path')
    check(package)
    installation = json.loads((package / 'installation.json').read_text())
    for name, spec in SOURCES.items():
        component = record['components'][name]
        actual = installation['source']['revision'] if name == 'tink-substrate' else installation['dependencies'][name]['revision']
        if component['url'] != spec['url'] or component['revision'] != actual:
            raise ValueError('Run component identity does not match installation')
    committed = checkout / 'runs' / run / 'tools.json'
    if committed.is_symlink() or not committed.is_file() or json.loads(committed.read_text()) != portable(record):
        raise ValueError('Committed runs/<run>/tools.json does not match this checkout\'s run tools identity')
    if workflow_digest(checkout) != record['workflow_digest']:
        raise ValueError('Run workflow changed; restore its saved scaffold before resuming')
    return record


def load_record(checkout, run):
    path = local_records(checkout) / f'{run}.json'
    if path.is_symlink():
        raise ValueError('Run tools record must not be a symlink')
    if not path.is_file():
        return None
    return validate_record(checkout, run, json.loads(path.read_text()))


@contextlib.contextmanager
def preparation_lock(checkout):
    directory = Path(git(checkout, 'rev-parse', '--absolute-git-dir'))
    fd = os.open(directory / 'substrate-prepare.lock', os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'a+b') as stream:
        try:
            fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise ValueError('Another preparation owns this checkout') from None
        yield


def prepare_run(checkout, run, packages=DEFAULT_PACKAGES, profile='light', kind='feature', upgrade_sdlc=False):
    checkout = Path(checkout).resolve()
    if not re.fullmatch('[a-z0-9][a-z0-9-]{0,79}', run):
        raise ValueError('Invalid run name')
    if profile not in ('light', 'full') or kind not in ('feature', 'bug'):
        raise ValueError('Unsupported run profile or kind')
    if Path(git(checkout, 'rev-parse', '--show-toplevel')).resolve() != checkout:
        raise ValueError('Select the checkout root')
    packages = Path(packages).absolute()
    if packages.resolve().is_relative_to(checkout):
        raise ValueError('Package storage must be outside the target checkout')
    with preparation_lock(checkout):
        path = checkout / 'runs' / run
        if path.is_symlink() or (checkout / 'runs').is_symlink():
            raise ValueError('Run paths must not be symlinks')
        record = load_record(checkout, run)
        if record:
            return record
        if path.exists():
            raise ValueError('This run was not prepared in this checkout; resume it where it was prepared, '
                             'or continue under its existing contracts')
        records = local_records(checkout)
        if records.is_dir() and any(records.glob('*.json')):
            raise ValueError('This checkout holds another prepared run; select another isolated checkout')
        if git(checkout, 'status', '--porcelain', '--untracked-files=all'):
            raise ValueError('New-run preparation needs a clean isolated checkout')
        verification = checkout / '_system/verification.json'
        if verification.exists() and json.loads(verification.read_text()).get('require_tink'):
            raise ValueError('This target requires Tink; bundled-only preparation cannot satisfy that policy')
        sources = resolve_sources()
        package = packages / uuid.uuid4().hex
        try:
            with tempfile.TemporaryDirectory(prefix='substrate-fetch-') as directory:
                cache = fetch_sources(sources, Path(directory))
                pins = {name: (spec['url'], spec['revision']) for name, spec in sources.items() if name != 'tink-substrate'}
                install(cache / 'tink-substrate', package, cache, pins=pins)
            smoke = smoke_package(package)
            components = versions(package, sources)
            current = resolve_sources()
            if any(current[name]['revision'] != value['revision'] for name, value in sources.items()):
                raise ValueError('Upstream main changed during preparation; retry before starting the run')
            initializer = package / '.substrate-tools/tink-sdlc/scripts/init.py'
            scaffold = checkout / '_system/scaffold.json'
            installed = json.loads(scaffold.read_text()).get('version') if scaffold.exists() else None
            bundled = components['tink-sdlc']['version']
            if installed and installed != bundled and not upgrade_sdlc:
                raise ValueError(f'Target has tink-sdlc {installed}; this run would use {bundled}. '
                                 'Upgrade only when the user asks: rerun with --upgrade-sdlc')
            with basic_environment() as env:
                upgrade = ['--upgrade'] if installed else []
                command([sys.executable, '-B', initializer, checkout, *upgrade, '--check'], env=env)
                if installed != bundled:
                    command([sys.executable, '-B', initializer, checkout, *upgrade], env=env)
                command([sys.executable, '-B', checkout / '_system/scripts/sdlc.py', 'new', run,
                         '--profile', profile, '--kind', kind], env=env)
        except BaseException:
            # Only an unprepared target can reach here; keep it, discard the unused package.
            if package.exists() and not path.exists():
                shutil.rmtree(package)
            raise
        record = {'schema': 1, 'checkout': str(checkout), 'run': run, 'package': str(package),
                  'components': components, 'integrations': 'bundled-only',
                  'checked_at': datetime.now(timezone.utc).isoformat(), 'compatibility': smoke,
                  'workflow_digest': workflow_digest(checkout)}
        (path / 'tools.json').write_text(json.dumps(portable(record), indent=2) + '\n')
        records.mkdir(exist_ok=True)
        # A crash before this final local record cannot be mistaken for a prepared run.
        temporary = records / f'.{run}.json.tmp'
        temporary.write_text(json.dumps(record, indent=2) + '\n')
        temporary.replace(records / f'{run}.json')
        return record


def workflow(checkout, run, arguments):
    checkout = Path(checkout).resolve()
    if not re.fullmatch('[a-z0-9][a-z0-9-]{0,79}', run):
        raise ValueError('Invalid run name')
    record = load_record(checkout, run)
    if not record:
        raise ValueError('This run has no tools record in this checkout; use prepare for new runs')
    commands = {'status', 'capabilities', 'verify', 'mark', 'decide', 'stage', 'pull', 'walk', 'lock-tests'}
    if not arguments or arguments[0] not in commands:
        raise ValueError('Use prepare for new runs; optional global integrations are disabled')
    if arguments[0] not in ('capabilities', 'walk') and (len(arguments) < 2 or arguments[1] != run):
        raise ValueError('Workflow commands must name this recorded run')
    arguments = list(arguments)
    if arguments[0] == 'stage':
        if any(value == '--worktree' or value.startswith('--worktree=') for value in arguments):
            raise ValueError('Stages use the prepared checkout; select a separate checkout before preparation')
        if '--here' not in arguments:
            arguments.append('--here')
    configuration = json.loads((checkout / '_system/verification.json').read_text())
    if configuration.get('require_tink'):
        raise ValueError('This target requires Tink; bundled-only workflow cannot satisfy that policy')
    # Disable only the runtime's optional discovery. Project checks retain PATH.
    launcher = ("import runpy,shutil,sys; original=shutil.which; "
                "shutil.which=lambda name,*a,**k: None if name in ('tink','tink-route') else original(name,*a,**k); "
                "sys.argv=sys.argv[1:]; runpy.run_path(sys.argv[0],run_name='__main__')")
    env = {**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'}
    result = subprocess.call([sys.executable, '-B', '-c', launcher,
                              str(checkout / '_system/scripts/sdlc.py'), *arguments], cwd=checkout, env=env)
    if result == 0 and arguments[0] == 'stage' and '--check' not in arguments:
        package = Path(record['package'])
        prefix = shlex.join([sys.executable, '-B', '-m', 'tink_substrate', 'workflow',
                             '--checkout', str(checkout), '--run', run, '--'])
        print(f'Prepared stage session prompt (start a new session in {checkout}):', flush=True)
        print(f'Perform stage {arguments[2]} for run {run}. Read its stages/ CONTEXT.md, '
              f'{checkout}/runs/{run}/handoff.md, {checkout}/runs/{run}/tools.json, and {package}/docs/automatic-tools.md. '
              f'Use {package} as the package directory and run SDLC commands through {prefix}. '
              'This run is bundled-only; optional global Tink and tink-route are disabled. '
              'Use the stage outputs and human gates; preparation is not approval.', flush=True)
    return result
