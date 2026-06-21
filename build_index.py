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


def categorize_post(tags: list) -> str:
    """Determine category class for a post based on its tags."""
    if not tags:
        return "lain"
    
    first_tag = str(tags[0]).lower()
    
    # Check AI category first (more comprehensive for existing AI posts)
    if any(word in first_tag for word in [
        "kecerdasan buatan", "kecerdasan-buatan", "artificial", "ai ", "anthropic",
        "claude code", "openai", "gpt", "gemini", "cohere", "llama", "llm", 
        "generative ai", "spacex", "google", "machine learning", "deepmind", 
        "claude", "chatgpt", "perplexity", "meta ai"
    ]):
        return "ai"
    elif "pasar modal" in first_tag:
        return "pasar-modal"
    elif any(word in first_tag for word in ["cyber security", "cybersecurity", "keamanan siber", "ransomware", "breach", "ransom", "data breach"]):
        return "cyber-security"
    elif any(word in first_tag for word in ["indeks", "saham", "stock", "stock exchange", "istock", "ikgrs"]):
        return "pasar-modal"
    elif any(word in first_tag for word in ["emas", "gold", "precious"]):
        return "pasar-modal"
    elif any(word in first_tag for word in ["crypto", "bitcoin", "blockchain", "btc", "solana", "ethereum"]):
        return "pasar-modal"
    else:
        return "lain"


