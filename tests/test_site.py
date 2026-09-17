import json
import tempfile
import unittest
from pathlib import Path

from blog_site import build_site


class SiteTests(unittest.TestCase):
    def test_safe_content_and_project_navigation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            posts = root / 'posts'
            posts.mkdir()
            post = {'title': '<script>title</script>', 'summary': '<img src=x onerror=alert(1)>', 'date': '2026-09-15', 'body': '<script>alert(1)</script>\n\n[bad](javascript:alert(1))\n\n[good](https://example.org/read)', 'sources': [{'title': '<b>Source</b>', 'url': 'https://example.org/?a=1&b=2'}]}
            (posts / '2026-09-15-example.json').write_text(json.dumps(post))
            output = root / 'site'
            build_site(posts, output, 'https://example.github.io/my-blog')
            index = (output / 'index.html').read_text()
            article = (output / 'posts/2026-09-15-example.html').read_text()
            self.assertIn('href="posts/2026-09-15-example.html"', index)
            self.assertIn('href="../index.html"', article)
            self.assertIn('href="../style.css"', article)
            self.assertIn('https://example.github.io/my-blog/posts/2026-09-15-example.html', article)
            self.assertNotIn('<script>', article)
            self.assertNotIn('<img', article)
            self.assertNotIn('href="javascript:', article)
            self.assertIn('href="https://example.org/read"', article)
            self.assertIn('&lt;b&gt;Source&lt;/b&gt;', article)
            self.assertIn('AI-assisted', article)

    def test_invalid_committed_post_stops_the_build(self):
        cases = [
            [],
            {'title': '', 'summary': 'Summary', 'date': '2026-09-15', 'body': 'Body'},
            {'title': 'Title', 'summary': 'Summary', 'date': 'not-a-date', 'body': 'Body'},
            {'title': 'Title', 'summary': 'Summary', 'date': '2026-09-15', 'body': 'Body',
             'sources': [{'title': 'Unsafe', 'url': 'javascript:alert(1)'}]},
        ]
        for post in cases:
            with self.subTest(post=post), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                posts = root / 'posts'
                posts.mkdir()
                (posts / 'bad.json').write_text(json.dumps(post))
                with self.assertRaisesRegex(ValueError, 'Invalid post bad.json'):
                    build_site(posts, root / 'site')

    def test_empty_blog_builds(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            build_site(root / 'missing', root / 'site')
            self.assertIn('No articles yet', (root / 'site/index.html').read_text())

    def test_rebuild_removes_deleted_article_only(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            posts = root / 'posts'
            posts.mkdir()
            article = posts / '2026-09-15-example.json'
            article.write_text(json.dumps({'title': 'Example', 'summary': 'Summary',
                                          'date': '2026-09-15', 'body': 'Body'}))
            output = root / 'site'
            build_site(posts, output)
            rendered = output / 'posts' / '2026-09-15-example.html'
            self.assertTrue(rendered.exists())
            attachment = output / 'posts' / 'notes.txt'
            attachment.write_text('Keep me')
            nested = output / 'posts' / 'archive'
            nested.mkdir()
            (nested / 'custom.html').write_text('Keep this too')
            article.unlink()
            build_site(posts, output)
            self.assertFalse(rendered.exists())
            self.assertNotIn('2026-09-15-example.html', (output / 'index.html').read_text())
            self.assertEqual(attachment.read_text(), 'Keep me')
            self.assertEqual((nested / 'custom.html').read_text(), 'Keep this too')


if __name__ == '__main__':
    unittest.main()
