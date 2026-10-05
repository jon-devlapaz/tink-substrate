"""Configure one chosen work item, view it locally, or read its JSON snapshot."""

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import urllib.error
import urllib.request
from urllib.parse import urlsplit

from . import __version__
from .archive import archive_run
from .server import make_server
from .sources import SourceError, read_record, snapshot, git

DEFAULT_CONFIG = Path.home() / '.config/tink-substrate/config.json'


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--version', action='version', version=f'tink-substrate {__version__}')
    parser.add_argument('--config', type=Path, default=DEFAULT_CONFIG)
    commands = parser.add_subparsers(dest='command', required=True)
    init = commands.add_parser('init', help='select a work record and checkout')
    init.add_argument('--work', type=Path, required=True)
    init.add_argument('--checkout', type=Path, required=True)
    init.add_argument('--replace', action='store_true', help='replace an existing selection')
    init.add_argument('--trust-sdlc', action='store_true', help='allow the selected checkout to execute its SDLC status command')
    serve = commands.add_parser('serve', help='open the read-only local server')
    serve.add_argument('--port', type=int, default=7871)
    status = commands.add_parser('status', help='print an agent-readable JSON snapshot')
    status.add_argument('--url', help='read the exact snapshot currently shown by a running loopback server')
    archive = commands.add_parser('archive', help='save a committed run and source outside its checkout')
    archive.add_argument('--checkout', type=Path, required=True)
    archive.add_argument('--project', required=True)
    archive.add_argument('--run', required=True)
    archive.add_argument('--phase', choices=('delivery', 'closure'), required=True)
    archive.add_argument('--root', type=Path, default=Path.home() / '.local/share/tink-substrate/archive')
    args = parser.parse_args(argv)
    try:
        if args.command == 'archive':
            print(archive_run(args.checkout, args.project, args.run, args.phase, args.root))
            return 0
        if args.command == 'init':
            read_record(args.work)
            checkout = args.checkout.resolve()
            top = Path(git(checkout, 'rev-parse', '--show-toplevel').strip()).resolve()
            if top != checkout:
                raise SourceError('Select the checkout root, not a subdirectory.')
            config = {'schema': 1, 'work': str(args.work.resolve()), 'checkout': str(checkout), 'trust_sdlc': args.trust_sdlc}
            if args.config.exists() and not args.replace:
                raise SourceError('Configuration already exists. Use --replace to change the selection.')
            args.config.parent.mkdir(parents=True, exist_ok=True)
            temporary = args.config.with_suffix('.tmp')
            temporary.write_text(json.dumps(config, indent=2) + '\n')
            temporary.replace(args.config)
            print(f'Saved {args.config}. Next: python3 -m tink_substrate serve')
            print('If a server is already running, restart it to load this selection. Refresh does not switch selections.')
            return 0
        if args.command == 'status' and args.url:
            parsed = urlsplit(args.url)
            if parsed.scheme != 'http' or parsed.hostname not in ('localhost', '127.0.0.1') or parsed.username or parsed.password or parsed.query or parsed.fragment or parsed.path not in ('', '/'):
                raise SourceError('Use the loopback server origin, for example http://127.0.0.1:7871.')
            try:
                with urllib.request.urlopen(args.url.rstrip('/') + '/api/snapshot', timeout=25) as response:
                    value = json.load(response)
            except urllib.error.HTTPError as error:
                raise SourceError(f'Server answered {error.code}: ' + error.read().decode(errors='replace')[:400]) from None
            minutes = (datetime.now(timezone.utc) - datetime.fromisoformat(value['observed_at'])).total_seconds() // 60
            print(f"Cached snapshot observed {minutes:.0f} min ago ({value['observed_at']}). "
                  'Run status without --url for a fresh observation before acting.', file=sys.stderr)
        else:
            config = json.loads(args.config.read_text())
            if config.get('schema') != 1:
                raise SourceError('Unsupported configuration schema.')
            if args.command == 'serve':
                server = make_server(config, args.port)
                print(f'Tink substrate: http://127.0.0.1:{server.server_port}', flush=True)
                try:
                    server.serve_forever()
                except KeyboardInterrupt:
                    pass
                finally:
                    server.server_close()
                return 0
            value = snapshot(config)
        print(json.dumps(value, indent=2, ensure_ascii=False))
        return 0
    except (OSError, ValueError, KeyError) as error:
        print(json.dumps({'error': str(error)}), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
