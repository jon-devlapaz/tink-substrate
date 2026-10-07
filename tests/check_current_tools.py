"""Authenticated live compatibility probe. Explicitly run; not unittest discovery."""
import argparse
import json
from pathlib import Path
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tink_substrate.package import install
from tink_substrate.prepare import resolve_sources, fetch_sources, smoke_package, versions


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    sources = resolve_sources()
    with tempfile.TemporaryDirectory(prefix='substrate-live-check-') as directory:
        root = Path(directory)
        cache = root / 'sources'; cache.mkdir()
        fetch_sources(sources, cache)
        package = root / 'package'
        pins = {name: (spec['url'], spec['revision']) for name, spec in sources.items() if name != 'tink-substrate'}
        install(cache / 'tink-substrate', package, cache, pins=pins)
        result = {'components': versions(package, sources), 'compatibility': smoke_package(package),
                  'limits': 'Live source compatibility only. This does not exercise the candidate entry skill after merge.'}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2) + '\n')
    print(args.out)


if __name__ == '__main__':
    main()
