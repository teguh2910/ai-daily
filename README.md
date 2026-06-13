# AI Daily 🤖

> Ringkasan harian perkembangan AI dalam Bahasa Indonesia — di-post otomatis tiap pagi.

**Live:** https://blog.ttmi.my.id · **RSS:** https://blog.ttmi.my.id/feed.xml

## Apa Ini?

AI Daily adalah blog otomatis yang setiap hari **08:00 WIB** mempublikasikan 1 artikel tentang perkembangan AI terupdate (rilis model, riset, tools, dampak industri) dalam Bahasa Indonesia. Tulisan dan hero image di-generate otomatis oleh AI agent (Hermes).

## Stack

- **Static site** — HTML + CSS murni, no database, no JS framework
- **Python helpers** — `new_post.py` (md → html), `build_index.py` (regenerate index + RSS)
- **nginx** + **Let's Encrypt** untuk serving + HTTPS
- **Cron LLM agent** (Hermes) untuk auto-posting harian

## Struktur

```
.
├── index.html              # auto-generated landing page
├── feed.xml                # auto-generated RSS 2.0
├── build_index.py          # regenerate index.html + feed.xml dari posts/
├── new_post.py             # wrap markdown → post HTML
├── posts/
│   └── YYYY-MM-DD-slug.html
└── assets/
    ├── style.css
    └── hero-*.jpg
```

## Cara Pakai (Local)

### Tambah artikel baru

```bash
# 1. Tulis body markdown
cat > /tmp/post.md <<'EOF'
## Judul Artikel
...
EOF

# 2. Publish
python3 new_post.py \
  --date 2026-06-15 \
  --slug openai-rilis-gpt-6 \
  --title "OpenAI Rilis GPT-6, 2x Lebih Cepat" \
  --summary "OpenAI luncurkan GPT-6 dengan ..." \
  --tags "OpenAI" "GPT" "LLM" \
  --hero-image hero-gpt-6.jpg \
  --hero-credit "Gambar oleh X dari Unsplash" \
  --body-file /tmp/post.md
```

### Rebuild index saja

```bash
python3 build_index.py
```

## Cara Deploy

Blog ini didesain untuk self-host di VPS. Langkahnya:

1. **Clone repo** ke `/var/www/<subdomain>.<domain>/`
2. **Buat nginx vhost** yang serve folder itu
3. **Pasang SSL** via `certbot --nginx -d <subdomain>`
4. **Set cron** (via Hermes atau system crontab) yang trigger LLM agent untuk riset + tulis + post tiap pagi

Detail lengkap: lihat [DEPLOY.md](DEPLOY.md) (TODO: tulis dokumentasi deployment).

## Format Post

Setiap file HTML di `posts/` dimulai dengan `<post-meta>` JSON block:

```html
<post-meta>
{
  "date": "2026-06-14",
  "title": "...",
  "summary": "...",
  "tags": ["Tag1", "Tag2"],
  "slug": "url-slug",
  "hero_image": "hero.jpg",
  "hero_credit": "Photo by X on Unsplash"
}
</post-meta>
<!-- HTML body follows -->
```

`build_index.py` parse block ini untuk generate landing page + RSS.

## Konfigurasi

URL canonical di-hardcode di:
- `build_index.py` → `https://blog.ttmi.my.id` (untuk RSS)
- `new_post.py` → `https://blog.ttmi.my.id/posts/...` (untuk share button)

Kalau deploy di domain lain, edit kedua file.

## Lisensi

MIT © 2026 Teguh Yuhono

---

Dibuat dengan ♥ oleh [Hermes Agent](https://hermes.ttmi.my.id)
