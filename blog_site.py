"""Build a small static blog from generated, reviewed JSON posts."""
from __future__ import annotations

import json
from html import escape
from pathlib import Path
from urllib.parse import quote, urlparse

from markdown_it import MarkdownIt

CSS = """*{box-sizing:border-box}body{margin:0;background:#faf9f6;color:#292923;font:18px/1.75 Georgia,serif}main,header,footer{max-width:760px;margin:auto;padding:24px}header{border-bottom:1px solid #deded5;font-family:system-ui,sans-serif}header a{font-weight:700}a{color:#24584b;text-underline-offset:3px}h1,h2,h3{line-height:1.2}h1{font-size:clamp(2rem,6vw,3rem);letter-spacing:-.04em}h2{font-size:1.6rem}article{margin:24px 0 48px}article.card{border-bottom:1px solid #deded5;padding-bottom:24px;margin-bottom:24px}.meta,footer{color:#64645a;font:14px/1.6 system-ui,sans-serif}.summary{font-size:1.2rem;color:#56564d}pre{overflow:auto;background:#eeeee6;padding:16px;font-size:14px}code{overflow-wrap:anywhere}blockquote{margin-left:0;padding-left:20px;border-left:3px solid #aebbae}img{max-width:100%}li{margin:6px 0}footer{border-top:1px solid #deded5}nav{margin-bottom:24px}.sources{font-size:16px}a:focus-visible{outline:3px solid #92b5a6;outline-offset:3px}"""


def _http_url(value: object) -> str:
    if not isinstance(value, str):
        return ""
    parsed = urlparse(value)
    return value if parsed.scheme in {"https", "http"} and parsed.netloc else ""


def _markdown(body: str) -> str:
    parser = MarkdownIt("commonmark", {"html": False})
    parser.validateLink = lambda url: bool(_http_url(url))
    # Avoid tracking images and make the site's output independent of remote assets.
    parser.disable("image")
    return parser.render(body)


def _page(title: str, content: str, prefix: str, canonical: str = "") -> str:
    canonical_tag = f'<link rel="canonical" href="{escape(canonical, quote=True)}">' if canonical else ""
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{escape(title)} · Field Notes</title>{canonical_tag}<link rel="stylesheet" href="{prefix}style.css"></head>
<body><header><a href="{prefix}index.html">Field Notes</a><div class="meta">A small, source-linked blog</div></header>
<main>{content}</main><footer>AI-assisted articles. Read the linked sources and verify important claims.</footer></body></html>'''


def build_site(posts_dir: Path, output_dir: Path, site_url: str = "") -> None:
    """Write index and article pages with portable relative navigation."""
    output_dir = Path(output_dir)
    (output_dir / "posts").mkdir(parents=True, exist_ok=True)
    (output_dir / "style.css").write_text(CSS, encoding="utf-8")
    base = _http_url(site_url).rstrip("/")
    posts = []
    source_paths = sorted(Path(posts_dir).glob("*.json"), reverse=True)
    expected_pages = {path.stem + ".html" for path in source_paths}
    for path in source_paths:
        post = json.loads(path.read_text(encoding="utf-8"))
        title, summary = escape(post["title"]), escape(post["summary"])
        date = escape(post["date"])
        filename = path.stem + ".html"
        href = "posts/" + quote(filename)
        sources = []
        for source in post.get("sources", []):
            url = _http_url(source.get("url"))
            if url:
                sources.append(f'<li><a href="{escape(url, quote=True)}" rel="noopener noreferrer">{escape(source.get("title") or url)}</a></li>')
        source_section = '<section class="sources"><h2>Sources</h2><ul>' + "".join(sources) + "</ul></section>" if sources else ""
        content = f'<nav><a href="../index.html">← All articles</a></nav><article><p class="meta">{date} · AI-assisted</p><h1>{title}</h1><p class="summary">{summary}</p>{_markdown(post["body"])}{source_section}</article>'
        (output_dir / "posts" / filename).write_text(_page(post["title"], content, "../", f"{base}/{href}" if base else ""), encoding="utf-8")
        posts.append(f'<article class="card"><p class="meta">{date} · AI-assisted</p><h2><a href="{escape(href, quote=True)}">{title}</a></h2><p>{summary}</p></article>')
    content = '<h1>Field Notes</h1><p class="summary">Ideas worth exploring, with sources worth reading.</p>' + ("".join(posts) or "<p>No articles yet. Check back soon.</p>")
    (output_dir / "index.html").write_text(_page("Latest articles", content, "", base + "/" if base else ""), encoding="utf-8")
    for rendered in (output_dir / "posts").glob("*.html"):
        if rendered.is_file() and rendered.name not in expected_pages:
            rendered.unlink()
