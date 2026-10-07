#!/usr/bin/env python3
"""Install a complete, independent Substrate skill without replacing existing work."""
import hashlib
import io
import json
import os
import re
from pathlib import Path
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



def install(source, destination, tool_cache=None, pins=None):
    pins = PINS if pins is None else pins
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
        for name, (url, revision) in pins.items():
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
                                          for name, (url, rev) in pins.items()},
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


def check(root):
    receipt = json.loads((root / 'installation.json').read_text())
    if receipt.get('schema') != 1 or not receipt.get('files'):
        raise ValueError('Unsupported or empty installation receipt')
    if any(path.is_symlink() for path in root.rglob('*')):
        raise ValueError('Installed package contains a symlink')
    actual = {str(path.relative_to(root)) for path in root.rglob('*') if path.is_file()}
    expected = set(receipt['files']) | {'installation.json'}
    if actual - expected:
        raise ValueError('Installed package contains unrecorded files: ' + ', '.join(sorted(actual - expected)))
    for name, digest in receipt['files'].items():
        path = root / name
        if Path(name).is_absolute() or '..' in Path(name).parts or path.resolve().is_relative_to(root.resolve()) is False:
            raise ValueError(f'Invalid installation path: {name}')
        if path.is_symlink() or any(parent.is_symlink() for parent in path.parents if parent != root and parent.is_relative_to(root)):
            raise ValueError(f'Installed path is a symlink: {name}')
        if hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            raise ValueError(f'Installed file changed: {name}')
    return receipt['source']['revision']

