#!/usr/bin/env python3
"""Install a complete, independent Substrate skill without replacing existing work."""
import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile

PINS = {
    'tink-skills': ('https://github.com/jon-devlapaz/tink-skills.git',
                    '58878b5794ca04a5ec0ba62027faadabfe7ca925'),
    'tink-sdlc': ('https://github.com/jon-devlapaz/tink-sdlc.git',
                  '3440e17960b780fa370889ad8f5876210827d7b3'),
}
# This repository's own SDLC workspace writes these blocks into AGENTS.md. They point
# at _system/, stages/ and _shared/, which the package does not contain.
WORKSPACE_BLOCKS = re.compile(r'\n*<!-- AI-Native SDLC Router -->.*?<!-- End AI-Native SDLC Router -->\n?'
                              r'|\n*<!-- tink:rules begin[^\n]*?-->.*?<!-- tink:rules end -->\n?', re.S)


def package_instructions(text):
    """Return AGENTS.md without the source workspace's router and compiled rules."""
    result = WORKSPACE_BLOCKS.sub('', text)
    if 'SDLC Router' in result or 'tink:rules' in result:
        raise ValueError('AGENTS.md has an unmatched SDLC router or tink:rules marker')
    return result.rstrip('\n') + '\n'


def export_tree(repo, revision, target, paths):
    data = subprocess.check_output(['git', '-C', str(repo), 'archive', revision, '--', *paths])
    with tarfile.open(fileobj=io.BytesIO(data)) as archive:
        for member in archive:
            path = Path(member.name)
            if path.is_absolute() or '..' in path.parts or not (member.isdir() or member.isfile()):
                raise ValueError(f'Unsupported dependency entry: {member.name}')
            output = target / path
            if member.isdir():
                output.mkdir(parents=True, exist_ok=True)
            else:
                output.parent.mkdir(parents=True, exist_ok=True)
                with archive.extractfile(member) as stream:
                    output.write_bytes(stream.read())
                output.chmod(member.mode & 0o777)



def install(source, destination, tool_cache=None):
    destination = destination.absolute()
    if destination.exists() or destination.is_symlink():
        raise ValueError(f'Destination already exists; left unchanged: {destination}')
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='substrate-install-') as temp:
        staging = Path(temp) / 'package'
        staging.mkdir()
        revision = subprocess.check_output(['git', '-C', str(source), 'rev-parse', 'HEAD'], text=True).strip()
        export_tree(source, revision, staging, [
            'tink_substrate', 'docs', 'LICENSE', 'AGENTS.md',
            'skills/tink-substrate/SKILL.md', 'scripts/check_install.py'])
        shutil.move(staging / 'skills/tink-substrate/SKILL.md', staging / 'SKILL.md')
        agents = staging / 'AGENTS.md'
        agents.write_text(package_instructions(agents.read_text()))
        shutil.rmtree(staging / 'skills')
        source_revision = revision
        for name, (url, revision) in PINS.items():
            repo = tool_cache / name if tool_cache else Path(temp) / name
            if not tool_cache:
                subprocess.run(['git', 'clone', '--quiet', '--no-checkout', url, str(repo)], check=True)
            # Export the pinned Git objects, never the cache's mutable working files.
            subprocess.run(['git', '-C', str(repo), 'cat-file', '-e', revision + '^{commit}'], check=True)
            paths = ['skills/seed-me', 'LICENSE'] if name == 'tink-skills' else ['.']
            export_tree(repo, revision, staging / '.substrate-tools' / name, paths)
        hashes = {str(p.relative_to(staging)): hashlib.sha256(p.read_bytes()).hexdigest()
                  for p in sorted(staging.rglob('*')) if p.is_file()}
        (staging / 'installation.json').write_text(json.dumps({
            'schema': 1, 'source': {'revision': source_revision}, 'dependencies': {name: {'url': url, 'revision': rev}
                                          for name, (url, rev) in PINS.items()},
            'files': hashes,
        }, indent=2) + '\n')
        # Reserve the final name exclusively; a competing install cannot be replaced.
        destination.mkdir()
        try:
            for item in staging.iterdir():
                if item.name != 'installation.json':
                    shutil.move(str(item), destination / item.name)
            shutil.move(staging / 'installation.json', destination / 'installation.json')
        except BaseException:
            shutil.rmtree(destination)
            raise
    return destination


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--destination', type=Path, default=Path(os.environ.get(
        'CODEX_HOME', str(Path.home() / '.codex'))) / 'skills/tink-substrate')
    parser.add_argument('--tool-cache', type=Path, help='Offline Git clones containing the pinned commits')
    args = parser.parse_args()
    if sys.version_info < (3, 11):
        parser.error('Python 3.11 or newer is required')
    try:
        result = install(Path(__file__).resolve().parents[1], args.destination, args.tool_cache)
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        parser.exit(1, f'Installation failed: {error}\n')
    print(f'Installed: {result}\nOpen a new agent session and use $tink-substrate.')


if __name__ == '__main__':
    main()
