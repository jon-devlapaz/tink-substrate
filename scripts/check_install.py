#!/usr/bin/env python3
"""Check the copied installation before using its tools."""
import hashlib
import json
from pathlib import Path
import sys


def check(root):
    receipt = json.loads((root / 'installation.json').read_text())
    if receipt.get('schema') != 1 or not receipt.get('files'):
        raise ValueError('Unsupported or empty installation receipt')
    for name, digest in receipt['files'].items():
        path = root / name
        if Path(name).is_absolute() or '..' in Path(name).parts or path.resolve().is_relative_to(root.resolve()) is False:
            raise ValueError(f'Invalid installation path: {name}')
        if hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            raise ValueError(f'Installed file changed: {name}')
    return receipt['source']['revision']


if __name__ == '__main__':
    try:
        revision = check(Path(__file__).resolve().parents[1])
    except (OSError, ValueError, KeyError) as error:
        sys.exit(f'Incomplete or changed installation: {error}. Install a fresh copy outside the skills directory for review.')
    print(f'Installation matches source {revision}')
