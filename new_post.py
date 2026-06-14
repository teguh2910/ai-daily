#!/usr/bin/env python3
"""new_post.py — Wrap post content into the full HTML template.

Usage (programmatic — the LLM writes the body markdown, this wraps it):

    python3 new_post.py \\
        --date 2026-06-14 \\
        --slug openai-rilis-model-baru \\
        --title "OpenAI Rilis Model Baru ..." \\
        --summary "Ringkasan 1-2 kalimat untuk index page." \\
        --tags "OpenAI" "LLM" --body-file body.md

Or with --body stdin:

    echo "## Heading..." | python3 new_post.py --date ... --body -

Outputs HTML to /var/www/blog.ttmi.my.id/posts/{date}-{slug}.html
then calls build_index.py.
"""
import argparse
import re
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
POSTS_DIR = ROOT / "posts"


def md_to_html(md: str) -> str:
    """Minimal markdown -> HTML. Handles headings, bold, italic, links, code, lists, blockquotes, paragraphs."""
    lines = md.split("\n")
    out = []
    in_ul = False
    in_ol = False
    in_code = False
    code_buf = []
    para_buf = []

    def flush_para():
        if para_buf:
            text = " ".join(para_buf).strip()
            if text:
                out.append(f"<p>{inline_md(text)}</p>")
            para_buf.clear()

    def close_lists():
        nonlocal in_ul, in_ol
        if in_ul:
            out.append("</ul>"); in_ul = False
        if in_ol:
            out.append("</ol>"); in_ol = False

    def inline_md(text: str) -> str:
        # Escape HTML
        text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        # Inline code first (so its content isn't processed)
        text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
        # Bold then italic
        text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
        text = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<em>\1</em>", text)
        # Links [text](url)
        text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2" target="_blank" rel="noopener">\1</a>', text)
        return text

    for line in lines:
        # Fenced code
        if line.strip().startswith("```"):
            if in_code:
                out.append("<pre><code>" + "\n".join(code_buf) + "</code></pre>")
                code_buf = []; in_code = False
            else:
                flush_para(); close_lists()
                in_code = True
            continue
        if in_code:
            code_buf.append(line)
            continue
        stripped = line.strip()
        # Headings
        if stripped.startswith("### "):
            flush_para(); close_lists()
            out.append(f"<h3>{inline_md(stripped[4:])}</h3>")
            continue
        if stripped.startswith("## "):
            flush_para(); close_lists()
            out.append(f"<h2>{inline_md(stripped[3:])}</h2>")
            continue
        if stripped.startswith("# "):
            flush_para(); close_lists()
            out.append(f"<h2>{inline_md(stripped[2:])}</h2>")
            continue
        # Blockquote
        if stripped.startswith("> "):
            flush_para(); close_lists()
            out.append(f"<blockquote>{inline_md(stripped[2:])}</blockquote>")
            continue
        # Unordered list
        if re.match(r"^[-*]\s+", stripped):
            flush_para()
            if not in_ul:
                close_lists(); out.append("<ul>"); in_ul = True
            item = inline_md(re.sub(r"^[-*]\s+", "", stripped))
            out.append(f"<li>{item}</li>")
            continue
        # Ordered list
        if re.match(r"^\d+\.\s+", stripped):
            flush_para()
            if not in_ol:
                close_lists(); out.append("<ol>"); in_ol = True
            item = inline_md(re.sub(r"^\d+\.\s+", "", stripped))
            out.append(f"<li>{item}</li>")
            continue
        # Empty line
        if not stripped:
            flush_para(); close_lists()
            continue
        # Paragraph text
        para_buf.append(stripped)

    flush_para()
    close_lists()
    if in_code and code_buf:
        out.append("<pre><code>" + "\n".join(code_buf) + "</code></pre>")
    return "\n".join(out)


def calc_reading_time(body_html: str) -> int:
    """Estimate reading time in minutes. ~200 words/min for Bahasa Indonesia."""
    # Strip HTML tags to count words
    import re as _re
    text = _re.sub(r"<[^>]+>", " ", body_html)
    words = len(text.split())
    return max(1, round(words / 200))