def render_index(posts: list[dict]) -> str:
    cards = []
    counts = {"ai": 0, "pasar-modal": 0, "cyber-security": 0, "lain": 0}
    for i, p in enumerate(posts):
        # Parse date for display
        try:
            dt = datetime.strptime(p["date"], "%Y-%m-%d")
            date_label = dt.strftime("%d %b %Y")
        except ValueError:
            date_label = p["date"]
        # First tag as badge with category class
        badge = ""
        category = categorize_post(p.get("tags", []))
        counts[category] = counts.get(category, 0) + 1
        if p.get("tags"):
            badge = f'<span class="badge {category}">{p["tags"][0]}</span>'
        # All tags as small list
        tags_html = ""
        if len(p.get("tags", [])) > 1:
            tags_html = " · " + " · ".join(p["tags"][1:4])
        # NEW badge only for most recent post
        new_badge = '<span class="new-badge">✦ NEW</span>' if i == 0 else ""
        cards.append(
            f'''        <a class="post-card {category}" href="/posts/{p["filename"]}" data-category="{category}">
          <div class="date">{date_label} {new_badge} {badge}{tags_html}</div>
          <h2>{p["title"]}</h2>
          <p>{p["summary"]}</p>
          <span class="read-more">Baca selengkapnya</span>
        </a>'''
        )
    cards_html = "\n".join(cards) if cards else '<p style="color: var(--text-faint); text-align: center; padding: 60px 0;">Belum ada artikel. Post pertama akan muncul di sini besok pagi 🌅</p>'

    total = len(posts)
    last_date = posts[0]["date"] if posts else "—"
    site_url = "https://blog.ttmi.my.id"
    count_ai = counts["ai"]
    count_pasar = counts["pasar-modal"]
    count_cyber = counts["cyber-security"]
    count_lain = counts["lain"]
    return f"""<!DOCTYPE html>
<html lang="id">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>AI Daily — Berita Perkembangan AI Terkini</title>
  <meta name="description" content="Ringkasan harian perkembangan AI: model baru, riset, tools, dan dampaknya. Update otomatis setiap hari.">
  <meta name="theme-color" content="#0a0a0f">
  <meta name="google-site-verification" content="-XPmvwqdXwmIqBQqVemlrNZsAFA1cuJS3QGrR87-SRE">
  <link rel="canonical" href="{site_url}/">
  <meta name="robots" content="index, follow">
  <meta name="author" content="Teguh Yuhono">
  <meta name="language" content="id-ID">
  <meta name="revisit-after" content="1 day">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap">
  <link rel="stylesheet" href="/assets/style.css?v=2">
  <link rel="icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><text y=%22.9em%22 font-size=%2290%22>🤖</text></svg>">

  <!-- Open Graph / Facebook -->
  <meta property="og:type" content="website">
  <meta property="og:url" content="{site_url}/">
  <meta property="og:title" content="AI Daily — Berita Perkembangan AI Terkini">
  <meta property="og:description" content="Ringkasan harian perkembangan AI: model baru, riset, tools, dan dampaknya. Update otomatis setiap hari.">
  <meta property="og:image" content="{site_url}/assets/hero-light-installation-museum.jpg">
  <meta property="og:image:alt" content="Geometric light installation art museum">
  <meta property="og:site_name" content="AI Daily">
  <meta property="og:locale" content="id_ID">

  <!-- Twitter Card -->
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="AI Daily — Berita Perkembangan AI Terkini">
  <meta name="twitter:description" content="Ringkasan harian perkembangan AI: model baru, riset, tools, dan dampaknya. Update otomatis setiap hari.">
  <meta name="twitter:image" content="{site_url}/assets/hero-light-installation-museum.jpg">
  <meta name="twitter:site" content="@teguhyuhono">
  <meta name="twitter:creator" content="@teguhyuhono">

  <!-- Schema.org structured data -->
  <script type="application/ld+json">
{{
  "@context": "https://schema.org",
  "@type": "WebSite",
  "name": "AI Daily",
  "description": "Ringkasan harian perkembangan AI: model baru, riset, tools, dan dampaknya. Update otomatis setiap hari.",
  "url": "{site_url}/",
  "inLanguage": "id-ID",
  "copyrightYear": "{datetime.now().year}",
  "author": {{
    "@type": "Person",
    "name": "Teguh Yuhono",
    "url": "https://hermes.ttmi.my.id"
  }},
  "potentialAction": [
    {{
      "@type": "SearchAction",
      "target": "{site_url}/?search={{query}}",
      "query-input": "required name=query"
    }}
  ]
}}
  </script>
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
      <h1>News & Insights, setiap hari.</h1>
      <p>Ringkasan otomatis harian: AI, pasar modal, dan keamanan siber — dikurasi dari sumber tepercaya dan ditulis dalam Bahasa Indonesia.</p>
      <div class="meta">
        <span class="pill">Auto-posting aktif</span>
        <span>{total} artikel</span>
        <span>· terakhir update {last_date}</span>
        <span>· posting 08:00 / 08:30 / 09:00 WIB</span>
      </div>
    </section>

    <nav class="category-nav" aria-label="Filter kategori">
      <button class="cat-btn active" data-filter="all">Semua <span class="cat-count">{total}</span></button>
      <button class="cat-btn" data-filter="ai">AI / Kecerdasan Buatan <span class="cat-count">{count_ai}</span></button>
      <button class="cat-btn" data-filter="pasar-modal">Pasar Modal <span class="cat-count">{count_pasar}</span></button>
      <button class="cat-btn" data-filter="cyber-security">Cyber Security <span class="cat-count">{count_cyber}</span></button>
      <button class="cat-btn" data-filter="lain">Lainnya <span class="cat-count">{count_lain}</span></button>
    </nav>

    <section class="posts" id="posts-grid">
{cards_html}
    </section>
  </main>

  <script>
    // Category filter — pure client-side, no page reload
    (function() {{
      const buttons = document.querySelectorAll('.cat-btn');
      const cards = document.querySelectorAll('.post-card');
      const empty = document.getElementById('empty-msg');
      buttons.forEach(btn => {{
        btn.addEventListener('click', () => {{
          buttons.forEach(b => b.classList.remove('active'));
          btn.classList.add('active');
          const filter = btn.dataset.filter;
          let visible = 0;
          cards.forEach(card => {{
            const match = filter === 'all' || card.dataset.category === filter;
            card.style.display = match ? '' : 'none';
            if (match) visible++;
          }});
          if (empty) empty.style.display = visible === 0 ? 'block' : 'none';
        }});
      }});
    }})();
  </script>

  <footer class="site-footer">
    <div class="container">
      Dibuat otomatis oleh <a href="https://hermes.ttmi.my.id" target="_blank" rel="noopener">Hermes Agent</a> · © {datetime.now().year} Teguh Yuhono
    </div>
  </footer>


</body>
</html>
"""




