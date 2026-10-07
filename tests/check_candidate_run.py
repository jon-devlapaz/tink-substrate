"""Exercise a committed candidate with real checked dependencies, without approval."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tink_substrate.prepare import prepare_run, resolve_sources, fetch_sources, basic_environment, command


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    source = Path(__file__).resolve().parents[1]
    revision = command(['git', '-C', source, 'rev-parse', 'HEAD']).strip()
    selected = resolve_sources()
    # Only this explicit test selects local candidate code. Production never bypasses CI.
    selected['tink-substrate'].update(revision=revision, ci_run=None, candidate=True)
    with tempfile.TemporaryDirectory(prefix='substrate-candidate-run-') as directory:
        root = Path(directory)
        cache = root / 'sources'; cache.mkdir()
        dependencies = {name: spec for name, spec in selected.items() if name != 'tink-substrate'}
        fetch_sources(dependencies, cache)
        command(['git', 'clone', '--quiet', '--no-checkout', source, cache / 'tink-substrate'])
        target = root / 'target'; target.mkdir()
        command(['git', 'init', '-q', target])
        command(['git', '-C', target, '-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid',
                 'commit', '--allow-empty', '-qm', 'synthetic target'])
        with patch('tink_substrate.prepare.resolve_sources', return_value=selected), \
             patch('tink_substrate.prepare.fetch_sources', return_value=cache):
            record = prepare_run(target, 'trial', root / 'packages')
        package = Path(record['package'])
        with basic_environment() as env:
            resumed = json.loads(command([sys.executable, '-B', '-m', 'tink_substrate', 'prepare',
                                          '--checkout', target, '--run', 'trial'], cwd=package, env=env))
            assert resumed == record
            opened = command([sys.executable, '-B', '-m', 'tink_substrate', 'workflow', '--checkout', target,
                              '--run', 'trial', '--', 'stage', 'trial', '1'], cwd=package, env=env)
            assert 'Prepared stage session prompt' in opened and str(package) in opened
            state = json.loads(command([sys.executable, '-B', '-m', 'tink_substrate', 'workflow',
                                        '--checkout', target, '--run', 'trial', '--', 'status', 'trial', '--json'],
                                       cwd=package, env=env))
            assert state['run']['verification_status'] == 'blocked'
        result = {'candidate': revision, 'components': record['components'], 'compatibility': record['compatibility'],
                  'checks': ['real-sdlc-1.21-install', 'copied-cli-offline-resume', 'real-stage-1-with-saved-prompt',
                             'copied-cli-blocked-status'],
                  'limits': 'Synthetic target; candidate source selected explicitly for this probe; no CI bypass in production, human approval or feature delivery.'}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2) + '\n')
    print(args.out)


if __name__ == '__main__':
    main()