def render_post(date: str, title: str, summary: str, tags: list[str], body_html: str, slug: str, hero_image: str | None = None, hero_credit: str | None = None, post_url: str = "") -> str:
    import json
    meta = {
        "date": date,
        "title": title,
        "summary": summary,
        "tags": tags,
        "slug": slug,
    }
    if hero_image:
        meta["hero_image"] = hero_image
    if hero_credit:
        meta["hero_credit"] = hero_credit
    meta_block = f"<post-meta>\n{json.dumps(meta, ensure_ascii=False, indent=2)}\n</post-meta>"
    tags_html = " ".join(f'<span class="tag">{t}</span>' for t in tags)
    try:
        dt = datetime.strptime(date, "%Y-%m-%d")
        date_label = dt.strftime("%d %B %Y")
    except ValueError:
        date_label = date
    hero_html = ""
    if hero_image:
        credit_html = f'<span class="credit">📷 {hero_credit}</span>' if hero_credit else ""
        hero_html = f'<div class="hero-image"><img src="/assets/{hero_image}" alt="{title}" loading="lazy">{credit_html}</div>'
    reading_time = calc_reading_time(body_html)
    word_count = len(body_html.split())
    return f"""<!DOCTYPE html>
<html lang="id">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title} — AI Daily</title>
  <meta name="description" content="{summary}">
  <meta name="theme-color" content="#0a0a0f">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap">
  <link rel="stylesheet" href="/assets/style.css?v=3">
  <link rel="icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><text y=%22.9em%22 font-size=%2290%22>🤖</text></svg>">
  <meta property="og:title" content="{title}">
  <meta property="og:description" content="{summary}">
  <meta property="og:type" content="article">
  <meta property="og:url" content="{post_url}">
  <meta name="twitter:card" content="summary_large_image">
</head>
<body>
  {meta_block}
  <div class="reading-progress" id="reading-progress"></div>
  <header class="site-header" id="site-header">
    <div class="container">
      <a class="logo" href="/"><span class="dot"></span> AI Daily</a>
      <nav class="nav-links">
        <a href="/">← Kembali</a>
        <a href="/feed.xml">RSS</a>
      </nav>
    </div>
  </header>

  <article class="container post">
    {hero_html}
    <header class="post-header">
      <div class="meta-row">
        <span>📅 {date_label}</span>
        <span class="dot-sep"></span>
        <span>⏱️ {reading_time} menit baca</span>
        <span class="dot-sep"></span>
        <span>📝 {word_count} kata</span>
      </div>
      <h1>{title}</h1>
      <p class="summary">{summary}</p>
      <div class="tags">{tags_html}</div>
    </header>

    <div class="post-body">
{body_html}
    </div>

    <footer class="post-footer">
      <span>Dipublikasikan otomatis oleh <a href="https://hermes.ttmi.my.id" target="_blank" rel="noopener">Hermes Agent</a></span>
      <div class="actions">
        <button class="action-btn" id="copy-link" data-url="{post_url}">🔗 Salin link</button>
        <a class="action-btn" href="/">← Beranda</a>
      </div>
    </footer>
  </article>

  <button class="back-to-top" id="back-to-top" aria-label="Kembali ke atas">↑</button>

  <footer class="site-footer">
    <div class="container">
      Dibuat otomatis dengan <span class="heart">♥</span> oleh <a href="https://hermes.ttmi.my.id" target="_blank" rel="noopener">Hermes Agent</a> · © {datetime.now().year} Teguh Yuhono
    </div>
  </footer>

  <script>
  (function() {{
    const progress = document.getElementById('reading-progress');
    const header = document.getElementById('site-header');
    const backBtn = document.getElementById('back-to-top');
    const copyBtn = document.getElementById('copy-link');
    const article = document.querySelector('.post-body');

    function updateScroll() {{
      const scrolled = window.scrollY;
      const docHeight = document.documentElement.scrollHeight - window.innerHeight;
      const pct = docHeight > 0 ? Math.min(1, scrolled / docHeight) : 0;
      if (progress) progress.style.transform = 'scaleX(' + pct + ')';
      if (header) header.classList.toggle('scrolled', scrolled > 20);
      if (backBtn) backBtn.classList.toggle('visible', scrolled > 600);
    }}
    window.addEventListener('scroll', updateScroll, {{ passive: true }});
    updateScroll();

    if (backBtn) {{
      backBtn.addEventListener('click', () => {{
        window.scrollTo({{ top: 0, behavior: 'smooth' }});
      }});
    }}

    if (copyBtn) {{
      copyBtn.addEventListener('click', async () => {{
        const url = copyBtn.dataset.url || window.location.href;
        try {{
          await navigator.clipboard.writeText(url);
          const orig = copyBtn.textContent;
          copyBtn.textContent = '✓ Tersalin!';
          copyBtn.classList.add('copied');
          setTimeout(() => {{ copyBtn.textContent = orig; copyBtn.classList.remove('copied'); }}, 2000);
        }} catch (e) {{
          copyBtn.textContent = 'Gagal';
        }}
      }});
    }}
  }})();
  </script>
</body>
</html>
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", required=True, help="YYYY-MM-DD")
    ap.add_argument("--slug", required=True, help="url-safe slug, e.g. openai-rilis-gpt6")
    ap.add_argument("--title", required=True)
    ap.add_argument("--summary", required=True)
    ap.add_argument("--tags", nargs="*", default=[])
    ap.add_argument("--body-file", help="Path to markdown body file (use - for stdin)")
    ap.add_argument("--hero-image", help="Hero image filename in /assets/ (e.g. hero.jpg)")
    ap.add_argument("--hero-credit", help="Image credit text (e.g. 'Photo by X on Unsplash')")
    args = ap.parse_args()

    if args.body_file == "-":
        md = sys.stdin.read()
    elif args.body_file:
        md = Path(args.body_file).read_text(encoding="utf-8")
    else:
        md = sys.stdin.read()

    body_html = md_to_html(md)
    post_url = f"https://blog.ttmi.my.id/posts/{args.date}-{args.slug}.html"
    html = render_post(args.date, args.title, args.summary, args.tags, body_html, args.slug,
                       hero_image=args.hero_image, hero_credit=args.hero_credit, post_url=post_url)

    out = POSTS_DIR / f"{args.date}-{args.slug}.html"
    out.write_text(html, encoding="utf-8")
    print(f"✓ wrote {out.relative_to(ROOT)}")

    # Rebuild index
    import subprocess
    subprocess.run([sys.executable, str(ROOT / "build_index.py")], check=True)


if __name__ == "__main__":
    main()
