#!/usr/bin/env python3
"""Check copied files against the installation receipt."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tink_substrate.package import check


if __name__ == '__main__':
    try:
        revision = check(Path(__file__).resolve().parents[1])
    except (OSError, ValueError, KeyError) as error:
        sys.exit(f'Incomplete or changed installation: {error}. Install a fresh copy outside the skills directory for review.')
    print(f'Installation matches source {revision}')
