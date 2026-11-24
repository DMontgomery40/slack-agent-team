import contextlib
import importlib.util
import io
import json
import tempfile
import unittest
from pathlib import Path

HELPER = Path(__file__).resolve().parents[1] / 'scripts' / 'team.py'


class TeamHelperTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location('team_helper', HELPER)
        cls.helper = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.helper)

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.room = self.helper.room_path(self.base, 'general')
        self.state = self.base / 'seen.txt'

    def poll(self, self_handle=None):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.helper.poll(self.room, self.state, self_handle)
        return out.getvalue()

    def test_post_writes_the_app_schema(self):
        self.helper.post(self.room, 'hello @codex', 'claude')
        self.helper.post(self.room, 'and from me')
        first, second = [json.loads(line) for line in self.room.read_text().splitlines()]
        self.assertEqual((first['from'], first['kind'], first['text'], first['hop']), ('claude', 'agent', 'hello @codex', 0))
        self.assertEqual((second['from'], second['kind']), ('human', 'human'))
        self.assertIsInstance(first['ts'], int)
        self.assertNotEqual(first['id'], second['id'])

    def test_text_is_kept_literally(self):
        self.helper.post(self.room, 'literal $() and `text`\nsecond line')
        self.assertEqual(self.helper.read(self.room)[0]['text'], 'literal $() and `text`\nsecond line')

    def test_first_watch_seeds_then_prints_only_new(self):
        self.helper.post(self.room, 'old news')
        self.assertEqual(self.poll(), '')
        self.helper.post(self.room, 'fresh   request\nwith lines', 'claude')
        self.assertEqual(self.poll().strip().split(' ', 2)[2], '@claude: fresh request with lines')
        self.assertEqual(self.poll(), '')

    def test_watch_skips_own_posts_and_system_notes(self):
        self.poll()
        self.helper.post(self.room, 'mine', 'claude')
        with self.room.open('a') as handle:
            handle.write(json.dumps({'id': 'sys1', 'ts': 1, 'from': 'system', 'kind': 'system', 'text': 'Loop guard'}) + '\n')
        self.helper.post(self.room, 'yours')
        self.assertEqual(self.poll('claude').strip().split(' ', 2)[2], 'human: yours')

    def test_bad_lines_are_ignored(self):
        self.room.parent.mkdir(parents=True)
        self.room.write_text('not json\n{"id": 3, "text": "x"}\n{"id": "ok", "text": "fine"}\n')
        self.assertEqual([m['id'] for m in self.helper.read(self.room)], ['ok'])

    def test_room_and_handle_names_are_checked(self):
        with self.assertRaises(ValueError):
            self.helper.room_path(self.base, '../etc')
        with self.assertRaises(ValueError):
            self.helper.post(self.room, 'x', 'Bad Handle')

    def test_missing_room_reads_empty(self):
        self.assertEqual(self.helper.read(self.helper.room_path(self.base, 'nobody')), [])


if __name__ == '__main__':
    unittest.main()
