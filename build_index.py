#!/usr/bin/env python3
"""build_index.py — Regenerate index.html from posts/*.html

Each post file must start with a <post-meta> JSON block, e.g.:

    <post-meta>
    {
      "date": "2026-06-14",
      "title": "...",
      "summary": "...",
      "tags": ["LLM", "OpenAI"],
      "slug": "openai-gpt-6-rilis"
    }
    </post-meta>

Then HTML body follows. The script extracts meta and generates a clean
index page.
"""
import json
import re
import os
import sys
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent
POSTS_DIR = ROOT / "posts"
INDEX = ROOT / "index.html"
TEMPLATE_PATH = Path(__file__).parent / "templates" / "index.html"

META_RE = re.compile(r"<post-meta>\s*(\{.*?\})\s*</post-meta>", re.DOTALL)


def extract_meta(path: Path) -> dict | None:
    """Parse <post-meta>...</post-meta> JSON block from a post HTML file."""
    try:
        text = path.read_text(encoding="utf-8")
    except Exception as e:
        print(f"  ! skip {path.name}: {e}", file=sys.stderr)
        return None
    m = META_RE.search(text)
    if not m:
        print(f"  ! skip {path.name}: no <post-meta> block", file=sys.stderr)
        return None
    try:
        meta = json.loads(m.group(1))
    except json.JSONDecodeError as e:
        print(f"  ! skip {path.name}: bad JSON in meta: {e}", file=sys.stderr)
        return None
    # Required fields
    for key in ("date", "title", "summary", "slug"):
        if key not in meta:
            print(f"  ! skip {path.name}: missing '{key}'", file=sys.stderr)
            return None
    meta.setdefault("tags", [])
    return meta


def collect_posts() -> list[dict]:
    posts = []
    for p in sorted(POSTS_DIR.glob("*.html"), reverse=True):
        meta = extract_meta(p)
        if meta:
            meta["filename"] = p.name
            posts.append(meta)
    posts.sort(key=lambda x: x["date"], reverse=True)
    return posts


def render_index(posts: list[dict]) -> str:
    cards = []
    for i, p in enumerate(posts):
        # Parse date for display
        try:
            dt = datetime.strptime(p["date"], "%Y-%m-%d")
            date_label = dt.strftime("%d %b %Y")
        except ValueError:
            date_label = p["date"]
        # First tag as badge
        badge = ""
        if p.get("tags"):
            badge = f'<span class="badge">{p["tags"][0]}</span>'
        # All tags as small list
        tags_html = ""
        if len(p.get("tags", [])) > 1:
            tags_html = " · " + " · ".join(p["tags"][1:4])
        # NEW badge only for most recent post
        new_badge = '<span class="new-badge">✦ NEW</span>' if i == 0 else ""
        cards.append(
            f'''        <a class="post-card" href="/posts/{p["filename"]}">
          <div class="date">{date_label} {new_badge} {badge}{tags_html}</div>
          <h2>{p["title"]}</h2>
          <p>{p["summary"]}</p>
          <span class="read-more">Baca selengkapnya</span>
        </a>'''
        )
    cards_html = "\n".join(cards) if cards else '<p style="color: var(--text-faint); text-align: center; padding: 60px 0;">Belum ada artikel. Post pertama akan muncul di sini besok pagi 🌅</p>'

    total = len(posts)
    last_date = posts[0]["date"] if posts else "—"
    return f"""<!DOCTYPE html>
<html lang="id">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>AI Daily — Berita Perkembangan AI Terkini</title>
  <meta name="description" content="Ringkasan harian perkembangan AI: model baru, riset, tools, dan dampaknya. Update otomatis setiap hari.">
  <meta name="theme-color" content="#0a0a0f">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap">
  <link rel="stylesheet" href="/assets/style.css?v=2">
  <link rel="icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><text y=%22.9em%22 font-size=%2290%22>🤖</text></svg>">
</head>
<body>
  <header class="site-header" id="site-header">
    <div class="container">
      <a class="logo" href="/"><span class="dot"></span> AI Daily</a>
      <nav class="nav-links">
        <a href="https://github.com/teguh2910" target="_blank" rel="noopener">GitHub</a>
        <a href="/feed.xml">RSS</a>
      </nav>
    </div>
  </header>

  <main class="container">
    <section class="hero">
      <h1>Perkembangan AI, setiap hari.</h1>
      <p>Ringkasan otomatis rilis model, riset, dan tools AI terpenting — dikurasi dari sumber tepercaya dan ditulis dalam Bahasa Indonesia.</p>
      <div class="meta">
        <span class="pill">Auto-posting aktif</span>
        <span>{total} artikel</span>
        <span>· terakhir update {last_date}</span>
        <span>· posting 08:00 WIB</span>
      </div>
    </section>

    <section class="posts">
{cards_html}
    </section>
  </main>

  <footer class="site-footer">
    <div class="container">
      Dibuat otomatis oleh <a href="https://hermes.ttmi.my.id" target="_blank" rel="noopener">Hermes Agent</a> · © {datetime.now().year} Teguh Yuhono
    </div>
  </footer>
</body>
</html>
"""


def render_rss(posts: list[dict]) -> str:
    """Generate a simple RSS 2.0 feed for the latest 20 posts."""
    items = []
    for p in posts[:20]:
        try:
            dt = datetime.strptime(p["date"], "%Y-%m-%d")
            pub = dt.strftime("%a, %d %b %Y 00:00:00 +0700")
        except ValueError:
            pub = p["date"]
        link = f"https://blog.ttmi.my.id/posts/{p['filename']}"
        items.append(
            f"""    <item>
      <title>{p['title']}</title>
      <link>{link}</link>
      <guid>{link}</guid>
      <pubDate>{pub}</pubDate>
      <description>{p['summary']}</description>
    </item>"""
        )
    last_build = datetime.now().strftime("%a, %d %b %Y %H:%M:%S +0700")
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>AI Daily — Berita Perkembangan AI Terkini</title>
    <link>https://blog.ttmi.my.id</link>
    <description>Ringkasan harian perkembangan AI dalam Bahasa Indonesia.</description>
    <language>id-ID</language>
    <lastBuildDate>{last_build}</lastBuildDate>
    <atom:link href="https://blog.ttmi.my.id/feed.xml" rel="self" type="application/rss+xml" />
{chr(10).join(items)}
  </channel>
</rss>
"""


def main():
    posts = collect_posts()
    INDEX.write_text(render_index(posts), encoding="utf-8")
    print(f"✓ index.html rebuilt — {len(posts)} posts")
    (ROOT / "feed.xml").write_text(render_rss(posts), encoding="utf-8")
    print(f"✓ feed.xml rebuilt — {len(posts)} posts (max 20 in feed)")


if __name__ == "__main__":
    main()
