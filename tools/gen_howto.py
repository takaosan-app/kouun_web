"""使い方のページ（/howto/）を、kouun/docs/howto/ の原稿（Markdown）から作る。

使い方（www/ で実行）:
    python3 tools/gen_howto.py

必要なもの: Python の markdown と Pillow（sudo apt install python3-markdown python3-pil）
原稿が変わったら、これを実行して public/howto/ のHTMLと画像を作り直す。

- 目次（public/howto/index.html）と、PAGES の各ページ（public/howto/<名前>.html）を作る
- 原稿がまだないページは「準備中」と出す
- 原稿の中の <!-- --> の注記は、HTMLに出さない
- 原稿が使っている画像だけを、幅 SHOT_WIDTH の WebP に縮めて public/howto/images/ に置く。
  画像がまだないときは枠だけを出す
"""
import html
import re
from pathlib import Path

import markdown
from PIL import Image

WWW = Path(__file__).resolve().parent.parent
DOCS_HOWTO = WWW.parent / "docs" / "howto"
OUT = WWW / "public" / "howto"
OUT_IMAGES = OUT / "images"

# 名前（原稿のファイル名と掲載先）、ページの名前、目次に出す番号。並びは目次の順
PAGES = [
    ("setup", "初期設定", "01"),
    ("fields", "圃場の一覧", "02"),
    ("conditions", "足元の状況", "03"),
    ("diary", "栽培日誌", "04"),
    ("notices", "注意情報", "05"),
    ("account", "会員情報", "06"),
    ("scenes", "こんなときは", "?"),
]

# 原稿がまだないページの説明
PENDING_LEAD = {
    "notices": "病害虫に注意したい時期の知らせの見方です。この機能は準備中です。",
}

# 使い方のページを最後に更新した日と、合わせたアプリの版。原稿が変わって作り直したら直す
UPDATED = "2026-11-18"
UPDATED_VERSION = "1.0.0 (3)"

# スクリーンショットを縮めた後の幅。ページでは最大300pxで出すので、高精細の画面でもぼやけない2倍にする
SHOT_WIDTH = 600
# WebP の画質（0〜100）
SHOT_QUALITY = 80

HEAD = """<!doctype html>
<html lang="ja">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="robots" content="noindex">
  <meta name="description" content="{description}">
  <title>{title}｜耕雲</title>
  <link rel="icon" type="image/png" href="/assets/icons/icon_origin.png">
  <link rel="stylesheet" href="/css/style.css">
</head>
<body>
  <p class="notice">耕雲は現在テスト版です。アプリの正式公開に向けて準備しています。</p>
  <header class="site-header">
    <a class="brand" href="/" aria-label="耕雲 トップ">
      <img src="/assets/icons/icon_origin.png" alt="" width="42" height="42">
      <span>耕雲<small>こううん</small></span>
    </a>
    <nav aria-label="メインナビゲーション">
      <a href="/#about">耕雲について</a>
      <a href="/howto/">使い方</a>
      <a href="/news/">お知らせ</a>
    </nav>
  </header>

"""

FOOT = """
  <footer class="site-footer">
    <a class="footer-brand" href="/">耕雲 <span>こううん</span></a>
    <p>天候データで農業を支援する。</p>
    <div class="footer-links">
      <a href="/legal/terms">利用規約</a>
      <a href="/legal/privacy">個人情報の取扱い</a>
      <a href="https://takaosan.app" target="_blank" rel="noopener noreferrer">開発者サイト ↗</a>
    </div>
    <small>© takaosan.app</small>
  </footer>
</body>
</html>
"""


def date_label(date):
    """「2026-11-18」を「2026年11月18日」にする。"""
    year, month, day = date.split("-")
    return f"{int(year)}年{int(month)}月{int(day)}日"


def indent(text, spaces):
    return "\n".join(" " * spaces + line if line else line for line in text.splitlines())


def split_title_lead(md_text):
    """原稿の最初の「# ページの名前」と、その下の一言の説明を取り出し、残りの本文と分ける。"""
    lines = md_text.strip().splitlines()
    title = lines[0].lstrip("# ").strip()
    rest = "\n".join(lines[1:]).strip()
    lead, _, body = rest.partition("\n\n")
    return title, lead.strip(), body


def to_body(md_text, used_images):
    """原稿の本文をHTMLにする。"""
    # 注記は出さない
    md_text = re.sub(r"<!--.*?-->", "", md_text, flags=re.S)
    # ほかのページへのリンク（setup.md など）を、掲載先の住所にする
    md_text = re.sub(r"\]\(([a-z_]+)\.md\)", r"](/howto/\1)", md_text)

    body = markdown.markdown(md_text, extensions=["tables"])

    # 見出しに番号の id を付け、ページの中の目次を作る
    sections = []

    def add_id(m):
        sections.append(m.group(1))
        return f'<h2 id="s{len(sections)}">{m.group(1)}</h2>'

    body = re.sub(r"<h2>(.*?)</h2>", add_id, body)

    # スクリーンショットを、枠付きの図にする
    def to_figure(m):
        src, alt = m.group("src"), m.group("alt")
        name = src.split("/")[-1]
        if (DOCS_HOWTO / "images" / name).exists():
            out_name, width, height = shrink_image(name)
            used_images.add(out_name)
            return (f'<figure class="shot"><img src="/howto/images/{out_name}" alt="{alt}" '
                    f'width="{width}" height="{height}" loading="lazy"></figure>')
        return f'<figure class="shot shot-missing" role="img" aria-label="{alt}"><span>画像を準備中です</span></figure>'

    body = re.sub(r'<p><img alt="(?P<alt>[^"]*)" src="(?P<src>[^"]*)" ?/?></p>', to_figure, body)

    body = body.replace("<table>", '<div class="table-wrap">\n<table>')
    body = body.replace("</table>", "</table>\n</div>")
    return body, sections


