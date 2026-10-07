#!/usr/bin/env python3
"""Install a reproducible pinned package; prepare refreshes tools for new runs."""
import argparse
import os
from pathlib import Path
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tink_substrate.package import PINS, install as build_package


def install(source, destination, tool_cache=None):
    return build_package(source, destination, tool_cache, pins=PINS)

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
    print(f'Installed: {result}\nOpen a new agent session and ask it to use tink-substrate.')


if __name__ == '__main__':
    main()
