from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime, timedelta, timezone
import http.client
import io
import json
import threading
import unittest
from unittest.mock import patch

from tink_substrate.__main__ import main
from tink_substrate.server import make_server


class ServerTests(unittest.TestCase):
    def setUp(self):
        self.server = make_server({}, 0)
        self.addCleanup(self.server.server_close)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.addCleanup(self.server.shutdown)

    def get(self, path, headers=None):
        conn = http.client.HTTPConnection('127.0.0.1', self.server.server_port)
        self.addCleanup(conn.close)
        conn.request('GET', path, headers=headers or {})
        r = conn.getresponse()
        return r.status, r.read(), dict(r.getheaders())

    def test_page_and_agents_share_snapshot_until_explicit_refresh(self):
        with patch('tink_substrate.server.snapshot', side_effect=[{'schema':1,'n':1},{'schema':1,'n':2}]) as fetch:
            first = self.get('/api/snapshot')[1]
            second = self.get('/api/snapshot')[1]
            self.assertEqual(first, second)
            self.assertEqual(fetch.call_count, 1)
            third = json.loads(self.get('/api/snapshot?refresh=1')[1])
            self.assertEqual(third['n'], 2)

    def test_no_arbitrary_files_or_cross_site_reads(self):
        for path in ('/../README.md', '/%2e%2e/README.md', '/seed-contract.md'):
            self.assertEqual(self.get(path)[0], 404)
        self.assertEqual(self.get('/', {'Host':'evil.test'})[0], 403)
        self.assertEqual(self.get('/api/snapshot', {'Origin':'https://evil.test'})[0], 403)
        self.assertEqual(self.get('/api/snapshot', {'Sec-Fetch-Site':'cross-site'})[0], 403)

    def test_invalid_config_refresh_reports_error_not_old_success(self):
        with patch('tink_substrate.server.snapshot', side_effect=[{'schema':1}, ValueError('Bad record')]):
            self.assertEqual(self.get('/api/snapshot')[0], 200)
            code, body, _ = self.get('/api/snapshot?refresh=1')
            self.assertEqual(code, 503)
            self.assertIn(b'Bad record', body)

    def test_failed_refresh_stays_visible_to_later_readers(self):
        old = {'schema': 1, 'observed_at': '2026-10-03T10:00:00+00:00', 'attention': ['Earlier item.']}
        with patch('tink_substrate.server.snapshot', side_effect=[old, ValueError('Bad record'), {**old, 'attention': []}]):
            self.get('/api/snapshot')
            self.assertEqual(self.get('/api/snapshot?refresh=1')[0], 503)
            code, body, _ = self.get('/api/snapshot')
            value = json.loads(body)
            self.assertEqual(code, 200)
            self.assertEqual(value['refresh_failed']['error'], 'Bad record')
            self.assertIn('last refresh failed', value['attention'][0])
            self.assertEqual(value['attention'][1:], ['Earlier item.'])
            recovered = json.loads(self.get('/api/snapshot?refresh=1')[1])
            self.assertNotIn('refresh_failed', recovered)
            self.assertEqual(recovered['attention'], [])

    def test_agent_status_reports_age_and_server_errors(self):
        url = f'http://127.0.0.1:{self.server.server_port}'
        cached = {'schema': 1, 'observed_at': (datetime.now(timezone.utc) - timedelta(minutes=90)).isoformat(), 'attention': []}
        with patch('tink_substrate.server.snapshot', side_effect=[ValueError('Bad record'), cached]):
            err = io.StringIO()
            with redirect_stdout(io.StringIO()), redirect_stderr(err):
                self.assertEqual(main(['status', '--url', url + '/']), 1)
            self.assertIn('503', err.getvalue())
            self.assertIn('Bad record', err.getvalue())
            out, err = io.StringIO(), io.StringIO()
            with redirect_stdout(out), redirect_stderr(err):
                self.assertEqual(main(['status', '--url', url]), 0)
            self.assertEqual(json.loads(out.getvalue()), cached)
            self.assertIn('observed 90 min ago', err.getvalue())

    def test_security_headers_and_no_inline_scripts(self):
        code, body, headers = self.get('/')
        self.assertEqual(code, 200)
        self.assertIn("frame-ancestors 'none'", headers['Content-Security-Policy'])
        self.assertIn(b'/app.js', body)
        self.assertEqual(headers['Cache-Control'], 'no-store')