def render_donation_widget() -> str:
    """Return the donation widget HTML/JS."""
    payment_addresses = {
        "btc": ("₿", "BTC", "3FQUMv4MfW9ntmJTDbKaS7YHnKu9TUhv7N"),
        "eth": ("Ξ", "ETH", "0x74cDDBFA3c43316ff4D066fe79e75B6F89b544E4"),
        "bnbbsc": ("🔶", "BNB", "0x05F9EdAee97e6f8534751de68AC5eEF739bEca4f"),
        "sol": ("◎", "SOL", "3W24GeYY8CM6LgQM8a6Rdwxdwz3WpjKu9DE5P6fhA9Bz"),
        "trx": ("⬡", "TRX", "TQJGge33fF4iea398bEX6sGx8HqTqH2FoQ"),
        "xrp": ("✕", "XRP", "rKKbNYZRqwPgZYkFWvqNUFBuscEyiFyCE"),
        "ltc": ("Ł", "LTC", "MC9Am59PL9CNGtZaG9Nw3gAqn1rdPaFsSE"),
        "doge": ("Ð", "DOGE", "D5mZYoQqcU6wxCcn8KPEmaDsdM7dVi12ks"),
        "matic": ("⬟", "MATIC", "0x011c586e54D0Bd4009a9ad2A080863026F10e85d"),
    }
    buttons = "\n".join(
        f'<a href="https://nowpayments.io/donate/{addr}" target="_blank" rel="noopener" class="donate-coin"><span class="donate-icon">{icon}</span><span class="donate-name">{name}</span></a>'
        for icon, name, addr in payment_addresses.values()
    )
    return (
        "\n<style>\n"
        ".donation-section{max-width:420px;margin:40px auto 20px;padding:28px 24px;background:linear-gradient(135deg,#0a0a1a 0%,#1a1a3a 100%);border-radius:16px;border:1px solid rgba(255,255,255,0.1);text-align:center}\n"
        ".donation-section h3{color:#fff;font-size:17px;margin:0 0 6px}\n"
        ".donation-section .donate-sub{color:#888;font-size:12px;margin:0 0 16px;line-height:1.5}\n"
        ".donation-coins{display:flex;flex-wrap:wrap;justify-content:center;gap:8px}\n"
        ".donate-coin{display:inline-flex;flex-direction:column;align-items:center;padding:10px 12px;background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.1);border-radius:10px;color:#fff;text-decoration:none;transition:all .2s;min-width:60px}\n"
        ".donate-coin:hover{background:rgba(255,255,255,0.12);transform:translateY(-2px)}\n"
        ".donate-icon{font-size:20px;margin-bottom:2px}\n"
        ".donate-name{font-size:10px;font-weight:600;color:#ccc}\n"
        ".donation-section .powered{color:#555;font-size:10px;margin-top:12px}\n"
        "</style>\n"
        '<div class="donation-section">\n'
        "<h3>☕ Support AI Daily</h3>\n"
        '<p class="donate-sub">Dukung blog ini dengan crypto untuk tetap update setiap hari</p>\n'
        '<div class="donation-coins">\n'
        f"{buttons}\n"
        '</div>\n'
        '<p class="powered">Powered by NOWPayments</p>\n'
        "</div>\n"
    )


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
    
    # Generate donation widget HTML
    donation_html = render_donation_widget()
    
    # Render index with donation widget
    index_html = render_index(posts)
    if '</footer>\n</body>' in index_html:
        index_html = index_html.replace(
            '</footer>\n</body>',
            f'</footer>\n\n{donation_html}\n</body>'
        )
    
    INDEX.write_text(index_html, encoding="utf-8")
    print(f"✓ index.html rebuilt — {len(posts)} posts + donation widget")
    
    (ROOT / "feed.xml").write_text(render_rss(posts), encoding="utf-8")
    print(f"✓ feed.xml rebuilt — {len(posts)} posts (max 20 in feed)")


if __name__ == "__main__":
    main()
