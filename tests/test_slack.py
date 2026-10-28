import contextlib
import importlib.util
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

HELPER = Path(__file__).resolve().parents[1] / 'scripts' / 'slack.py'


class HelperTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not HELPER.exists():
            raise AssertionError('The portable helper is not implemented')
        spec = importlib.util.spec_from_file_location('slack_helper', HELPER)
        cls.helper = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.helper)

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.state = Path(self.tmp.name) / 'seen.txt'

    def poll(self, messages, *, threads=None):
        calls = []
        def api(method, **args):
            calls.append((method, args))
            if method == 'conversations.history':
                return {'messages': messages}
            if method == 'conversations.replies':
                return {'messages': threads}
            if method == 'users.info':
                return {'user': {'real_name': 'A teammate'}}
            raise AssertionError(method)
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.helper.poll(api, 'C_EXAMPLE', 'U_SELF', self.state, {}, now=10000)
        return out.getvalue(), calls

    def test_first_read_seeds_state_and_is_quiet(self):
        output, _ = self.poll([{'ts': '1.0', 'user': 'U_OTHER', 'text': 'old'}])
        self.assertEqual(output, '')
        self.assertEqual(self.state.read_text().split(), ['1.0'])

    def test_first_post_after_an_empty_baseline_is_delivered(self):
        self.assertEqual(self.poll([])[0], '')
        output, _ = self.poll([{'ts': '1.0', 'user': 'U_OTHER', 'text': 'first request'}])
        self.assertIn('first request', output)

    def test_untagged_human_and_worker_posts_arrive_once_in_order(self):
        self.state.write_text('1.0')
        messages = [
            {'ts': '3.0', 'user': 'U_WORKER', 'bot_id': 'B_WORKER', 'text': 'Build ready'},
            {'ts': '2.0', 'user': 'U_OTHER', 'text': 'Can we ship this today?'},
        ]
        output, _ = self.poll(messages)
        self.assertIn('Can we ship this today?', output)
        self.assertIn('Build ready', output)
        self.assertLess(output.index('2.0'), output.index('3.0'))
        self.assertEqual(self.poll(messages)[0], '')

    def test_own_posts_and_join_events_are_seen_but_not_emitted(self):
        self.state.write_text('1.0')
        messages = [
            {'ts': '2.0', 'user': 'U_SELF', 'text': 'my post'},
            {'ts': '3.0', 'user': 'U_NEW', 'subtype': 'channel_join', 'text': 'joined'},
            {'ts': '4.0', 'subtype': 'bot_add', 'text': 'bot added'},
        ]
        output, _ = self.poll(messages)
        self.assertEqual(output, '')
        self.assertEqual(set(self.state.read_text().split()), {'1.0', '2.0', '3.0', '4.0'})

    def test_recent_thread_replies_are_emitted_and_old_threads_are_not_read(self):
        self.state.write_text('1.0')
        parent = {'ts': '2.0', 'user': 'U_SELF', 'text': 'parent', 'reply_count': 1, 'latest_reply': '9999'}
        reply = {'ts': '9999', 'thread_ts': '2.0', 'user': 'U_OTHER', 'text': 'thread question'}
        output, calls = self.poll([parent], threads=[parent, reply])
        self.assertIn('(thread 2.0)', output)
        self.assertIn('thread question', output)
        self.assertEqual(sum(m == 'conversations.replies' for m, _ in calls), 1)
        parent['latest_reply'] = '100'
        _, calls = self.poll([parent])
        self.assertFalse(any(m == 'conversations.replies' for m, _ in calls))

    def test_unreadable_thread_does_not_block_an_untagged_top_level_request(self):
        self.state.write_text('1.0')
        def api(method, **args):
            if method == 'conversations.history':
                return {'messages': [
                    {'ts': '2.0', 'user': 'U_SELF', 'reply_count': 1, 'latest_reply': '9999'},
                    {'ts': '3.0', 'user': 'U_OTHER', 'text': 'ordinary request'},
                ]}
            if method == 'conversations.replies':
                raise self.helper.SlackError('missing_scope')
            return {'user': {'real_name': 'A teammate'}}
        out = io.StringIO()
        import warnings
        with warnings.catch_warnings(record=True), contextlib.redirect_stdout(out):
            self.helper.poll(api, 'C_EXAMPLE', 'U_SELF', self.state, {}, now=10000)
        self.assertIn('ordinary request', out.getvalue())
        self.assertIn('3.0', self.state.read_text().split())

    def test_name_lookup_rate_limit_delivers_message_then_requests_backoff(self):
        self.state.write_text('1.0')
        def api(method, **args):
            if method == 'conversations.history':
                return {'messages': [{'ts': '2.0', 'user': 'U_OTHER', 'text': 'ordinary request'}]}
            raise self.helper.SlackError('http_429', retry_after=120)
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            with self.assertRaises(self.helper.SlackError) as raised:
                self.helper.poll(api, 'C_EXAMPLE', 'U_SELF', self.state, {}, now=10000)
        self.assertIn('ordinary request', out.getvalue())
        self.assertEqual(raised.exception.retry_after, 120)
        self.assertIn('2.0', self.state.read_text().split())

    def test_api_failure_preserves_existing_state(self):
        self.state.write_text('1.0')
        def fail(*args, **kwargs):
            raise self.helper.SlackError('missing_scope')
        with self.assertRaises(self.helper.SlackError):
            self.helper.poll(fail, 'C_EXAMPLE', 'U_SELF', self.state, {}, now=10000)
        self.assertEqual(self.state.read_text(), '1.0')

    def test_printed_preview_keeps_live_watchers_600_character_limit(self):
        self.state.write_text('1.0')
        output, _ = self.poll([{'ts': '2.0', 'user': 'U_OTHER', 'text': 'x' * 601}])
        self.assertIn('x' * 600, output)
        self.assertNotIn('x' * 601, output)

    def test_post_uses_selected_identity_and_has_no_thread(self):
        slack = self.helper.Slack('test-token', 'C_EXAMPLE')
        calls = []
        def api(method, **args):
            calls.append((method, args))
            return {'ts': '2.0'}
        with patch.object(slack, 'call', side_effect=api):
            self.assertEqual(slack.post('hello'), {'ts': '2.0'})
        method, args = calls[0]
        self.assertEqual(method, 'chat.postMessage')
        self.assertEqual(args['channel'], 'C_EXAMPLE')
        self.assertEqual(args['text'], 'hello')
        self.assertNotIn('thread_ts', args)

    def test_http_post_carries_the_selected_token_and_exact_stdin_text(self):
        slack = self.helper.Slack('test-token', 'C_EXAMPLE')
        response = io.BytesIO(b'{"ok": true, "ts": "2.0"}')
        with patch.object(self.helper.urllib.request, 'urlopen', return_value=response) as send:
            slack.post('literal $() and `text`\nsecond line')
        request = send.call_args.args[0]
        self.assertEqual(request.get_method(), 'POST')
        self.assertEqual(request.get_header('Authorization'), 'Bearer test-token')
        payload = json.loads(request.data)
        self.assertEqual(payload['channel'], 'C_EXAMPLE')
        self.assertEqual(payload['text'], 'literal $() and `text`\nsecond line')
        self.assertNotIn('thread_ts', payload)

    def test_http_rate_limit_exposes_retry_delay_without_response_body(self):
        slack = self.helper.Slack('test-token', 'C_EXAMPLE')
        error = self.helper.urllib.error.HTTPError(
            'https://slack.com/api/conversations.history', 429, 'rate limited',
            {'Retry-After': '60'}, io.BytesIO(b'test-token'))
        with patch.object(self.helper.urllib.request, 'urlopen', side_effect=error):
            with self.assertRaises(self.helper.SlackError) as raised:
                slack.call('conversations.history', channel='C_EXAMPLE')
        self.assertEqual(str(raised.exception), 'http_429')
        self.assertEqual(raised.exception.retry_after, 60)

    def test_slack_error_reports_code_without_raw_response_or_token(self):
        slack = self.helper.Slack('test-token', 'C_EXAMPLE')
        response = io.BytesIO(json.dumps({'ok': False, 'error': 'missing_scope', 'debug': 'test-token'}).encode())
        with patch.object(self.helper.urllib.request, 'urlopen', return_value=response):
            with self.assertRaisesRegex(self.helper.SlackError, '^missing_scope$'):
                slack.call('auth.test')


if __name__ == '__main__':
    unittest.main()