def page_nav(index):
    """前後のページへのリンク。"""
    parts = []
    if index > 0:
        name, title, _ = PAGES[index - 1]
        parts.append(f'<a class="prev" href="/howto/{name}"><small>前へ</small>{title}</a>')
    else:
        parts.append("<span></span>")
    if index < len(PAGES) - 1:
        name, title, _ = PAGES[index + 1]
        parts.append(f'<a class="next" href="/howto/{name}"><small>次へ</small>{title}</a>')
    return '<nav class="page-nav" aria-label="前後のページ">\n  ' + "\n  ".join(parts) + "\n</nav>"


def build_page(index, used_images):
    name, title, _ = PAGES[index]
    src = DOCS_HOWTO / f"{name}.md"
    if src.exists():
        title, lead, md_body = split_title_lead(src.read_text(encoding="utf-8"))
        body, sections = to_body(md_body, used_images)
        pending = False
    else:
        lead = PENDING_LEAD.get(name, "このページは準備中です。")
        body, sections = '<p class="pending">このページは準備中です。できあがりしだい、ここでご案内します。</p>', []
        pending = True

    toc = ""
    if len(sections) > 1:
        items = "\n".join(f'  <li><a href="#s{i}">{s}</a></li>' for i, s in enumerate(sections, 1))
        toc = f'<nav class="on-this-page" aria-label="このページの内容">\n<p>このページの内容</p>\n<ol>\n{items}\n</ol>\n</nav>\n'

    main = f"""<main class="howto-page">
  <p class="breadcrumb"><a href="/howto/">使い方</a></p>
  <h1>{title}</h1>
  <p class="lead">{lead}</p>
{indent(toc, 2)}
  <article>
{indent(body, 4)}
  </article>
{indent(page_nav(index), 2)}
</main>
"""
    out = HEAD.format(title=f"{title}｜使い方", description=html.escape(lead)) + indent(main, 2) + "\n" + FOOT
    (OUT / f"{name}.html").write_text(out, encoding="utf-8")
    return title, lead, pending


def build_index(entries):
    items = []
    for (name, _, number), (title, lead, pending) in zip(PAGES, entries):
        badge = '<em class="badge">準備中</em>' if pending else ""
        items.append(f"""<li>
  <a href="/howto/{name}">
    <span class="number">{number}</span>
    <span class="text"><b>{title}{badge}</b><small>{lead}</small></span>
  </a>
</li>""")
    main = f"""<main class="howto-page">
  <p class="eyebrow">GUIDE</p>
  <h1>使い方</h1>
  <p class="history-date">更新日：<time datetime="{UPDATED}">{date_label(UPDATED)}</time>（アプリの版 {UPDATED_VERSION} に合わせています）</p>
  <p class="lead">耕雲のアプリの使い方をご案内します。はじめての方は「初期設定」からお読みください。</p>
  <ul class="howto-list">
{indent(chr(10).join(items), 4)}
  </ul>
  <p class="howto-more">アプリを更新したときに変わったところは、<a href="/history/">更新履歴</a>をご覧ください。</p>
  <a class="back-link" href="/">← トップページへ戻る</a>
</main>
"""
    out = HEAD.format(title="使い方", description="耕雲のアプリの使い方をご案内します。") + indent(main, 2) + "\n" + FOOT
    (OUT / "index.html").write_text(out, encoding="utf-8")


def shrink_image(name):
    """原稿の画像を幅 SHOT_WIDTH の WebP に縮めて置き、置いた名前と大きさを返す。
    置いたものが原稿の画像より新しければ、縮め直さない。"""
    src = DOCS_HOWTO / "images" / name
    out = OUT_IMAGES / (Path(name).stem + ".webp")
    if out.exists() and out.stat().st_mtime >= src.stat().st_mtime:
        with Image.open(out) as img:
            return out.name, img.width, img.height
    OUT_IMAGES.mkdir(parents=True, exist_ok=True)
    with Image.open(src) as img:
        height = round(img.height * SHOT_WIDTH / img.width)
        small = img.convert("RGB").resize((SHOT_WIDTH, height), Image.LANCZOS)
        small.save(out, "WEBP", quality=SHOT_QUALITY, method=6)
    return out.name, SHOT_WIDTH, height


def remove_old_images(used_images):
    """使わなくなった画像を消す。"""
    for old in OUT_IMAGES.glob("*"):
        if old.name not in used_images:
            old.unlink()


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    used_images = set()
    entries = [build_page(i, used_images) for i in range(len(PAGES))]
    build_index(entries)
    remove_old_images(used_images)
    for (name, _, _), (_, _, pending) in zip(PAGES, entries):
        print(f"howto/{name}.html" + ("（準備中）" if pending else ""))
    print(f"画像 {len(used_images)} 枚")


if __name__ == "__main__":
    main()
