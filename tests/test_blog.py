import json
from datetime import date
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import blog

SOURCE = {'title': 'A useful source', 'url': 'https://huggingface.co/blog/example', 'text': 'Evidence'}

def article(**overrides):
    data = {'title': 'A useful idea', 'summary': 'What the source explains.',
            'body': '## An idea\n\n' + 'A supported explanation. ' * 90 + '\n\n[Source](' + SOURCE['url'] + ')',
            'approved': True}
    return json.dumps(dict(data, **overrides))

class BlogTests(unittest.TestCase):
    def test_editor_rejection_and_bad_citations_never_save(self):
        for raw in [article(approved=False), article(body='word ' * 300),
                    article(body='word ' * 300 + '[Source](https://evil.example)'),
                    article(body='word ' * 300 + '<script>x</script>'), article(title='')]:
            with self.subTest(raw=raw[:30]), self.assertRaises(ValueError):
                blog.validate_article(raw, SOURCE)

    def test_valid_post_roundtrip_and_duplicate_day_or_source(self):
        with tempfile.TemporaryDirectory() as temp:
            posts = Path(temp)
            data = blog.validate_article(article(), SOURCE)
            saved = blog.save_post(data, SOURCE, posts, date(2026, 9, 15))
            self.assertEqual(json.loads(saved.read_text())['source_url'], SOURCE['url'])
            self.assertIsNone(blog.save_post(data, dict(SOURCE, url='https://huggingface.co/blog/another'), posts, date(2026, 9, 15)))
            self.assertIsNone(blog.save_post(data, SOURCE, posts, date(2026, 9, 16)))
            self.assertEqual(len(list(posts.glob('*.json'))), 1)

    def test_fresh_sources_only_and_host_filter(self):
        def item(url, day):
            return f'<item><title>Story</title><link>{url}</link><pubDate>{day}</pubDate></item>'
        xml = '<rss><channel>' + item(SOURCE['url'], 'Tue, 15 Sep 2026 10:00:00 GMT') + item('https://evil.example/x', 'Tue, 15 Sep 2026 10:00:00 GMT') + item(SOURCE['url']+'/old', 'Sat, 01 Aug 2026 10:00:00 GMT') + '</channel></rss>'
        self.assertEqual(len(blog.feed_items(xml, ['huggingface.co'], date(2026, 9, 15))), 1)

    def test_no_new_source_is_a_clean_skip(self):
        with tempfile.TemporaryDirectory() as temp, patch('blog.fetch', return_value='<rss><channel/></rss>'):
            self.assertIsNone(blog.choose_source({'feeds':[{'url': SOURCE['url'], 'hosts':['huggingface.co']}]}, Path(temp), date(2026,9,15)))

    def test_source_fetch_failure_is_not_empty_success(self):
        with tempfile.TemporaryDirectory() as temp, patch('blog.fetch', side_effect=OSError('offline')):
            with self.assertRaises(RuntimeError):
                blog.choose_source({'feeds':[{'url': SOURCE['url'], 'hosts':['huggingface.co']}]}, Path(temp), date(2026,9,15))

    def test_reject_unapproved_source_before_network(self):
        with self.assertRaises(ValueError):
            blog.fetch('http://localhost/private', ['huggingface.co'])

if __name__ == '__main__':
    unittest.main()
